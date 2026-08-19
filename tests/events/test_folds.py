import datetime as dt

from src.events.constants import PURGE_CALENDAR_DAYS
from src.events.folds import rolling_year_folds


def test_rolling_year_folds_apply_five_day_purge() -> None:
    folds = rolling_year_folds(2018, 2018)
    assert len(folds) == 1
    assert folds[0].fold_id == "R2018"
    assert folds[0].purge_calendar_days == PURGE_CALENDAR_DAYS
    assert folds[0].train_end == dt.date(2017, 12, 31) - dt.timedelta(
        days=PURGE_CALENDAR_DAYS
    )
