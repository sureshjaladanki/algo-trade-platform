"""Index membership as-of a date, plus Indian surveillance flags. ESM Stage II is not tradable."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl

NIFTY_50 = "nifty_50"
NIFTY_NEXT_50 = "nifty_next_50"
NIFTY_100 = "nifty_100"
NIFTY_200 = "nifty_200"
NIFTY_MIDCAP_150 = "nifty_midcap_150"
NIFTY_SMALLCAP_250 = "nifty_smallcap_250"

NARROW_UNIVERSE = (NIFTY_50, NIFTY_NEXT_50)


def load_membership_events(path: Path) -> pl.DataFrame:
    return pl.read_csv(path, try_parse_dates=True)


def load_snapshot(path: Path, index_name: str, as_of: date) -> pl.DataFrame:
    raw = pl.read_csv(path)
    cols = {c.lower().replace(" ", "_"): c for c in raw.columns}
    symbol = cols["symbol"]
    isin = cols.get("isin_code") or cols.get("isin")
    return raw.select(
        pl.lit(as_of).alias("effective_date"),
        pl.lit(index_name).alias("index"),
        pl.col(symbol).cast(pl.Utf8).alias("symbol"),
        pl.col(isin).cast(pl.Utf8).alias("isin") if isin else pl.lit("").alias("isin"),
        pl.lit("in").alias("action"),
    )


def membership_as_of(
    events: pl.DataFrame,
    index_name: str,
    as_of: date,
    *,
    seed: pl.DataFrame | None = None,
) -> frozenset[str]:
    """Walk seed membership through events with effective_date <= as_of."""
    names: set[str] = set()
    seed_date: date | None = None
    if seed is not None and not seed.is_empty():
        seed_date = seed.get_column("effective_date").min()
        names = set(seed.get_column("symbol").to_list())
        if seed_date is not None and as_of < seed_date:
            later = events.filter(
                (pl.col("index") == index_name)
                & (pl.col("effective_date") > as_of)
                & (pl.col("effective_date") <= seed_date)
            ).sort("effective_date", descending=True)
            for rec in later.iter_rows(named=True):
                if rec["action"] == "in":
                    names.discard(rec["symbol"])
                elif rec["action"] == "out":
                    names.add(rec["symbol"])
            return frozenset(names)
    hist = events.filter((pl.col("index") == index_name) & (pl.col("effective_date") <= as_of)).sort(
        "effective_date"
    )
    if seed is None:
        names = set()
        for rec in hist.iter_rows(named=True):
            if rec["action"] == "in":
                names.add(rec["symbol"])
            elif rec["action"] == "out":
                names.discard(rec["symbol"])
    return frozenset(names)


def load_flag_intervals(path: Path) -> pl.DataFrame:
    if not path.exists():
        return pl.DataFrame(
            schema={
                "symbol": pl.Utf8,
                "start": pl.Date,
                "end": pl.Date,
                "esm_stage": pl.Int64,
                "gsm_stage": pl.Int64,
                "price_band_pct": pl.Float64,
                "in_fno_ban": pl.Boolean,
                "fno_eligible": pl.Boolean,
            }
        )
    return pl.read_csv(path, try_parse_dates=True)


def flags_as_of(intervals: pl.DataFrame, symbol: str, as_of: date) -> dict:
    hit = intervals.filter(
        (pl.col("symbol") == symbol) & (pl.col("start") <= as_of) & (pl.col("end") >= as_of)
    )
    if hit.is_empty():
        return {
            "fno_eligible": False,
            "cas_eligible": False,
            "esm_stage": 0,
            "gsm_stage": 0,
            "price_band_pct": 20.0,
            "in_fno_ban": False,
        }
    row = hit.row(0, named=True)
    esm = int(row.get("esm_stage") or 0)
    fno = bool(row.get("fno_eligible") or False)
    cas = fno and as_of >= date(2026, 8, 3)
    return {
        "fno_eligible": fno,
        "cas_eligible": cas,
        "esm_stage": esm,
        "gsm_stage": int(row.get("gsm_stage") or 0),
        "price_band_pct": float(row.get("price_band_pct") or 20.0),
        "in_fno_ban": bool(row.get("in_fno_ban") or False),
    }


def tradable_symbols(
    symbols: set[str],
    intervals: pl.DataFrame,
    as_of: date,
    *,
    sleeve: str = "cash",
) -> frozenset[str]:
    """Cash tradable set: refuse ESM Stage II. F&O sleeve also refuses the ban list."""
    kept = set()
    for symbol in symbols:
        flags = flags_as_of(intervals, symbol, as_of)
        if flags["esm_stage"] >= 2:
            continue
        if sleeve == "fno" and flags["in_fno_ban"]:
            continue
        kept.add(symbol)
    return frozenset(kept)
