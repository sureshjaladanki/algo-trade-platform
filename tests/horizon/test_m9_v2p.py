"""V2p session selection — residual > 0 at the first eligible bar."""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from src.horizon.m9.v2p_range import (
    V2P_RESIDUAL_THRESHOLD,
    select_v2p_post_open_sessions,
    select_v2p_sessions,
)


def test_v2p_selects_positive_residual_first_bar_only() -> None:
    d1 = dt.date(2018, 1, 2)
    d2 = dt.date(2018, 1, 3)
    rows = [
        {
            "date": dt.datetime.combine(d1, dt.time(10, 0)),
            "date_only": d1,
            "range_q50": 0.03,
            "range_imp_vix": 0.02,
            "remaining_range": 0.04,
        },
        {
            "date": dt.datetime.combine(d1, dt.time(11, 0)),
            "date_only": d1,
            "range_q50": 0.01,
            "range_imp_vix": 0.02,
            "remaining_range": 0.02,
        },
        {
            "date": dt.datetime.combine(d2, dt.time(10, 0)),
            "date_only": d2,
            "range_q50": 0.01,
            "range_imp_vix": 0.02,
            "remaining_range": 0.015,
        },
    ]
    selected = select_v2p_sessions(pl.DataFrame(rows))
    assert V2P_RESIDUAL_THRESHOLD == 0.0
    assert selected.height == 1
    assert selected["date_only"][0] == d1


def test_v2p_post_open_skips_bleed_bar() -> None:
    d1 = dt.date(2018, 1, 2)
    rows = [
        {
            "date": dt.datetime.combine(d1, dt.time(9, 30)),
            "date_only": d1,
            "time_only": dt.time(9, 30),
            "range_q50": 0.05,
            "range_imp_vix": 0.01,
            "remaining_range": 0.06,
        },
        {
            "date": dt.datetime.combine(d1, dt.time(9, 45)),
            "date_only": d1,
            "time_only": dt.time(9, 45),
            "range_q50": 0.03,
            "range_imp_vix": 0.02,
            "remaining_range": 0.04,
        },
    ]
    selected = select_v2p_post_open_sessions(pl.DataFrame(rows))
    assert selected.height == 1
    assert selected["date"][0].time() == dt.time(9, 45)
    assert selected["residual"][0] == pytest.approx(0.01)


def test_v2p_zero_keeps_bleed_when_post_open_residual_is_negative() -> None:
    d1 = dt.date(2018, 1, 2)
    rows = [
        {
            "date": dt.datetime.combine(d1, dt.time(9, 30)),
            "date_only": d1,
            "time_only": dt.time(9, 30),
            "range_q50": 0.05,
            "range_imp_vix": 0.01,
            "remaining_range": 0.06,
        },
        {
            "date": dt.datetime.combine(d1, dt.time(9, 45)),
            "date_only": d1,
            "time_only": dt.time(9, 45),
            "range_q50": 0.01,
            "range_imp_vix": 0.02,
            "remaining_range": 0.02,
        },
    ]
    panel = pl.DataFrame(rows)
    zero = select_v2p_sessions(panel)
    post = select_v2p_post_open_sessions(panel)
    assert zero.height == 1
    assert zero["date"][0].time() == dt.time(9, 30)
    assert post.height == 0
