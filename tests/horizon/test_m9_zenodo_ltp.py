"""Zenodo last-trade ATM snapshots — report-only, not quote V2."""

from __future__ import annotations

import datetime as dt

import polars as pl
import pytest

from src.horizon.m9.index_option_store import (
    ENTRY_CLOCK,
    EXIT_CLOCK,
    session_entry_exit,
)
from src.horizon.m9.zenodo_ltp import (
    SOURCE_ID,
    build_zenodo_snapshots,
    clip_expiry_to_last_trade,
    is_zenodo_last_trade,
    last_thursday,
    parse_contract_name,
    parse_expiry_label,
)


def test_parse_contract_name_both_layouts() -> None:
    assert parse_contract_name("CE 10600.txt") == ("CE", 10600.0)
    assert parse_contract_name("NIFTY10200PE") == ("PE", 10200.0)
    assert parse_contract_name("NIFTY10900CE.csv") == ("CE", 10900.0)


def test_expiry_from_range_or_last_thursday() -> None:
    assert last_thursday(2018, 2) == dt.date(2018, 2, 22)
    assert last_thursday(2019, 1) == dt.date(2019, 1, 31)
    assert parse_expiry_label("February 2018.zip") == dt.date(2018, 2, 22)
    assert parse_expiry_label(
        "April/CSV 11-03-19 to 25-04-19 (Expiry Day).zip"
    ) == dt.date(2019, 4, 25)


def _tick(
    day: dt.date,
    t: dt.time,
    expiry: dt.date,
    strike: float,
    opt: str,
    close: float,
) -> dict:
    return {
        "date_only": day,
        "time_only": t,
        "expiry": expiry,
        "strike": strike,
        "opt_type": opt,
        "close": close,
    }


def test_atm_prefers_dte_band_and_drops_zero_dte() -> None:
    day = dt.date(2018, 2, 1)
    near = dt.date(2018, 2, 8)
    pin = day
    far = dt.date(2018, 2, 22)
    ticks = pl.DataFrame(
        [
            _tick(day, ENTRY_CLOCK, pin, 10500, "CE", 1.0),
            _tick(day, ENTRY_CLOCK, pin, 10500, "PE", 1.0),
            _tick(day, ENTRY_CLOCK, near, 10500, "CE", 40.0),
            _tick(day, ENTRY_CLOCK, near, 10500, "PE", 42.0),
            _tick(day, ENTRY_CLOCK, far, 10500, "CE", 80.0),
            _tick(day, ENTRY_CLOCK, far, 10500, "PE", 80.0),
            _tick(day, EXIT_CLOCK, near, 10500, "CE", 20.0),
            _tick(day, EXIT_CLOCK, near, 10500, "PE", 21.0),
            _tick(day, EXIT_CLOCK, far, 10500, "CE", 70.0),
            _tick(day, EXIT_CLOCK, far, 10500, "PE", 70.0),
        ]
    )
    spots = pl.DataFrame(
        [
            {"date_only": day, "time_only": ENTRY_CLOCK, "spot": 10510.0},
            {"date_only": day, "time_only": EXIT_CLOCK, "spot": 10520.0},
        ]
    )
    snaps = build_zenodo_snapshots(ticks, spots)
    assert snaps.height == 2
    assert snaps["expiry"][0] == near
    assert snaps["ce_bid"][0] == pytest.approx(40.0)
    assert snaps["ce_ask"][0] == pytest.approx(40.0)
    assert snaps["source"][0] == SOURCE_ID
    assert is_zenodo_last_trade(snaps)


def test_atm_falls_back_to_nearest_monthly_when_band_empty() -> None:
    day = dt.date(2018, 2, 1)
    far = dt.date(2018, 2, 22)
    farther = dt.date(2018, 3, 28)
    ticks = pl.DataFrame(
        [
            _tick(day, ENTRY_CLOCK, far, 10500, "CE", 80.0),
            _tick(day, ENTRY_CLOCK, far, 10500, "PE", 81.0),
            _tick(day, ENTRY_CLOCK, farther, 10500, "CE", 120.0),
            _tick(day, ENTRY_CLOCK, farther, 10500, "PE", 121.0),
            _tick(day, EXIT_CLOCK, far, 10500, "CE", 70.0),
            _tick(day, EXIT_CLOCK, far, 10500, "PE", 71.0),
            _tick(day, EXIT_CLOCK, farther, 10500, "CE", 110.0),
            _tick(day, EXIT_CLOCK, farther, 10500, "PE", 111.0),
        ]
    )
    spots = pl.DataFrame(
        [
            {"date_only": day, "time_only": ENTRY_CLOCK, "spot": 10500.0},
            {"date_only": day, "time_only": EXIT_CLOCK, "spot": 10500.0},
        ]
    )
    snaps = build_zenodo_snapshots(ticks, spots)
    assert snaps["expiry"][0] == far


def test_clip_expiry_uses_last_trade_when_thursday_is_holiday() -> None:
    ticks = pl.DataFrame(
        [
            _tick(dt.date(2018, 3, 27), ENTRY_CLOCK, dt.date(2018, 3, 29), 10100, "CE", 10.0),
            _tick(dt.date(2018, 3, 28), ENTRY_CLOCK, dt.date(2018, 3, 29), 10100, "CE", 5.0),
        ]
    )
    clipped = clip_expiry_to_last_trade(ticks)
    assert set(clipped["expiry"].to_list()) == {dt.date(2018, 3, 28)}


def test_missing_exit_minute_drops_session() -> None:
    day = dt.date(2018, 2, 1)
    expiry = dt.date(2018, 2, 8)
    ticks = pl.DataFrame(
        [
            _tick(day, ENTRY_CLOCK, expiry, 10500, "CE", 40.0),
            _tick(day, ENTRY_CLOCK, expiry, 10500, "PE", 42.0),
        ]
    )
    spots = pl.DataFrame(
        [{"date_only": day, "time_only": ENTRY_CLOCK, "spot": 10500.0}]
    )
    snaps = build_zenodo_snapshots(ticks, spots)
    assert snaps.height == 0
    assert session_entry_exit(snaps).height == 0
