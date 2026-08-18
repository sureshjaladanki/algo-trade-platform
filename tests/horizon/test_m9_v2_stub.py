"""V2 stub: held ATM-straddle PnL from EOD marks."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.horizon.m9.v2_straddle import (
    held_straddle_pnl,
    morning_long_vol_sessions,
    v2_session_block_gate,
)


def test_morning_long_vol_keeps_first_bar_when_q50_exceeds_implied() -> None:
    panel = pl.DataFrame(
        {
            "symbol": ["RELIANCE.NS", "RELIANCE.NS", "TCS.NS"],
            "date": [
                dt.datetime(2021, 1, 4, 9, 45),
                dt.datetime(2021, 1, 4, 10, 0),
                dt.datetime(2021, 1, 4, 9, 45),
            ],
            "date_only": [dt.date(2021, 1, 4)] * 3,
            "range_q50": [0.03, 0.04, 0.01],
            "range_imp_atm": [0.02, 0.02, 0.02],
        }
    )
    sel = morning_long_vol_sessions(panel)
    assert sel.height == 1
    assert sel["symbol"][0] == "RELIANCE.NS"


def test_held_straddle_pnl_uses_same_strike_next_session() -> None:
    selected = pl.DataFrame(
        {"symbol": ["RELIANCE.NS"], "date_only": [dt.date(2021, 1, 4)]}
    )
    atm = pl.DataFrame(
        {
            "symbol": ["RELIANCE.NS"],
            "date_only": [dt.date(2021, 1, 4)],
            "atm_strike": [2000.0],
            "expiry": [dt.date(2021, 1, 28)],
            "straddle": [40.0],
            "underlying_close": [2000.0],
        }
    )
    marks = pl.DataFrame(
        {
            "symbol": ["RELIANCE.NS", "RELIANCE.NS", "RELIANCE.NS"],
            "date_only": [
                dt.date(2021, 1, 4),
                dt.date(2021, 1, 5),
                dt.date(2021, 1, 6),
            ],
            "expiry": [dt.date(2021, 1, 28)] * 3,
            "strike": [2000.0, 2000.0, 2100.0],
            "straddle": [40.0, 50.0, 99.0],
        }
    )
    pnl = held_straddle_pnl(selected, atm, marks)
    assert pnl.height == 1
    assert pnl["date_exit"][0] == dt.date(2021, 1, 5)
    assert abs(float(pnl["pnl_bps"][0]) - 50.0) < 1e-6
    gate = v2_session_block_gate(pnl, fold="R2021")
    assert gate.n == 1
    assert gate.verdict in {"PASS", "FAIL", "INCONCLUSIVE", "THIN"}
