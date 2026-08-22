"""A2 sleeve economics. Synthetic cycles; no dump peek."""

from datetime import date

import pytest

from src.books.vrp_sleeve import (
    C1_MEASURED_BPS,
    PUTW_HURDLE_BPS,
    SLEEVE_NOTIONAL,
    SLEEVE_WEIGHT,
    CyclePnl,
    after_tax_cagr,
    blend_excess_bps,
    run_sleeve_screen,
    screen_declaration,
    sleeve_max_dd,
)
from src.tax import SECTION_1256_BLEND
from src.vti import IndexPoint
from src.yahoo import DailyBar


def _cycle(day: date, pnl: float, *, exit: date | None = None) -> CyclePnl:
    end = exit or day
    return CyclePnl(
        entry=day,
        expiry=end,
        exit=end,
        n_contracts=1,
        pnl_usd=pnl,
        max_loss_usd=4_000.0,
        cash_settled=True,
    )


def test_a2_declaration_clears_mde() -> None:
    decl = screen_declaration(144)
    assert decl.clears_gate
    assert decl.spec_id == "A.spx-put-spread-sleeve-a2"


def test_after_tax_cagr_applies_1256_blend() -> None:
    cycles = [_cycle(date(2012, 1, 20), 5_000.0, exit=date(2013, 1, 20))]
    cagr = after_tax_cagr(cycles, years=1.0)
    after = 5_000.0 * (1.0 - SECTION_1256_BLEND)
    assert cagr == pytest.approx(after / SLEEVE_NOTIONAL)


def test_blend_dilutes_when_sleeve_loses_to_vti() -> None:
    vti = 0.15
    sleeve = 0.05
    bps = blend_excess_bps(sleeve_cagr=sleeve, vti_cagr=vti, weight=SLEEVE_WEIGHT)
    assert bps < C1_MEASURED_BPS
    tied = blend_excess_bps(
        sleeve_cagr=vti + C1_MEASURED_BPS / 1e4, vti_cagr=vti, weight=SLEEVE_WEIGHT
    )
    assert tied == pytest.approx(C1_MEASURED_BPS)


def test_max_dd_is_fraction_of_sleeve_notional() -> None:
    cycles = [
        _cycle(date(2012, 1, 20), 0.0, exit=date(2012, 2, 17)),
        _cycle(date(2012, 2, 20), -10_000.0, exit=date(2012, 3, 16)),
    ]
    expected = 10_000.0 * (1.0 - SECTION_1256_BLEND) / SLEEVE_NOTIONAL
    assert sleeve_max_dd(cycles) == pytest.approx(expected)


def test_sleeve_screen_identity() -> None:
    cycles = [
        _cycle(date(2012, 1, 20), 2_000.0, exit=date(2012, 2, 17)),
        _cycle(date(2012, 2, 20), 2_000.0, exit=date(2012, 3, 16)),
        _cycle(date(2013, 1, 20), 2_000.0, exit=date(2013, 2, 15)),
    ]
    putw = [
        DailyBar(date(2012, 1, 20), close=100.0),
        DailyBar(date(2013, 2, 15), close=105.0),
    ]
    vti = [
        IndexPoint(date(2012, 1, 20), before_tax=1.0, after_tax=1.0),
        IndexPoint(date(2013, 2, 15), before_tax=1.10, after_tax=1.08),
    ]
    screen = run_sleeve_screen(cycles, putw=putw, vti_points=vti)
    assert screen.n == 3
    assert PUTW_HURDLE_BPS == 75.0
    assert screen.passed is (
        screen.beat_putw and screen.sharpe_ok and screen.dd_ok and screen.no_dilute
    )
