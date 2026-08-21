"""C1: location, bands, harvest audit, five-year retrospective vs static VTI."""

from pathlib import Path

import pytest

from src.books.tax_engine import (
    C1_HURDLE_BPS,
    HARVEST_QUARANTINE_DAYS,
    in_rebalance_band,
    locate,
    mes_overlay_notional,
    run_harvest_sim,
)
from src.tax import Wrapper
from src.vti import fetch_yahoo_bars, load_daily_bars, write_daily_bars

DAILY = Path(__file__).resolve().parent.parent / "data" / "raw" / "vti_daily.csv"


def test_high_turnover_locates_to_ira() -> None:
    assert locate(turnover_per_year=12.0, is_1256=False, ira_room_usd=7_000) is Wrapper.IRA
    assert locate(turnover_per_year=12.0, is_1256=False, ira_room_usd=0) is Wrapper.TAXABLE
    assert locate(turnover_per_year=0.1, is_1256=False, ira_room_usd=7_000) is Wrapper.TAXABLE
    assert locate(turnover_per_year=12.0, is_1256=True, ira_room_usd=7_000) is Wrapper.TAXABLE


def test_rebalance_band_and_mes_overlay() -> None:
    assert in_rebalance_band(0.62, 0.60)
    assert not in_rebalance_band(0.70, 0.60)
    assert mes_overlay_notional(equity_usd=100_000, weight=0.62, target=0.60) == 0.0
    overlay = mes_overlay_notional(equity_usd=100_000, weight=0.70, target=0.60)
    assert overlay == pytest.approx(-10_000.0)


def test_harvest_quarantine_is_31_days() -> None:
    assert HARVEST_QUARANTINE_DAYS == 31


def _bars():
    if DAILY.exists():
        return load_daily_bars(DAILY)
    bars = fetch_yahoo_bars()
    write_daily_bars(bars, DAILY)
    return bars


def test_five_year_harvest_beats_static_vti_by_25bps_with_zero_washes() -> None:
    result = run_harvest_sim(_bars())
    assert result.wash_sale_violations == 0
    assert result.audit
    assert all(event.buy_symbol != event.sell_symbol for event in result.audit)
    assert result.excess_bps_per_year >= C1_HURDLE_BPS
    assert result.passed
