"""P2 C0 disaster clip — left tail is realized, not dropped."""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from src.horizon.successor.fade_bound import (
    DISASTER_SL,
    attach_clipped_side_drift,
    attach_multiday_close_drift,
)


def test_disaster_stop_clips_instead_of_dropping() -> None:
    day = dt.date(2018, 1, 2)
    stock = pl.DataFrame(
        {
            "symbol": ["A", "A"],
            "date": [
                dt.datetime.combine(day, dt.time(10, 15)),
                dt.datetime.combine(day, dt.time(15, 15)),
            ],
            "close": [100.0, 80.0],  # −20% into flatten vs 500 bps floor
        }
    )
    events = pl.DataFrame(
        {
            "symbol": ["A"],
            "date": [dt.datetime.combine(day, dt.time(10, 15))],
            "date_only": [day],
            "close": [100.0],
            "side": ["short"],
            "rule_id": ["prior_day_high_reject"],
        }
    )
    out = attach_clipped_side_drift(events, stock)
    assert out.height == 1
    # Short profits from the drop; clip binds on adverse (long-side) disasters.
    # Rebuild an adverse long path to prove the floor.
    events_long = events.with_columns(side=pl.lit("long"))
    out_long = attach_clipped_side_drift(events_long, stock)
    assert out_long.height == 1
    assert out_long["side_drift"][0] == -DISASTER_SL


def test_multiday_close_drift_uses_daily_close_and_clips() -> None:
    days = [dt.date(2018, 1, d) for d in (2, 3, 4, 5)]
    daily = pl.DataFrame(
        {
            "symbol": ["A"] * 4,
            "date": days,
            "close": [100.0, 101.0, 102.0, 80.0],
        }
    )
    events = pl.DataFrame(
        {
            "symbol": ["A", "A"],
            "date": [
                dt.datetime.combine(days[0], dt.time(10, 15)),
                dt.datetime.combine(days[0], dt.time(11, 15)),
            ],
            "date_only": [days[0], days[0]],
            "close": [99.0, 98.0],
            "side": ["short", "short"],
            "rule_id": ["prior_day_high_reject", "prior_day_high_reject"],
        }
    )
    out = attach_multiday_close_drift(events, daily, horizon_sessions=3)
    assert out.height == 1
    assert out["entry_close"][0] == 100.0
    assert out["exit_close"][0] == 80.0
    assert out["side_drift"][0] == pytest.approx(0.20)

    events_long = events.with_columns(side=pl.lit("long"))
    out_long = attach_multiday_close_drift(events_long, daily, horizon_sessions=3)
    assert out_long.height == 1
    assert out_long["side_drift"][0] == -DISASTER_SL
    assert out_long["side_drift_raw"][0] == pytest.approx(-0.20)
