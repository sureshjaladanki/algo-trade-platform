# Naive IST stamps, matching NSE session close.
# ruff: noqa: DTZ001
import datetime as dt

import polars as pl
import pytest

from src.events.residual import (
    first_session_strictly_after,
    residual_bps,
    window_residual_bps,
)


def test_residual_is_stock_minus_nifty() -> None:
    # stock +10%, nifty +5% → +500 bps
    assert residual_bps(100.0, 110.0, 200.0, 210.0) == pytest.approx(500.0)


def test_first_session_strictly_after_skips_the_announcement_day() -> None:
    calendar = [dt.date(2020, 2, 20), dt.date(2020, 2, 21), dt.date(2020, 2, 24)]
    assert first_session_strictly_after(calendar, dt.date(2020, 2, 20)) == dt.date(
        2020, 2, 21
    )
    assert first_session_strictly_after(calendar, dt.date(2020, 2, 22)) == dt.date(
        2020, 2, 24
    )


def test_window_residual_skips_missing_close() -> None:
    panel = pl.DataFrame(
        {
            "symbol": ["FOO.NS"],
            "date": [dt.date(2020, 1, 2)],
            "close": [110.0],
            "nifty_close": [210.0],
        }
    )
    assert (
        window_residual_bps(panel, "FOO.NS", dt.date(2020, 1, 1), dt.date(2020, 1, 2))
        is None
    )


def test_first_close_containing_maps_after_hours_to_next_session() -> None:
    from src.events.constants import NSE_EQUITY_CLOSE
    from src.events.residual import first_close_containing

    calendar = [dt.date(2020, 1, 2), dt.date(2020, 1, 3), dt.date(2020, 1, 6)]
    same_day = first_close_containing(
        calendar, dt.datetime(2020, 1, 2, 14, 0), NSE_EQUITY_CLOSE
    )
    after_hours = first_close_containing(
        calendar, dt.datetime(2020, 1, 2, 16, 0), NSE_EQUITY_CLOSE
    )
    date_only = first_close_containing(
        calendar, dt.datetime(2020, 1, 2, 0, 0), NSE_EQUITY_CLOSE
    )
    weekend = first_close_containing(
        calendar, dt.datetime(2020, 1, 4, 12, 0), NSE_EQUITY_CLOSE
    )
    assert same_day == dt.date(2020, 1, 2)
    assert after_hours == dt.date(2020, 1, 3)
    assert date_only == dt.date(2020, 1, 3)
    assert weekend == dt.date(2020, 1, 6)
