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
