"""Tax unit tests against hand-worked examples, including IRA wash-sale destruction."""

from datetime import date

import pytest

from src.tax import (
    HARVEST_QUARANTINE_DAYS,
    HOLDING_PERIOD_LT_DAYS,
    LTCG_RATE,
    QD_RATE,
    SECTION_1256_BLEND,
    STCG_RATE,
    WASH_SALE_WINDOW_DAYS,
    Lot,
    LotMethod,
    Purchase,
    Wrapper,
    apply_wash_sale,
    capital_gain_rate,
    close_lots,
    dividend_tax,
    is_qualified_dividend,
    mark_1256_year_end,
    section_1256_tax,
    tax_on_gain,
    tax_on_realization,
    wash_sale_window,
)


def test_working_rates() -> None:
    assert STCG_RATE == 0.40
    assert LTCG_RATE == 0.20
    assert SECTION_1256_BLEND == pytest.approx(0.28)
    assert QD_RATE == 0.20
    assert HARVEST_QUARANTINE_DAYS == WASH_SALE_WINDOW_DAYS + 1


def test_st_lt_and_1256_hand_worked() -> None:
    assert tax_on_gain(1_000.0, holding_days=100, wrapper=Wrapper.TAXABLE) == pytest.approx(400.0)
    assert tax_on_gain(1_000.0, holding_days=366, wrapper=Wrapper.TAXABLE) == pytest.approx(200.0)
    assert section_1256_tax(1_000.0) == pytest.approx(280.0)
    assert capital_gain_rate(1, is_1256=True) == pytest.approx(0.28)
    assert capital_gain_rate(HOLDING_PERIOD_LT_DAYS + 1) == LTCG_RATE
    assert tax_on_gain(1_000.0, holding_days=10, wrapper=Wrapper.IRA) == 0.0


def test_qualified_and_ordinary_dividends() -> None:
    assert dividend_tax(100.0, qualified=True, wrapper=Wrapper.TAXABLE) == pytest.approx(20.0)
    assert dividend_tax(100.0, qualified=False, wrapper=Wrapper.TAXABLE) == pytest.approx(40.0)
    assert dividend_tax(100.0, qualified=True, wrapper=Wrapper.IRA) == 0.0
    ex = date(2024, 6, 17)
    assert is_qualified_dividend(acquired=date(2024, 1, 1), ex_date=ex)
    assert not is_qualified_dividend(
        acquired=date(2024, 6, 10), ex_date=ex, sold=date(2024, 6, 20)
    )


def _lot(
    lot_id: str,
    qty: float,
    basis: float,
    acquired: date,
    *,
    wrapper: Wrapper = Wrapper.TAXABLE,
    symbol: str = "VTI",
    is_1256: bool = False,
    account_id: str = "taxable-1",
) -> Lot:
    return Lot(
        lot_id=lot_id,
        taxpayer_id="hh1",
        account_id=account_id,
        wrapper=wrapper,
        symbol=symbol,
        quantity=qty,
        cost_basis=basis,
        acquired=acquired,
        is_1256=is_1256,
    )


def test_fifo_closes_oldest_lots_first() -> None:
    lots = [
        _lot("a", 100, 10_000, date(2020, 1, 2)),
        _lot("b", 100, 12_000, date(2021, 1, 4)),
        _lot("c", 100, 15_000, date(2022, 1, 3)),
    ]
    remaining, realized = close_lots(
        lots, symbol="VTI", quantity=150, proceeds=22_500, closed=date(2024, 6, 1)
    )
    assert [r.lot_id for r in realized] == ["a", "b"]
    assert realized[0].quantity == 100
    assert realized[1].quantity == 50
    assert remaining[0].lot_id == "c"
    leftover_b = next(lot for lot in remaining if lot.lot_id == "b")
    assert leftover_b.quantity == 50
    assert leftover_b.cost_basis == pytest.approx(6_000)


def test_specific_lot_closes_named_lot() -> None:
    lots = [
        _lot("a", 100, 10_000, date(2020, 1, 2)),
        _lot("c", 100, 15_000, date(2022, 1, 3)),
    ]
    remaining, realized = close_lots(
        lots,
        symbol="VTI",
        quantity=100,
        proceeds=16_000,
        closed=date(2024, 6, 1),
        method=LotMethod.SPECIFIC,
        lot_ids=("c",),
    )
    assert [r.lot_id for r in realized] == ["c"]
    assert realized[0].gain == pytest.approx(1_000)
    assert remaining[0].lot_id == "a"


def test_wash_sale_inside_window_rolls_into_replacement_basis() -> None:
    sale = date(2024, 6, 1)
    replacement = Purchase(
        lot_id="r1",
        taxpayer_id="hh1",
        account_id="taxable-1",
        wrapper=Wrapper.TAXABLE,
        symbol="VTI",
        quantity=100,
        cost_basis=9_200,
        trade_date=date(2024, 6, 10),
    )
    wash = apply_wash_sale(
        symbol="VTI",
        quantity_sold=100,
        loss=-1_000,
        sale_date=sale,
        taxpayer_id="hh1",
        sold_lot_id="s1",
        purchases=(replacement,),
    )
    assert wash.disallowed == pytest.approx(1_000)
    assert not wash.ira_destroyed
    assert wash.replacement_basis_add == pytest.approx(1_000)
    lots = [_lot("s1", 100, 10_000, date(2023, 1, 3)), _lot("r1", 100, 9_200, date(2024, 6, 10))]
    remaining, realized = close_lots(
        lots,
        symbol="VTI",
        quantity=100,
        proceeds=9_000,
        closed=sale,
        method=LotMethod.SPECIFIC,
        lot_ids=("s1",),
        purchases=(replacement,),
    )
    assert realized[0].wash_disallowed == pytest.approx(1_000)
    assert realized[0].recognized_gain == pytest.approx(0.0)
    repl = next(lot for lot in remaining if lot.lot_id == "r1")
    assert repl.cost_basis == pytest.approx(10_200)


def test_wash_sale_outside_31_day_quarantine_is_allowed() -> None:
    replacement = Purchase(
        lot_id="r1",
        taxpayer_id="hh1",
        account_id="taxable-1",
        wrapper=Wrapper.TAXABLE,
        symbol="VTI",
        quantity=100,
        cost_basis=9_200,
        trade_date=date(2024, 7, 3),
    )
    wash = apply_wash_sale(
        symbol="VTI",
        quantity_sold=100,
        loss=-1_000,
        sale_date=date(2024, 6, 1),
        taxpayer_id="hh1",
        sold_lot_id="s1",
        purchases=(replacement,),
    )
    assert wash.disallowed == 0.0
    start, end = wash_sale_window(date(2024, 6, 1))
    assert (end - start).days == 60
    assert replacement.trade_date > end


def test_ira_replacement_destroys_the_loss() -> None:
    replacement = Purchase(
        lot_id="ira1",
        taxpayer_id="hh1",
        account_id="ira-1",
        wrapper=Wrapper.IRA,
        symbol="VTI",
        quantity=100,
        cost_basis=9_200,
        trade_date=date(2024, 6, 10),
    )
    lots = [
        _lot("s1", 100, 10_000, date(2023, 1, 3)),
        _lot("ira1", 100, 9_200, date(2024, 6, 10), wrapper=Wrapper.IRA, account_id="ira-1"),
    ]
    remaining, realized = close_lots(
        lots,
        symbol="VTI",
        quantity=100,
        proceeds=9_000,
        closed=date(2024, 6, 1),
        method=LotMethod.SPECIFIC,
        lot_ids=("s1",),
        purchases=(replacement,),
    )
    assert realized[0].ira_destroyed
    assert tax_on_realization(realized[0]) == 0.0
    ira_lot = next(lot for lot in remaining if lot.lot_id == "ira1")
    assert ira_lot.cost_basis == pytest.approx(9_200)


def test_joint_account_purchase_washes_the_sale() -> None:
    replacement = Purchase(
        lot_id="spouse",
        taxpayer_id="hh1",
        account_id="taxable-2",
        wrapper=Wrapper.TAXABLE,
        symbol="VTI",
        quantity=100,
        cost_basis=9_200,
        trade_date=date(2024, 5, 20),
    )
    wash = apply_wash_sale(
        symbol="VTI",
        quantity_sold=100,
        loss=-1_000,
        sale_date=date(2024, 6, 1),
        taxpayer_id="hh1",
        sold_lot_id="s1",
        purchases=(replacement,),
    )
    assert wash.disallowed == pytest.approx(1_000)


def test_december_1256_mark() -> None:
    lots = [
        _lot(
            "spx1",
            1,
            5_000,
            date(2024, 11, 1),
            symbol="SPX_PUT",
            is_1256=True,
        )
    ]
    marked, realizations = mark_1256_year_end(lots, year=2024, prices={"SPX_PUT": 5_500})
    assert realizations[0].gain == pytest.approx(500)
    assert section_1256_tax(realizations[0].gain) == pytest.approx(140)
    assert marked[0].cost_basis == pytest.approx(5_500)
    assert marked[0].acquired == date(2024, 12, 31)


def test_join_foreign_gain_transition_year_to_one_rupee() -> None:
    from decimal import Decimal

    from src.tax import (
        INDIA_FOREIGN_LTCG_RATE,
        INDIA_FOREIGN_STCG_RATE,
        STCG_RATE,
        RealisedLine,
        ThirdJurisdictionRefused,
        carry_through_fy,
        cross_book_set_off,
        dual_india_tax_on_foreign_gain,
        india_tax_on_foreign_gain,
        inr_measured_foreign_gain,
        refuse_third_jurisdiction,
        working_residency_calendar,
    )

    gain = inr_measured_foreign_gain(
        usd_cost=Decimal(10000),
        usd_proceeds=Decimal(12000),
        inr_per_usd_cost=Decimal(80),
        inr_per_usd_proceeds=Decimal(90),
    )
    assert gain == Decimal(280000)
    calendar = working_residency_calendar()
    acquired = date(2026, 1, 1)
    rnor_close = date(2028, 3, 15)
    ror_close = date(2028, 4, 2)
    rnor_tax = india_tax_on_foreign_gain(
        gain,
        acquired=acquired,
        closed=rnor_close,
        receipt_in_india=False,
        calendar=calendar,
    )
    ror_tax = india_tax_on_foreign_gain(
        gain,
        acquired=acquired,
        closed=ror_close,
        receipt_in_india=False,
        calendar=calendar,
    )
    assert rnor_tax == Decimal(0)
    assert ror_tax == Decimal(36400)
    assert ror_tax == gain * INDIA_FOREIGN_LTCG_RATE
    assert ror_tax != gain * Decimal(str(STCG_RATE))
    rnor_report, ror_report = dual_india_tax_on_foreign_gain(
        gain, acquired=acquired, closed=ror_close, receipt_in_india=False
    )
    assert rnor_report == Decimal(0)
    assert ror_report == Decimal(36400)
    short_tax = india_tax_on_foreign_gain(
        gain,
        acquired=date(2027, 6, 1),
        closed=ror_close,
        receipt_in_india=False,
        calendar=calendar,
    )
    assert short_tax == Decimal(87360)
    assert short_tax == gain * INDIA_FOREIGN_STCG_RATE

    lines = (
        RealisedLine("alien", gain, True, ror_close, other_asset=True),
        RealisedLine("india", Decimal(-100000), False, ror_close, other_asset=False),
    )
    with_set = cross_book_set_off(lines, calendar=calendar, cross_book=True)
    without = cross_book_set_off(lines, calendar=calendar, cross_book=False)
    assert without.tax == Decimal(36400)
    assert with_set.tax == Decimal(23400)
    assert with_set.value_inr == Decimal(13000)
    assert not with_set.g5_applied
    pre_cliff = (
        RealisedLine("alien", gain, True, rnor_close, other_asset=True),
        RealisedLine("india", Decimal(-100000), False, rnor_close, other_asset=False),
    )
    assert cross_book_set_off(pre_cliff, calendar=calendar).value_inr == Decimal(0)

    carry_lines = (RealisedLine("alien", Decimal(-50000), True, ror_close),)
    carried = cross_book_set_off(carry_lines, calendar=calendar)
    assert carried.tax == Decimal(0)
    assert carried.carried_ltcl == Decimal(50000)
    assert carried.carry_through_fy == "2036-37"
    assert carry_through_fy(ror_close) == "2036-37"
    with pytest.raises(ThirdJurisdictionRefused):
        refuse_third_jurisdiction(("IN", "US", "IE"))

