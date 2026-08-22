"""OptionsDX SPX EOD chains.

Cboe DataShop historical cart exceeded the $100 stop, so this dump is the A1
tape: SPX only, 2012–2023, bid/ask used; vendor greeks are ignored.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl

from src.theta import OptionQuote

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw" / "optionsdx" / "SPX"
UNPACKED_NAME = "unpacked"
DERIVED_DIR = REPO_ROOT / "data" / "derived"
PUT_PANEL_CACHE = DERIVED_DIR / "optionsdx_spx_puts_dte47.parquet"
KEEP_DTE_MAX = 47.0
MONEYNESS_LOW = 0.70
MONEYNESS_HIGH = 1.05
SLIM_COLUMNS = (
    "quote_date",
    "expire_date",
    "dte",
    "strike",
    "p_bid",
    "p_ask",
    "p_delta",
    "underlying_last",
)

FLOAT_COLUMNS = (
    "quote_time_hours",
    "underlying_last",
    "dte",
    "c_delta",
    "c_gamma",
    "c_vega",
    "c_theta",
    "c_rho",
    "c_iv",
    "c_volume",
    "c_last",
    "c_bid",
    "c_ask",
    "strike",
    "p_bid",
    "p_ask",
    "p_last",
    "p_delta",
    "p_gamma",
    "p_vega",
    "p_theta",
    "p_rho",
    "p_iv",
    "p_volume",
    "strike_distance",
    "strike_distance_pct",
)


class OptionsDxDumpMissing(Exception):
    """No OptionsDX archive or unpacked monthly files under data/raw/optionsdx/SPX."""


def _column_name(name: str) -> str:
    return name.strip().strip("[]").strip().lower()


def extract_archives(directory: Path = RAW_DIR) -> Path:
    import py7zr

    unpacked = directory / UNPACKED_NAME
    unpacked.mkdir(parents=True, exist_ok=True)
    archives = sorted(directory.glob("*.7z"))
    if not archives and not list(unpacked.glob("*.txt")):
        raise OptionsDxDumpMissing(f"no OptionsDX 7z or txt files in {directory}")
    for archive in archives:
        with py7zr.SevenZipFile(archive, mode="r") as zipfile:
            names = [Path(name).name for name in zipfile.getnames() if name.endswith(".txt")]
            if names and all((unpacked / name).exists() for name in names):
                continue
            zipfile.extractall(path=unpacked)
    return unpacked


def read_month_file(path: Path) -> pl.DataFrame:
    raw = pl.read_csv(path)
    frame = raw.rename({column: _column_name(column) for column in raw.columns})
    frame = frame.with_columns(pl.col(pl.String).str.strip_chars())
    casts = [
        pl.col(name).cast(pl.Float64, strict=False)
        for name in FLOAT_COLUMNS
        if name in frame.columns
    ]
    casts.extend(
        [
            pl.col("quote_date").str.to_date(),
            pl.col("expire_date").str.to_date(),
        ]
    )
    return frame.with_columns(casts)


def month_paths(directory: Path | None = None) -> list[Path]:
    unpacked = extract_archives() if directory is None else directory
    paths = sorted(unpacked.glob("*.txt"))
    if not paths:
        raise OptionsDxDumpMissing(f"no monthly txt files in {unpacked}")
    return paths


def iter_month_frames(directory: Path | None = None) -> list[pl.DataFrame]:
    return [read_month_file(path) for path in month_paths(directory)]


def load_chain(directory: Path | None = None) -> pl.DataFrame:
    frames = iter_month_frames(directory)
    return pl.concat(frames, how="vertical")


def _slim_puts(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.filter(
        (pl.col("p_bid") > 0)
        & (pl.col("p_ask") >= pl.col("p_bid"))
        & (pl.col("dte") >= 0)
        & (pl.col("dte") <= KEEP_DTE_MAX)
        & (pl.col("underlying_last") > 0)
        & (
            (pl.col("strike") / pl.col("underlying_last")).is_between(
                MONEYNESS_LOW, MONEYNESS_HIGH
            )
        )
    ).select([name for name in SLIM_COLUMNS if name in frame.columns])


def load_put_panel(
    directory: Path | None = None,
    *,
    cache: Path | None = PUT_PANEL_CACHE,
) -> pl.DataFrame:
    """Puts with DTE ≤ 47 and strike in a 20–25Δ moneyness band. Cached parquet."""
    paths = month_paths(directory)
    if cache is not None and directory is None and cache.exists():
        return pl.read_parquet(cache)
    frames = []
    for i, path in enumerate(paths, start=1):
        frames.append(_slim_puts(read_month_file(path)))
        if i % 12 == 0 or i == len(paths):
            print(f"OptionsDX months {i}/{len(paths)}", flush=True)
    panel = pl.concat(frames, how="vertical").unique(
        ["quote_date", "expire_date", "strike"], keep="last"
    )
    if cache is not None and directory is None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        panel.write_parquet(cache)
    return panel


def puts_from_panel(
    panel: pl.DataFrame,
    *,
    expiry: date,
    trade_date: date,
    delta_lo: float | None = None,
    delta_hi: float | None = None,
) -> list[OptionQuote]:
    day = panel.filter(
        (pl.col("quote_date") == trade_date) & (pl.col("expire_date") == expiry)
    )
    if (
        delta_lo is not None
        and delta_hi is not None
        and "p_delta" in day.columns
    ):
        day = day.filter(
            pl.col("p_delta").abs().is_between(max(delta_lo - 0.05, 0.0), delta_hi + 0.05)
        )
    return [
        OptionQuote(
            expiry=row["expire_date"],
            trade_date=row["quote_date"],
            strike=row["strike"],
            right="P",
            bid=row["p_bid"],
            ask=row["p_ask"],
        )
        for row in day.iter_rows(named=True)
        if row["p_bid"] is not None and row["p_ask"] is not None
    ]


def legs_on_date(
    panel: pl.DataFrame,
    *,
    expiry: date,
    trade_date: date,
    short_strike: float,
    long_strike: float,
) -> tuple[OptionQuote, OptionQuote] | None:
    quotes = {
        quote.strike: quote
        for quote in puts_from_panel(panel, expiry=expiry, trade_date=trade_date)
    }
    short = quotes.get(short_strike)
    long = quotes.get(long_strike)
    if short is None or long is None:
        return None
    return short, long


def quotes_from_frame(frame: pl.DataFrame) -> list[OptionQuote]:
    quotes: list[OptionQuote] = []
    for row in frame.iter_rows(named=True):
        trade_date = row["quote_date"]
        expiry = row["expire_date"]
        strike = row["strike"]
        put_bid = row["p_bid"]
        put_ask = row["p_ask"]
        if put_bid is not None and put_ask is not None and put_bid > 0 and put_ask >= put_bid:
            quotes.append(
                OptionQuote(
                    expiry=expiry,
                    trade_date=trade_date,
                    strike=strike,
                    right="P",
                    bid=put_bid,
                    ask=put_ask,
                    close=float(row["p_last"] or 0.0),
                )
            )
        call_bid = row["c_bid"]
        call_ask = row["c_ask"]
        if (
            call_bid is not None
            and call_ask is not None
            and call_bid > 0
            and call_ask >= call_bid
        ):
            quotes.append(
                OptionQuote(
                    expiry=expiry,
                    trade_date=trade_date,
                    strike=strike,
                    right="C",
                    bid=call_bid,
                    ask=call_ask,
                    close=float(row["c_last"] or 0.0),
                )
            )
    return quotes


def puts_on_date(
    frame: pl.DataFrame, *, expiry: date, trade_date: date
) -> list[OptionQuote]:
    day = frame.filter(
        (pl.col("quote_date") == trade_date) & (pl.col("expire_date") == expiry)
    )
    return [quote for quote in quotes_from_frame(day) if quote.right == "P"]


def summarize_chain(frame: pl.DataFrame) -> dict[str, object]:
    puts = frame.filter((pl.col("p_bid") > 0) & (pl.col("p_ask") >= pl.col("p_bid")))
    tenor = puts.filter((pl.col("dte") >= 30) & (pl.col("dte") <= 45))
    delta_bucket = tenor.filter(pl.col("p_delta").abs().is_between(0.20, 0.25))
    return {
        "n_rows": frame.height,
        "quote_dates": int(frame["quote_date"].n_unique()),
        "expiries": int(frame["expire_date"].n_unique()),
        "first_quote": frame["quote_date"].min(),
        "last_quote": frame["quote_date"].max(),
        "valid_puts": puts.height,
        "puts_30_45_dte": tenor.height,
        "puts_20_25_delta": delta_bucket.height,
    }


def main() -> None:
    unpacked = extract_archives()
    frame = load_chain(unpacked)
    summary = summarize_chain(frame)
    print("OptionsDX SPX EOD (A1 tape; vendor greeks unused)")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
