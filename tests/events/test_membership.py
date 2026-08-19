import datetime as dt

import polars as pl

from src.events.event_pool import build_membership_events
from src.events.membership import nifty50_members_on


def test_nifty50_has_fifty_names() -> None:
    assert len(nifty50_members_on(dt.date(2025, 12, 8))) == 50
    assert len(nifty50_members_on(dt.date(2016, 6, 1))) == 50


def test_walk_includes_excluded_name_before_effective_date() -> None:
    assert "YESBANK.NS" in nifty50_members_on(dt.date(2020, 3, 18))
    assert "YESBANK.NS" not in nifty50_members_on(dt.date(2020, 3, 19))
    assert "SHREECEM.NS" in nifty50_members_on(dt.date(2020, 3, 19))


def test_differencing_recovers_replacement() -> None:
    dates = [dt.date(2020, 3, 18), dt.date(2020, 3, 19)]
    events = build_membership_events(dates)
    adds = events.filter(pl.col("event_type") == "addition")["symbol"].to_list()
    dels = events.filter(pl.col("event_type") == "deletion")["symbol"].to_list()
    assert adds == ["SHREECEM.NS"]
    assert dels == ["YESBANK.NS"]
    assert events["announcement_date_status"][0] == "unrecoverable_from_pit"
    assert events["announcement_date"][0] is None
