"""S4-P1 Nifty snapshot store + remaining-session short-straddle PnL."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest

from src.horizon.m9.index_option_store import (
    COVERAGE_GATE,
    ENTRY_CLOCK,
    EXIT_CLOCK,
    IndexOptionStoreMissingError,
    coverage_selected,
    load_nifty_option_snapshots,
    session_entry_exit,
)
from src.horizon.m9.v2_index_straddle import attach_short_straddle_pnl, v2_selected_pnl


def _snap(
    day: dt.date,
    t: dt.time,
    *,
    ce_bid: float,
    ce_ask: float,
    pe_bid: float,
    pe_ask: float,
    spot: float = 10000.0,
) -> dict:
    return {
        "underlying": "^NSEI",
        "date_only": day,
        "time_only": t,
        "spot": spot,
        "expiry": dt.date(2018, 1, 25),
        "strike": 10000.0,
        "ce_bid": ce_bid,
        "ce_ask": ce_ask,
        "pe_bid": pe_bid,
        "pe_ask": pe_ask,
        "source": "test",
    }


def test_load_snapshots_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(IndexOptionStoreMissingError):
        load_nifty_option_snapshots(tmp_path / "missing.parquet")


def test_session_entry_exit_holds_strike_and_clocks() -> None:
    d1 = dt.date(2018, 1, 2)
    rows = [
        _snap(d1, ENTRY_CLOCK, ce_bid=40, ce_ask=42, pe_bid=38, pe_ask=40),
        _snap(d1, EXIT_CLOCK, ce_bid=20, ce_ask=22, pe_bid=18, pe_ask=20),
        _snap(d1, dt.time(10, 0), ce_bid=1, ce_ask=2, pe_bid=1, pe_ask=2),
    ]
    marks = session_entry_exit(pl.DataFrame(rows))
    assert marks.height == 1
    assert marks["mid_entry"][0] == pytest.approx(80.0)
    assert marks["mid_exit"][0] == pytest.approx(40.0)


def test_short_straddle_pnl_is_entry_minus_exit_over_spot() -> None:
    d1 = dt.date(2018, 1, 2)
    rows = [
        _snap(d1, ENTRY_CLOCK, ce_bid=40, ce_ask=42, pe_bid=38, pe_ask=40, spot=10000.0),
        _snap(d1, EXIT_CLOCK, ce_bid=20, ce_ask=22, pe_bid=18, pe_ask=20, spot=10100.0),
    ]
    pnl = attach_short_straddle_pnl(session_entry_exit(pl.DataFrame(rows)))
    assert pnl["pnl"][0] == pytest.approx(40.0 / 10000.0)


def test_v2_join_drops_unmarked_selected_dates() -> None:
    d1 = dt.date(2018, 1, 2)
    d2 = dt.date(2018, 1, 3)
    rows = [
        _snap(d1, ENTRY_CLOCK, ce_bid=40, ce_ask=42, pe_bid=38, pe_ask=40),
        _snap(d1, EXIT_CLOCK, ce_bid=20, ce_ask=22, pe_bid=18, pe_ask=20),
    ]
    selected = pl.DataFrame({"date_only": [d1, d2]})
    marks = session_entry_exit(pl.DataFrame(rows))
    out = v2_selected_pnl(selected, marks)
    assert out.height == 1
    assert out["date_only"][0] == d1
    cov = coverage_selected(selected["date_only"], marks)
    assert cov["n"] == 2
    assert cov["n_marked"] == 1
    assert cov["coverage"] == pytest.approx(0.5)
    assert cov["coverage"] < COVERAGE_GATE
