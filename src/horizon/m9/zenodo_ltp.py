"""Zenodo last-trade Nifty 1m → remaining-session snapshot rows.

Bhat 2024, https://doi.org/10.5281/zenodo.10899828 (CC0). Report-only:
bid = ask = last-trade close. Do not write the S4-P1 quote store.
"""

from __future__ import annotations

import datetime as dt
import io
import re
import zipfile
from pathlib import Path

import polars as pl

from src.horizon.m9.index_option_store import (
    ENTRY_CLOCK,
    EXIT_CLOCK,
    REQUIRED_COLS,
    UNDERLYING,
)
from src.utils.symbol_data import load_symbol_data

SOURCE_ID = "zenodo_bhat_1m_ltp"
DEFAULT_ZENODO_ZIP = Path("data/GOLDEN_IV/zenodo/Nifty Options Data.zip")
DEFAULT_ZENODO_SNAPSHOT_PATH = Path("data/GOLDEN_IV/nifty_option_snapshots_zenodo.parquet")
DTE_MIN = 1
DTE_PREFERRED_MAX = 10

_CLOCKS = (ENTRY_CLOCK, EXIT_CLOCK)
_MONTH_NUM = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
_RANGE = re.compile(r"(\d{2}-\d{2}-\d{2})\s+to\s+(\d{2}-\d{2}-\d{2})", re.IGNORECASE)
_MONTH_YEAR = re.compile(
    r"(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{4})",
    re.IGNORECASE,
)
_CONTRACT_NIFTY = re.compile(r"^NIFTY\s*(\d+)\s*(CE|PE)$", re.IGNORECASE)
_CONTRACT_OPT = re.compile(r"^(CE|PE)\s*(\d+)$", re.IGNORECASE)


def last_thursday(year: int, month: int) -> dt.date:
    """Last Thursday of a calendar month (NSE monthly Nifty expiry, no holiday shift)."""
    if month == 12:
        day = dt.date(year + 1, 1, 1) - dt.timedelta(days=1)
    else:
        day = dt.date(year, month + 1, 1) - dt.timedelta(days=1)
    while day.weekday() != 3:
        day -= dt.timedelta(days=1)
    return day


def parse_contract_name(name: str) -> tuple[str, float]:
    """Return ``(CE|PE, strike)`` from a Zenodo strike filename or first-column token."""
    stem = Path(name).stem.strip().upper().replace("_", " ")
    match = _CONTRACT_NIFTY.fullmatch(stem)
    if match:
        return match.group(2).upper(), float(match.group(1))
    match = _CONTRACT_OPT.fullmatch(stem)
    if match:
        return match.group(1).upper(), float(match.group(2))
    raise ValueError(f"unrecognised contract name {name!r}")


def parse_expiry_label(*labels: str) -> dt.date:
    """Expiry from a date-range archive name, else last Thursday of ``Month YYYY``."""
    for label in labels:
        match = _RANGE.search(label.replace("\\", "/"))
        if match:
            day_s, month_s, year_s = match.group(2).split("-")
            return dt.date(2000 + int(year_s), int(month_s), int(day_s))
    for label in labels:
        match = _MONTH_YEAR.search(label.replace("\\", "/"))
        if match:
            return last_thursday(int(match.group(2)), _MONTH_NUM[match.group(1).lower()])
    raise ValueError(f"cannot parse expiry from {labels!r}")


def is_zenodo_last_trade(snapshots: pl.DataFrame) -> bool:
    """True when the store is the report-only last-trade companion, not quote V2."""
    if "source" not in snapshots.columns or snapshots.is_empty():
        return False
    sources = snapshots["source"].unique().to_list()
    return sources == [SOURCE_ID]


def load_golden_clock_spots(
    csv_path: Path,
    *,
    start_period: str = "2018",
    end_period: str = "2019",
) -> pl.DataFrame:
    """GOLDEN ``^NSEI`` close at 09:45 and 15:15."""
    raw = load_symbol_data(
        csv_path, start_period=start_period, end_period=end_period
    )
    return (
        raw.with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
        )
        .filter(pl.col("time_only").is_in(list(_CLOCKS)))
        .select("date_only", "time_only", pl.col("close").alias("spot"))
        .unique(["date_only", "time_only"])
        .sort(["date_only", "time_only"])
    )


def _strike_archive(
    month_zip: zipfile.ZipFile,
) -> tuple[zipfile.ZipFile, str]:
    files = [n for n in month_zip.namelist() if not n.endswith("/")]
    csv_zips = [n for n in files if n.lower().endswith(".zip") and "csv" in n.lower()]
    txt_zips = [n for n in files if n.lower().endswith(".zip") and "txt" in n.lower()]
    other_zips = [n for n in files if n.lower().endswith(".zip")]
    chosen = csv_zips[0] if csv_zips else txt_zips[0] if txt_zips else (
        other_zips[0] if other_zips else ""
    )
    if not chosen:
        return month_zip, ""
    return zipfile.ZipFile(io.BytesIO(month_zip.read(chosen))), chosen


_CLOCK_LABELS = ("09:45", "9:45", "09:45:00", "15:15", "15:15:00")


def _parse_clock_file(
    payload: bytes,
    expiry: dt.date,
    opt_type: str,
    strike: float,
) -> pl.DataFrame:
    df = pl.read_csv(
        io.BytesIO(payload),
        has_header=False,
        new_columns=[
            "contract",
            "trade_date",
            "trade_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ],
        schema_overrides={
            "contract": pl.Utf8,
            "trade_date": pl.Utf8,
            "trade_time": pl.Utf8,
            "close": pl.Float64,
        },
        truncate_ragged_lines=True,
        ignore_errors=True,
    )
    if df.is_empty():
        return df
    clocked = df.filter(pl.col("trade_time").str.strip_chars().is_in(_CLOCK_LABELS))
    if clocked.is_empty():
        return clocked
    parsed = clocked.with_columns(
        date_only=pl.col("trade_date").str.to_date("%Y/%m/%d", strict=False),
        time_only=pl.when(
            pl.col("trade_time").str.strip_chars().str.contains("09:45")
            | pl.col("trade_time").str.strip_chars().str.contains("9:45")
        )
        .then(pl.lit(ENTRY_CLOCK))
        .when(pl.col("trade_time").str.strip_chars().str.contains("15:15"))
        .then(pl.lit(EXIT_CLOCK))
        .otherwise(pl.lit(None).cast(pl.Time)),
    )
    return (
        parsed.filter(
            pl.col("date_only").is_not_null()
            & pl.col("time_only").is_not_null()
            & pl.col("close").is_finite()
        )
        .select(
            "date_only",
            "time_only",
            pl.lit(expiry).alias("expiry"),
            pl.lit(strike).alias("strike"),
            pl.lit(opt_type).alias("opt_type"),
            "close",
        )
    )


def clip_expiry_to_last_trade(ticks: pl.DataFrame) -> pl.DataFrame:
    """If the folder's last Thursday is a holiday, use the last traded date."""
    last = ticks.group_by("expiry").agg(last_trade=pl.col("date_only").max())
    return (
        ticks.join(last, on="expiry")
        .with_columns(
            expiry=pl.when(pl.col("last_trade") < pl.col("expiry"))
            .then(pl.col("last_trade"))
            .otherwise(pl.col("expiry"))
        )
        .drop("last_trade")
    )


def load_zenodo_clock_ticks(
    zip_path: Path,
    *,
    years: tuple[int, ...] = (2018, 2019),
) -> pl.DataFrame:
    """09:45 and 15:15 last-trades from the nested yearly/monthly Zenodo zips."""
    chunks: list[pl.DataFrame] = []
    with zipfile.ZipFile(zip_path) as outer:
        for year in years:
            year_name = f"Nifty Options Data/NiftyOptions {year}.zip"
            with zipfile.ZipFile(io.BytesIO(outer.read(year_name))) as year_zip:
                for month_name in sorted(year_zip.namelist()):
                    if not month_name.lower().endswith(".zip"):
                        continue
                    with zipfile.ZipFile(io.BytesIO(year_zip.read(month_name))) as month_zip:
                        strike_zip, nested_name = _strike_archive(month_zip)
                        expiry = parse_expiry_label(nested_name, month_name)
                        n_before = len(chunks)
                        try:
                            for member in strike_zip.namelist():
                                if member.endswith("/") or member.lower().endswith(".zip"):
                                    continue
                                leaf = member.rsplit("/", 1)[-1]
                                if not leaf.lower().endswith((".csv", ".txt")):
                                    continue
                                try:
                                    opt_type, strike = parse_contract_name(leaf)
                                except ValueError:
                                    continue
                                part = _parse_clock_file(
                                    strike_zip.read(member), expiry, opt_type, strike
                                )
                                if not part.is_empty():
                                    chunks.append(part)
                        finally:
                            if strike_zip is not month_zip:
                                strike_zip.close()
                        print(
                            f"   {month_name} expiry={expiry.isoformat()} "
                            f"files={len(chunks) - n_before}"
                        )
    if not chunks:
        return pl.DataFrame(
            schema={
                "date_only": pl.Date,
                "time_only": pl.Time,
                "expiry": pl.Date,
                "strike": pl.Float64,
                "opt_type": pl.Utf8,
                "close": pl.Float64,
            }
        )
    start = dt.date(min(years), 1, 1)
    end = dt.date(max(years), 12, 31)
    return (
        pl.concat(chunks)
        .filter((pl.col("date_only") >= start) & (pl.col("date_only") <= end))
        .pipe(clip_expiry_to_last_trade)
        .unique(["date_only", "time_only", "expiry", "strike", "opt_type"])
        .sort(["date_only", "time_only", "expiry", "strike", "opt_type"])
    )


def build_zenodo_snapshots(
    ticks: pl.DataFrame,
    spots: pl.DataFrame,
) -> pl.DataFrame:
    """ATM last-trade snapshots: prefer DTE ∈ [1, 10], else nearest DTE ≥ 1."""
    spot_entry = spots.filter(pl.col("time_only") == ENTRY_CLOCK).select(
        "date_only", pl.col("spot").alias("spot_entry")
    )
    spot_exit = spots.filter(pl.col("time_only") == EXIT_CLOCK).select(
        "date_only", pl.col("spot").alias("spot_exit")
    )
    entry = ticks.filter(pl.col("time_only") == ENTRY_CLOCK)
    ce = entry.filter(pl.col("opt_type") == "CE").select(
        "date_only",
        "expiry",
        "strike",
        pl.col("close").alias("ce_close"),
    )
    pe = entry.filter(pl.col("opt_type") == "PE").select(
        "date_only",
        "expiry",
        "strike",
        pl.col("close").alias("pe_close"),
    )
    both = (
        ce.join(pe, on=["date_only", "expiry", "strike"], how="inner")
        .join(spot_entry, on="date_only", how="inner")
        .with_columns(
            dte=(pl.col("expiry") - pl.col("date_only")).dt.total_days(),
            dist=(pl.col("strike") - pl.col("spot_entry")).abs(),
        )
        .filter(pl.col("dte") >= DTE_MIN)
    )
    has_band = both.group_by("date_only").agg(
        has_preferred=(pl.col("dte") <= DTE_PREFERRED_MAX).any()
    )
    candidates = both.join(has_band, on="date_only").filter(
        (pl.col("dte") <= DTE_PREFERRED_MAX) | (~pl.col("has_preferred"))
    )
    held = (
        candidates.sort(["date_only", "dte", "dist", "strike"])
        .group_by("date_only", maintain_order=True)
        .first()
        .select(
            "date_only",
            "expiry",
            "strike",
            "spot_entry",
            "ce_close",
            "pe_close",
            "dte",
        )
    )
    exit_ticks = ticks.filter(pl.col("time_only") == EXIT_CLOCK)
    exit_ce = exit_ticks.filter(pl.col("opt_type") == "CE").select(
        "date_only",
        "expiry",
        "strike",
        pl.col("close").alias("ce_exit"),
    )
    exit_pe = exit_ticks.filter(pl.col("opt_type") == "PE").select(
        "date_only",
        "expiry",
        "strike",
        pl.col("close").alias("pe_exit"),
    )
    paired = (
        held.join(exit_ce, on=["date_only", "expiry", "strike"], how="inner")
        .join(exit_pe, on=["date_only", "expiry", "strike"], how="inner")
        .join(spot_exit, on="date_only", how="left")
        .with_columns(
            spot_exit=pl.coalesce(pl.col("spot_exit"), pl.col("spot_entry")),
        )
    )
    entry_rows = paired.select(
        pl.lit(UNDERLYING).alias("underlying"),
        "date_only",
        pl.lit(ENTRY_CLOCK).alias("time_only"),
        pl.col("spot_entry").alias("spot"),
        "expiry",
        "strike",
        pl.col("ce_close").alias("ce_bid"),
        pl.col("ce_close").alias("ce_ask"),
        pl.col("pe_close").alias("pe_bid"),
        pl.col("pe_close").alias("pe_ask"),
        pl.lit(SOURCE_ID).alias("source"),
    )
    exit_rows = paired.select(
        pl.lit(UNDERLYING).alias("underlying"),
        "date_only",
        pl.lit(EXIT_CLOCK).alias("time_only"),
        pl.col("spot_exit").alias("spot"),
        "expiry",
        "strike",
        pl.col("ce_exit").alias("ce_bid"),
        pl.col("ce_exit").alias("ce_ask"),
        pl.col("pe_exit").alias("pe_bid"),
        pl.col("pe_exit").alias("pe_ask"),
        pl.lit(SOURCE_ID).alias("source"),
    )
    return pl.concat([entry_rows, exit_rows]).select(list(REQUIRED_COLS)).sort(
        ["date_only", "time_only"]
    )
