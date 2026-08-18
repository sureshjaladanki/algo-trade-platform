"""S4-P1 Nifty option snapshot store — remaining-session V2 marks.

Until ``data/GOLDEN_IV/nifty_option_snapshots.parquet`` exists,
``load_nifty_option_snapshots`` raises with a pointer to the S4-P1 charter.
EOD bhavcopy is not this store.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from src.horizon.m9.v2p_range import V2P_POST_OPEN_MIN_TIME
from src.horizon.session import MIS_EXIT_BAR_END

DEFAULT_SNAPSHOT_PATH = Path("data/GOLDEN_IV/nifty_option_snapshots.parquet")
COVERAGE_GATE = 0.70
ENTRY_CLOCK = V2P_POST_OPEN_MIN_TIME
EXIT_CLOCK = MIS_EXIT_BAR_END
UNDERLYING = "^NSEI"

REQUIRED_COLS: tuple[str, ...] = (
    "underlying",
    "date_only",
    "time_only",
    "spot",
    "expiry",
    "strike",
    "ce_bid",
    "ce_ask",
    "pe_bid",
    "pe_ask",
    "source",
)

# Finance Act 2026, effective 2026-04-01. Seller, on option premium.
STT_OPTIONS_SELL = 0.0015
# Sample-era companion (pre-Oct-2024 options STT on premium).
STT_OPTIONS_SELL_SAMPLE = 0.000625
TICK_INR = 0.05


class IndexOptionStoreMissingError(FileNotFoundError):
    """Raised when S4-P1 Nifty snapshots have not been materialised."""


def load_nifty_option_snapshots(
    path: Path = DEFAULT_SNAPSHOT_PATH,
) -> pl.DataFrame:
    """Load same-session Nifty chain snapshots; fail fast if S4-P1 is incomplete."""
    if not path.exists():
        raise IndexOptionStoreMissingError(
            f"Nifty option snapshots not found at {path}. "
            "Acquire same-session marks per "
            "docs/next/horizon-successor-s4-p1-index-marks-charter.md "
            "before running V2. EOD bhavcopy is not a remaining-session mark."
        )
    df = pl.read_parquet(path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"snapshot store missing columns {missing}")
    return df.with_columns(
        underlying=pl.col("underlying").cast(pl.Utf8),
        date_only=pl.col("date_only").cast(pl.Date),
        time_only=pl.col("time_only").cast(pl.Time),
        spot=pl.col("spot").cast(pl.Float64),
        expiry=pl.col("expiry").cast(pl.Date),
        strike=pl.col("strike").cast(pl.Float64),
        ce_bid=pl.col("ce_bid").cast(pl.Float64),
        ce_ask=pl.col("ce_ask").cast(pl.Float64),
        pe_bid=pl.col("pe_bid").cast(pl.Float64),
        pe_ask=pl.col("pe_ask").cast(pl.Float64),
        source=pl.col("source").cast(pl.Utf8),
    )


def _straddle_mids(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        straddle_mid=(pl.col("ce_bid") + pl.col("ce_ask") + pl.col("pe_bid") + pl.col("pe_ask"))
        / 2.0,
        straddle_bid=pl.col("ce_bid") + pl.col("pe_bid"),
        straddle_ask=pl.col("ce_ask") + pl.col("pe_ask"),
    )


def session_entry_exit(snapshots: pl.DataFrame) -> pl.DataFrame:
    """One row per session with 09:45 entry and 15:15 exit on the held contract."""
    marked = _straddle_mids(snapshots.filter(pl.col("underlying") == UNDERLYING))
    entry = (
        marked.filter(pl.col("time_only") == ENTRY_CLOCK)
        .select(
            [
                "date_only",
                "expiry",
                "strike",
                pl.col("spot").alias("spot_entry"),
                pl.col("straddle_mid").alias("mid_entry"),
                pl.col("straddle_bid").alias("bid_entry"),
                pl.col("straddle_ask").alias("ask_entry"),
                "source",
            ]
        )
    )
    exit_px = (
        marked.filter(pl.col("time_only") == EXIT_CLOCK)
        .select(
            [
                "date_only",
                "expiry",
                "strike",
                pl.col("straddle_mid").alias("mid_exit"),
                pl.col("straddle_bid").alias("bid_exit"),
                pl.col("straddle_ask").alias("ask_exit"),
            ]
        )
    )
    return entry.join(exit_px, on=["date_only", "expiry", "strike"], how="inner")


def coverage_selected(
    selected_dates: pl.Series,
    session_marks: pl.DataFrame,
) -> dict[str, float | int]:
    """Share of V2p-c selected sessions with both entry and exit marks."""
    n = int(selected_dates.n_unique())
    if n == 0:
        return {"n": 0, "n_marked": 0, "coverage": float("nan")}
    marked = set(session_marks["date_only"].to_list())
    n_marked = sum(1 for d in selected_dates.unique().to_list() if d in marked)
    return {"n": n, "n_marked": n_marked, "coverage": n_marked / n}
