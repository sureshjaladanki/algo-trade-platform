"""Holdout folds and purged walk-forward for fresh Horizon validation.

Legacy dual-fold A/B stay for ledger comparability with M1–M5R. M5P adds
rolling folds with an explicit purge/embargo gap between train and test.
``GBMHorizonModel`` purged windows remain the validation *spirit*, not the
ship path for Stages B–D.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import polars as pl

from src.horizon.horizon_model import (
    DEFAULT_EMBARGO_BARS,
    DEFAULT_EMBARGO_DAYS,
    DEFAULT_TEST_DAYS,
    DEFAULT_TRAIN_DAYS,
    DEFAULT_VAL_DAYS,
)

# Calendar embargo (days) between train_end and test_start on rolling folds.
# Wider than the 1-session model embargo: blocks label leakage across the cut.
DEFAULT_PURGE_CALENDAR_DAYS = 5


@dataclass(frozen=True)
class FoldSpec:
    """One purged train/test window."""

    fold_id: str
    train_period: str  # "YYYY-YYYY" or "YYYY-MM-DD:YYYY-MM-DD"
    test_period: str
    purge_calendar_days: int = DEFAULT_PURGE_CALENDAR_DAYS
    regime_run_id: str | None = None

    @property
    def has_purge(self) -> bool:
        return self.purge_calendar_days > 0


# Dual-fold holdouts — same calendar as production Horizon peeks / EV-net Step 0.
# Adjacent calendar years historically had no explicit gap; M5P records that debt
# and applies purge only on ROLLING_FOLDS (do not silently rewrite A/B ledgers).
FOLDS: dict[str, dict[str, str]] = {
    "A": {
        "train_period": "2015-2017",
        "test_period": "2018-2018",
        "regime_run_id": "e9dbc99428d748f0a78e12281531f27f",
        "purge_calendar_days": "0",
    },
    "B": {
        "train_period": "2016-2018",
        "test_period": "2019-2019",
        "regime_run_id": "7fff95a9410144efb4ac69c10608ee53",
        "purge_calendar_days": "0",
    },
}


def _year_fold(test_year: int, *, train_start: int = 2015) -> FoldSpec:
    """Expanding train ending Dec 31 of (test_year − 1), then purge, then test year."""
    train_end_year = test_year - 1
    return FoldSpec(
        fold_id=f"R{test_year}",
        train_period=f"{train_start}-{train_end_year}",
        test_period=f"{test_year}-{test_year}",
        purge_calendar_days=DEFAULT_PURGE_CALENDAR_DAYS,
    )


# M5P: ≥6 rolling annual holdouts (expanding train, explicit purge).
# Covers 2017–2022 so every fold has a completed calendar year of test mass.
ROLLING_FOLDS: dict[str, FoldSpec] = {
    f"R{y}": _year_fold(y) for y in range(2017, 2023)
}


def fold_spec(fold_id: str) -> FoldSpec:
    """Resolve legacy A/B dict or rolling FoldSpec."""
    if fold_id in ROLLING_FOLDS:
        return ROLLING_FOLDS[fold_id]
    if fold_id not in FOLDS:
        raise KeyError(f"unknown fold {fold_id!r}")
    raw = FOLDS[fold_id]
    return FoldSpec(
        fold_id=fold_id,
        train_period=raw["train_period"],
        test_period=raw["test_period"],
        purge_calendar_days=int(raw.get("purge_calendar_days", "0")),
        regime_run_id=raw.get("regime_run_id"),
    )


def apply_purge_cutoff(train_end_year: int, purge_calendar_days: int) -> str:
    """Inclusive ISO date cutoff for train after calendar purge."""
    end = dt.date(train_end_year, 12, 31)
    if purge_calendar_days > 0:
        end = end - dt.timedelta(days=purge_calendar_days)
    return end.isoformat()


def apply_purge_date_filter(
    df: pl.DataFrame,
    train_end_year: int,
    purge_calendar_days: int,
    *,
    datetime_col: str = "date",
) -> pl.DataFrame:
    """
    Drop rows after the purged train cutoff.

    ``filter_by_period`` is year/month based and cannot express a 5-day embargo
    inside December. Call this *after* the year filter so the last
    ``purge_calendar_days`` of the train year are actually held out.
    """
    if purge_calendar_days <= 0:
        return df
    cutoff = dt.date.fromisoformat(
        apply_purge_cutoff(train_end_year, purge_calendar_days)
    )
    return df.filter(pl.col(datetime_col).dt.date() <= cutoff)


def apply_purge_to_train_end(train_end: str, purge_calendar_days: int) -> str:
    """
    Pull a year / mm/yyyy / ISO train_end back by purge calendar days.

    Year-based ``filter_by_period`` cannot consume this ISO string — use
    ``apply_purge_date_filter`` on the already year-sliced frame instead.
    """
    if purge_calendar_days <= 0:
        return train_end
    if "/" in train_end:
        month_str, year_str = train_end.split("/")
        year, month = int(year_str), int(month_str)
        if month == 12:
            end = dt.date(year, 12, 31)
        else:
            end = dt.date(year, month + 1, 1) - dt.timedelta(days=1)
    elif len(train_end) == 4 and train_end.isdigit():
        return apply_purge_cutoff(int(train_end), purge_calendar_days)
    else:
        end = dt.date.fromisoformat(train_end)
    return (end - dt.timedelta(days=purge_calendar_days)).isoformat()


@dataclass(frozen=True)
class PurgedCvSpirit:
    """Documented walk-forward lengths reused from ``GBMHorizonModel`` defaults."""

    train_days: int = DEFAULT_TRAIN_DAYS
    val_days: int = DEFAULT_VAL_DAYS
    test_days: int = DEFAULT_TEST_DAYS
    embargo_days: int = DEFAULT_EMBARGO_DAYS
    embargo_bars: int = DEFAULT_EMBARGO_BARS
    purge_calendar_days: int = DEFAULT_PURGE_CALENDAR_DAYS


PURGED_CV_SPIRIT = PurgedCvSpirit()
