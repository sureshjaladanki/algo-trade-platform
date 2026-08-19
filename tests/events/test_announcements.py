import datetime as dt

import polars as pl

from src.events.announcements import (
    ANNOUNCEMENTS,
    attach_announcement_dates,
    ledger_covers_replacements,
)
from src.events.event_pool import build_membership_events
from src.events.membership import REPLACEMENTS
from src.events.residual import first_session_on_or_after


def test_announcement_table_covers_every_replacement() -> None:
    assert len(ANNOUNCEMENTS) == len(REPLACEMENTS)
    assert ledger_covers_replacements()


def test_announcement_is_on_or_before_effective() -> None:
    for row in ANNOUNCEMENTS:
        assert row.announcement_date <= row.ledger_effective


def test_attach_sets_recovered_status() -> None:
    dates = [dt.date(2020, 3, 18), dt.date(2020, 3, 19)]
    events = attach_announcement_dates(build_membership_events(dates))
    adds = events.filter(pl.col("event_type") == "addition")
    assert adds["announcement_date"][0] == dt.date(2020, 3, 16)
    assert adds["announcement_date_status"][0] == "recovered_free"


def test_first_session_on_or_after_skips_weekend() -> None:
    calendar = [dt.date(2020, 3, 16), dt.date(2020, 3, 17), dt.date(2020, 3, 18)]
    assert first_session_on_or_after(calendar, dt.date(2020, 3, 15)) == dt.date(
        2020, 3, 16
    )
