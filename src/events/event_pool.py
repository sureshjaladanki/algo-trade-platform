"""Reconstruct membership-change events by differencing PIT flags."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.events.constants import FAMILY_NIFTY_50
from src.events.daily_panel import list_index_price_files
from src.events.membership import (
    ANNOUNCEMENT_DATE_STATUS,
    covered_families,
    nifty50_members_on,
)
from src.events.paths import EVENT_POOL_PARQUET, GOLDEN_DIR, LOGS_DIR

_MEMBERS_ON = {FAMILY_NIFTY_50: nifty50_members_on}


def build_membership_events(
    session_dates: list[dt.date],
    family: str = FAMILY_NIFTY_50,
) -> pl.DataFrame:
    """Addition and deletion rows from consecutive-session membership diffs."""
    members_on = _MEMBERS_ON[family]
    dates = sorted(session_dates)
    rows: list[dict] = []
    prev = members_on(dates[0])
    for day in dates[1:]:
        cur = members_on(day)
        for symbol in sorted(cur - prev):
            rows.append(
                {
                    "family": family,
                    "symbol": symbol,
                    "event_type": "addition",
                    "effective_date": day,
                    "announcement_date": None,
                    "announcement_date_status": ANNOUNCEMENT_DATE_STATUS,
                }
            )
        for symbol in sorted(prev - cur):
            rows.append(
                {
                    "family": family,
                    "symbol": symbol,
                    "event_type": "deletion",
                    "effective_date": day,
                    "announcement_date": None,
                    "announcement_date_status": ANNOUNCEMENT_DATE_STATUS,
                }
            )
        prev = cur
    if not rows:
        return pl.DataFrame(
            schema={
                "family": pl.String,
                "symbol": pl.String,
                "event_type": pl.String,
                "effective_date": pl.Date,
                "announcement_date": pl.Date,
                "announcement_date_status": pl.String,
            }
        )
    return pl.DataFrame(rows).with_columns(
        pl.col("announcement_date").cast(pl.Date)
    )


def flag_tradable_universe(events: pl.DataFrame, panel: pl.DataFrame) -> pl.DataFrame:
    """Mark names that have a GOLDEN close on the effective session."""
    closes = panel.select("symbol", "date", "close").rename(
        {"date": "effective_date"}
    )
    joined = events.join(closes, on=["symbol", "effective_date"], how="left")
    return joined.with_columns(
        in_tradable_universe=pl.col("close").is_not_null()
    ).drop("close")


def count_events_by_year_family(events: pl.DataFrame) -> pl.DataFrame:
    return (
        events.with_columns(year=pl.col("effective_date").dt.year())
        .group_by(["year", "family", "event_type"])
        .agg(n=pl.len())
        .sort(["year", "family", "event_type"])
    )


def f1_gate_support(events: pl.DataFrame) -> dict[str, str]:
    """Which of F1a/F1b/F1c the available dates can actually support."""
    n = events.height
    n_tradable = int(events["in_tradable_universe"].sum()) if n else 0
    announcement = (
        events["announcement_date_status"][0] if n else ANNOUNCEMENT_DATE_STATUS
    )
    return {
        "F1a": (
            "unsupported: announcement dates are "
            f"{announcement}; announcement-to-effective residual cannot run"
        ),
        "F1b": (
            "unsupported: pre-announcement ranking needs the announcement "
            "date; this is F3's job if a free calendar appears later"
        ),
        "F1c": (
            f"supported: post-effective reversal on effective dates "
            f"(n={n}, tradable={n_tradable})"
        ),
        "F1_effective": (
            "supported as the existence test this peek can actually run: "
            "T-20 close to T close residual vs Nifty, dated on the PIT "
            f"difference (n={n}, tradable={n_tradable}). This is not F1a."
        ),
    }


def write_event_pool(events: pl.DataFrame) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    events.write_parquet(EVENT_POOL_PARQUET)


def index_price_families_without_membership(golden_dir=GOLDEN_DIR) -> list[str]:
    return list_index_price_files(golden_dir)


def families_with_membership() -> tuple[str, ...]:
    return covered_families()
