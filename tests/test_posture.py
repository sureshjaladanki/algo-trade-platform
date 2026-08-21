"""PDT counter and margin thresholds."""

from datetime import date, timedelta

from src.posture import (
    MAX_OVERNIGHT_LEVERAGE,
    PDT_DAY_TRADES_BELOW_MIN,
    PDT_MIN_EQUITY,
    PORTFOLIO_MARGIN_MIN_EQUITY,
    REG_T_LEVERAGE,
    PdtState,
    is_portfolio_margin_eligible,
    overnight_gross_allowed,
)


def test_margin_constants() -> None:
    assert PDT_MIN_EQUITY == 25_000.0
    assert REG_T_LEVERAGE == 2.0
    assert PORTFOLIO_MARGIN_MIN_EQUITY == 125_000.0
    assert MAX_OVERNIGHT_LEVERAGE == 1.0
    assert is_portfolio_margin_eligible(125_000.0)
    assert not is_portfolio_margin_eligible(124_999.0)
    assert overnight_gross_allowed(100_000.0) == 100_000.0


def test_three_day_trades_allowed_below_pdt_min() -> None:
    state = PdtState(equity=20_000.0)
    start = date(2026, 3, 2)
    for i in range(PDT_DAY_TRADES_BELOW_MIN):
        session = start + timedelta(days=i)
        assert state.can_day_trade(session)
        state.record_day_trade(session)
    assert not state.can_day_trade(start + timedelta(days=3))
    assert not state.flagged_as_pdt


def test_fourth_day_trade_flags_pdt_and_restricts_below_min() -> None:
    state = PdtState(equity=20_000.0)
    start = date(2026, 3, 2)
    for i in range(4):
        state.record_day_trade(start + timedelta(days=i))
    assert state.flagged_as_pdt
    assert state.restriction_until == date(2026, 3, 5) + timedelta(days=90)
    assert not state.can_day_trade(date(2026, 4, 1))


def test_futures_never_count_as_day_trades() -> None:
    state = PdtState(equity=20_000.0)
    session = date(2026, 3, 2)
    for _ in range(10):
        assert state.can_day_trade(session, is_futures=True)
        state.record_day_trade(session, is_futures=True)
    assert state.day_trades == []
    assert not state.flagged_as_pdt


def test_above_pdt_min_allows_day_trades() -> None:
    state = PdtState(equity=25_000.0)
    start = date(2026, 3, 2)
    for i in range(6):
        session = start + timedelta(days=i)
        assert state.can_day_trade(session)
        state.record_day_trade(session)
    assert state.flagged_as_pdt
    assert state.restriction_until is None
