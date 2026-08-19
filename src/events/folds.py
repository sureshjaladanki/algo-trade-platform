"""Purged calendar-year folds for event peeks.

New peeks use a 5-calendar-day embargo. Dual-fold A/B (2018 / 2019) had no
gap on the closed cascade ledgers — do not silently rewrite those reprints.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from src.events.constants import PURGE_CALENDAR_DAYS


@dataclass(frozen=True)
class YearFold:
    fold_id: str
    test_year: int
    train_end: dt.date
    purge_calendar_days: int = PURGE_CALENDAR_DAYS


def rolling_year_folds(
    start_year: int,
    end_year: int,
    *,
    train_start_year: int = 2015,
    purge_calendar_days: int = PURGE_CALENDAR_DAYS,
) -> list[YearFold]:
    """Expanding train through 31 Dec of (test_year − 1), then purge, then test year."""
    folds: list[YearFold] = []
    for test_year in range(start_year, end_year + 1):
        train_end = dt.date(test_year - 1, 12, 31) - dt.timedelta(
            days=purge_calendar_days
        )
        if test_year - 1 < train_start_year:
            continue
        folds.append(
            YearFold(
                fold_id=f"R{test_year}",
                test_year=test_year,
                train_end=train_end,
                purge_calendar_days=purge_calendar_days,
            )
        )
    return folds
