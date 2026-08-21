"""Book A $0 VIX–RV / PUTW screen. Public data, working costs. Not A1."""

from datetime import date, timedelta

import pytest

from src.books.vrp import (
    VRP_HYPOTHESIZED,
    VRP_SIGMA,
    premium_cost_to_vol_points,
    realized_vol_points,
    run_vrp_screen,
    screen_declaration,
    sign_stable,
    working_premium_cost,
)
from src.costs import WORKING_TABLE, ProductBucket, round_trip_pct_of_premium
from src.harness import HarnessGuardError, print_mde, reset, run_declared
from src.tax import ORDINARY_DIVIDEND_RATE, SECTION_1256_BLEND
from src.yahoo import DailyBar


def setup_function() -> None:
    reset()


def _weekdays(start: date, n: int) -> list[date]:
    days: list[date] = []
    day = start
    while len(days) < n:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


def test_premium_cost_uses_costs_module() -> None:
    assert working_premium_cost("high") == WORKING_TABLE[ProductBucket.SPX_ATM_30_45].all_in_high
    assert working_premium_cost("mid") == round_trip_pct_of_premium(
        ProductBucket.SPX_ATM_30_45
    )
    assert premium_cost_to_vol_points(2.0, 20.0) == pytest.approx(0.40)


def test_flat_spx_gives_zero_realized_vol() -> None:
    closes = [100.0] * 22
    assert realized_vol_points(closes) == pytest.approx(0.0)


def test_vrp_screen_nets_expensive_cost_and_needs_mde_first() -> None:
    days = _weekdays(date(2005, 1, 3), 80)
    spx = [DailyBar(day, close=100.0) for day in days]
    vix = [DailyBar(day, close=20.0) for day in days[:50]]
    with pytest.raises(HarnessGuardError):
        run_declared(lambda: run_vrp_screen(vix, spx))
    print_mde(screen_declaration(240))
    screened = run_declared(lambda: run_vrp_screen(vix, spx))
    high_cost = premium_cost_to_vol_points(working_premium_cost("high"), 20.0)
    assert screened.mean_raw == pytest.approx(20.0)
    assert screened.mean_net_high == pytest.approx(20.0 - high_cost)
    assert screened.mean_net_high > 0
    assert screened.sign_stable_high is False
    assert screened.buy_cboe is False
    assert screened.n >= 2


def test_sign_stable_requires_four_of_five() -> None:
    rows = [
        (date(2005, 1, 1), date(2008, 12, 31), 2.0, 10),
        (date(2009, 1, 1), date(2012, 12, 31), 1.0, 10),
        (date(2013, 1, 1), date(2016, 12, 31), 0.5, 10),
        (date(2017, 1, 1), date(2020, 12, 31), -0.2, 10),
        (date(2021, 1, 1), date(2026, 12, 31), 1.5, 10),
    ]
    assert sign_stable(rows) is True
    rows[2] = (rows[2][0], rows[2][1], -1.0, 10)
    assert sign_stable(rows) is False


def test_putw_ordinary_tax_and_1256_wedge() -> None:
    from src.books.vrp import after_tax_ordinary_series, marked_cagr, putw_report
    from src.vti import after_tax_vti_series

    bars = [
        DailyBar(date(2017, 1, 3), close=100.0),
        DailyBar(date(2017, 3, 15), close=100.0, dividend=2.0),
        DailyBar(date(2017, 12, 29), close=100.0),
        DailyBar(date(2018, 12, 31), close=100.0),
    ]
    ordinary = after_tax_ordinary_series(bars)
    assert ordinary[-1].before_tax == pytest.approx(1.02)
    assert ordinary[-1].after_tax == pytest.approx(1.0 + 0.02 * (1.0 - ORDINARY_DIVIDEND_RATE))
    vti = after_tax_vti_series(bars)
    report = putw_report(bars, vti)
    assert report.putw_after_tax_ordinary < report.putw_before_tax
    assert marked_cagr({2017: 0.10}, SECTION_1256_BLEND) == pytest.approx(0.10 * (1.0 - SECTION_1256_BLEND))


def test_screen_declaration_clears_mde_at_full_n() -> None:
    decl = screen_declaration(240)
    assert decl.sigma == VRP_SIGMA
    assert decl.hypothesized_effect == VRP_HYPOTHESIZED
    assert decl.clears_gate
