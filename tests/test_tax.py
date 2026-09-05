"""P0: tax reproduces a hand-worked Tax Year 2026-27 mixed book to within ₹1."""

from datetime import date
from decimal import Decimal

from src.tax import (
    AuditTrade,
    BusinessKind,
    CarryLedgers,
    audit_turnover,
    business_income,
    long_term_holding,
    ltcg,
    stcg,
    tax_year,
    tax_year_start,
)


def _d(value: str) -> Decimal:
    return Decimal(value)


def test_tax_year_is_april_to_march() -> None:
    assert tax_year(date(2026, 4, 1)) == "2026-27"
    assert tax_year(date(2027, 3, 31)) == "2026-27"
    assert tax_year(date(2026, 3, 31)) == "2025-26"
    assert tax_year_start(date(2026, 6, 1)) == 2026


def test_long_term_holding_is_twelve_calendar_months() -> None:
    assert long_term_holding(date(2025, 9, 5), date(2026, 9, 5))
    assert not long_term_holding(date(2025, 9, 6), date(2026, 9, 5))
    assert long_term_holding(date(2024, 2, 29), date(2025, 2, 28))
    assert stcg(_d("80000")) == _d("16640.00")


def test_ltcg_exemption_and_cess() -> None:
    assert ltcg(_d("200000"), exemption_used=_d("0")) == _d("9750.00")
    assert ltcg(_d("100000"), exemption_used=_d("0")) == _d("0.00")
    assert ltcg(_d("100000"), exemption_used=_d("125000")) == _d("13000.00")


def test_mixed_book_tax_year_2026_27_within_one_rupee() -> None:
    """Delivery 14 months + 5 months, intraday loss, F&O loss. See p0-cost-verification.md."""
    ltcg_tax = ltcg(_d("200000"), exemption_used=_d("0"))
    stcg_tax = stcg(_d("80000"))
    capital = ltcg_tax + stcg_tax
    assert abs(capital - _d("26390.00")) <= _d("1")

    ledgers = CarryLedgers()
    intra = business_income(_d("-40000"), BusinessKind.SPECULATIVE, 2026, ledgers)
    fo = business_income(_d("-120000"), BusinessKind.NON_SPECULATIVE, 2026, ledgers)
    assert intra.tax == _d("0.00")
    assert fo.tax == _d("0.00")
    assert intra.carried == _d("40000.00")
    assert intra.years_allowed == 4
    assert fo.carried == _d("120000.00")
    assert fo.years_allowed == 8
    assert ledgers.remaining(BusinessKind.SPECULATIVE, 2027) == _d("40000.00")
    assert ledgers.remaining(BusinessKind.NON_SPECULATIVE, 2027) == _d("120000.00")
    assert ledgers.remaining(BusinessKind.SPECULATIVE, 2031) == _d("0.00")
    assert ledgers.remaining(BusinessKind.NON_SPECULATIVE, 2035) == _d("0.00")


def test_speculative_loss_does_not_offset_fno() -> None:
    ledgers = CarryLedgers()
    business_income(_d("-40000"), BusinessKind.SPECULATIVE, 2026, ledgers)
    fo = business_income(_d("40000"), BusinessKind.NON_SPECULATIVE, 2027, ledgers)
    assert fo.taxable_income == _d("40000")
    assert ledgers.remaining(BusinessKind.SPECULATIVE, 2027) == _d("40000.00")


def test_speculative_loss_offsets_only_speculative_profit() -> None:
    ledgers = CarryLedgers()
    business_income(_d("-40000"), BusinessKind.SPECULATIVE, 2026, ledgers)
    later = business_income(_d("10000"), BusinessKind.SPECULATIVE, 2027, ledgers)
    assert later.taxable_income == _d("0.00")
    assert later.tax == _d("0.00")
    assert ledgers.remaining(BusinessKind.SPECULATIVE, 2027) == _d("30000.00")


def test_audit_turnover_absolute_sum_plus_option_premium() -> None:
    result = audit_turnover(
        [
            AuditTrade(pnl=_d("80000")),
            AuditTrade(pnl=_d("-45000")),
            AuditTrade(pnl=_d("25000"), option_premium_sold=_d("60000")),
        ]
    )
    assert result.turnover == _d("210000.00")
    assert not result.crosses_one_crore
    assert not result.crosses_ten_crore


def test_audit_turnover_skips_premium_already_in_pnl() -> None:
    result = audit_turnover(
        [AuditTrade(pnl=_d("10000"), option_premium_sold=_d("60000"), premium_already_in_pnl=True)]
    )
    assert result.turnover == _d("10000.00")


def test_audit_flags_at_one_and_ten_crore() -> None:
    one = audit_turnover([AuditTrade(pnl=_d("10000001"))])
    ten = audit_turnover([AuditTrade(pnl=_d("100000001"))])
    assert one.crosses_one_crore
    assert not one.crosses_ten_crore
    assert ten.crosses_ten_crore
