"""L2: §6.1 limits by ₹1, deferral across the 12-month line, exemption harvest."""

from datetime import date
from decimal import Decimal

import pytest

from src.books.ledger import Lot
from src.portfolio import (
    DESIGN_EQUITY,
    LimitError,
    apply_realisation,
    assert_active,
    assert_gross,
    assert_margin,
    assert_no_naked_short_options,
    assert_no_single_stock_derivatives,
    assert_overnight_4sigma,
    assert_portfolio,
    assert_sector,
    assert_single_name,
    tracking_error_bps,
)
from src.tax import add_months, stcg


def test_limits_fail_when_breached_by_one_rupee() -> None:
    equity = DESIGN_EQUITY
    assert_gross(equity, equity)
    with pytest.raises(LimitError):
        assert_gross(equity + Decimal("1.00"), equity)

    assert_active(equity * Decimal("0.40"), equity)
    with pytest.raises(LimitError):
        assert_active(equity * Decimal("0.40") + Decimal("1.00"), equity)

    assert_single_name(equity * Decimal("0.06"), equity)
    with pytest.raises(LimitError):
        assert_single_name(equity * Decimal("0.06") + Decimal("1.00"), equity)

    assert_sector(equity * Decimal("0.25"), equity)
    with pytest.raises(LimitError):
        assert_sector(equity * Decimal("0.25") + Decimal("1.00"), equity)

    sigma = Decimal("0.01")
    max_pos = (equity * Decimal("0.02")) / (Decimal(4) * sigma)
    assert_overnight_4sigma(max_pos, sigma, equity)
    with pytest.raises(LimitError):
        assert_overnight_4sigma(max_pos + Decimal("1.00"), sigma, equity)

    assert_no_naked_short_options(0)
    with pytest.raises(LimitError):
        assert_no_naked_short_options(1)
    assert_no_single_stock_derivatives(0)
    with pytest.raises(LimitError):
        assert_no_single_stock_derivatives(1)

    assert_margin(equity / Decimal("1.25"), equity)
    with pytest.raises(LimitError):
        assert_margin(equity / Decimal("1.25") + Decimal("1.00"), equity)


def _year_lots() -> list[Lot]:
    """Twenty names. N00 was bought 11 months before 2026-06-30."""
    lots = []
    for i in range(20):
        symbol = f"N{i:02d}"
        acquired = date(2025, 4, 1)
        if symbol == "N00":
            acquired = date(2025, 7, 15)
        sector = "IT" if i < 5 else "BANK" if i < 10 else "ENERGY"
        lots.append(
            Lot(
                symbol=symbol,
                quantity=Decimal(125),
                acquired=acquired,
                cost_per_share=Decimal(800),
                price=Decimal(1000),
                sector=sector,
                sleeve="core",
            )
        )
    return lots


def test_simulated_year_defers_across_12_month_line_and_harvests() -> None:
    lots = _year_lots()
    equity = DESIGN_EQUITY
    total = Decimal(20) * Decimal(125) * Decimal(1000)
    equal = Decimal(125000) / total
    targets = {lot.symbol: equal for lot in lots}
    targets["N00"] = equal * Decimal("0.90")
    as_of = date(2026, 6, 30)
    assert add_months(date(2025, 7, 15), 12) == date(2026, 7, 15)
    result = apply_realisation(lots, targets, as_of, max_defer_sessions=63)
    assert result.deferred
    assert any(d.symbol == "N00" for d in result.deferred)
    assert result.log
    assert "DEFER" in result.log[0]
    assert result.deferred[0].rupees_saved == stcg(Decimal(2500))
    te = tracking_error_bps(lots, result.deferred)
    assert te <= Decimal(150)

    march = apply_realisation(
        lots,
        {lot.symbol: equal for lot in lots},
        date(2027, 3, 31),
        harvest_exemption=True,
    )
    assert march.harvested.sells
    harvested_gain = sum((s.gain for s in march.harvested.sells), Decimal(0))
    assert harvested_gain > 0
    assert harvested_gain <= Decimal(125000)
    assert any("HARVEST" in line for line in march.log)

    sigmas = {lot.symbol: Decimal("0.01") for lot in lots}
    assert_portfolio(lots, equity, sigmas)
