"""GL-H1: household reproduces both desks; clocks do not mix."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src import household
from src.books.ledger import Lot as IndiaLot
from src.books.step_up import STEP_UP_HURDLE_BPS, score_lots
from src.books.step_up import Lot as StepLot
from src.household import (
    RUPEE,
    USD_BOOK_MARK_USD,
    USD_CENT,
    USD_LINE_SYMBOLS,
    VANGUARD_COST_BASIS_PATH,
    VANGUARD_MARK_DATE,
    WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_INR,
    WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_USD,
    WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_WEIGHT,
    WORKING_VWRA_INDIA_LOOKTHROUGH_INR,
    WORKING_VWRA_INDIA_LOOKTHROUGH_SOURCE,
    WORKING_VWRA_INDIA_LOOKTHROUGH_USD,
    WORKING_VWRA_INDIA_LOOKTHROUGH_WEIGHT,
    AlienLot,
    ClockContamination,
    Desk,
    HoldingClock,
    JoinLot,
    fa_line_count,
    from_desks,
    inr_native_rate,
    load_alien_from_vanguard,
    parse_vanguard_cost_basis,
    revalue,
    total_india_exposure,
    usd_rate,
)

AS_OF = date(2026, 9, 14)
VANGUARD_FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "vanguard_cost_basis_sample.csv"
)


def _india_lots() -> list[IndiaLot]:
    return [
        IndiaLot(
            symbol="N50",
            quantity=Decimal(10),
            acquired=date(2025, 4, 1),
            cost_per_share=Decimal(1000),
            price=Decimal(1100),
        ),
        IndiaLot(
            symbol="N50",
            quantity=Decimal(5),
            acquired=date(2026, 1, 2),
            cost_per_share=Decimal(2000),
            price=Decimal(2100),
        ),
    ]


def _alien_lots() -> list[AlienLot]:
    # Planted CSPX+XUSE is a W0-shape counterfactual for FA count, not the live core.
    fx_cost = usd_rate(
        Decimal("86.78"), source="yahoo_usdinr_working", as_of=date(2025, 7, 15)
    )
    fx_mark = usd_rate(
        Decimal("95.69"), source="yahoo_usdinr_working", as_of=date(2026, 9, 11)
    )
    return [
        AlienLot(
            lot_id="al-1",
            symbol="CSPX",
            acquired=date(2025, 7, 15),
            usd_cost=Decimal("100.01"),
            usd_value=Decimal("110.02"),
            fx_cost=fx_cost,
            fx_value=fx_mark,
        ),
        AlienLot(
            lot_id="al-2",
            symbol="XUSE",
            acquired=date(2025, 8, 1),
            usd_cost=Decimal("200.02"),
            usd_value=Decimal("210.03"),
            fx_cost=fx_cost,
            fx_value=fx_mark,
        ),
    ]


def _csus_vxua_lots() -> list[AlienLot]:
    fx_cost = usd_rate(
        Decimal("86.78"), source="yahoo_usdinr_working", as_of=date(2025, 7, 15)
    )
    fx_mark = usd_rate(
        Decimal("95.69"), source="yahoo_usdinr_working", as_of=date(2026, 9, 11)
    )
    return [
        AlienLot(
            lot_id="csus-1",
            symbol="CSUS",
            acquired=date(2025, 7, 15),
            usd_cost=Decimal("600.00"),
            usd_value=Decimal("660.00"),
            fx_cost=fx_cost,
            fx_value=fx_mark,
        ),
        AlienLot(
            lot_id="vxua-1",
            symbol="VXUA",
            acquired=date(2025, 8, 1),
            usd_cost=Decimal("400.00"),
            usd_value=Decimal("440.00"),
            fx_cost=fx_cost,
            fx_value=fx_mark,
        ),
    ]


def test_reproduces_india_to_one_rupee() -> None:
    india = _india_lots()
    ledger = from_desks(india=india, alien=_alien_lots(), as_of=AS_OF)
    assert ledger.india_cost_inr() == Decimal(20000)
    assert ledger.india_value_inr() == Decimal(21500)
    assert abs(ledger.india_cost_inr() - Decimal(20000)) <= RUPEE


def test_reproduces_alien_to_one_cent() -> None:
    alien = _alien_lots()
    ledger = from_desks(india=_india_lots(), alien=alien, as_of=AS_OF)
    assert ledger.alien_cost_usd() == Decimal("300.03")
    assert ledger.alien_value_usd() == Decimal("320.05")
    assert abs(ledger.alien_cost_usd() - Decimal("300.03")) <= USD_CENT


def test_planted_cross_clock_error_is_caught() -> None:
    fx = inr_native_rate(AS_OF)
    with pytest.raises(ClockContamination, match="india_12m"):
        JoinLot(
            lot_id="bad",
            desk=Desk.INDIA,
            symbol="N50",
            acquired=date(2025, 4, 1),
            native_cost=Decimal(1000),
            native_value=Decimal(1100),
            native_currency="INR",
            fx_cost=fx,
            fx_value=fx,
            clock=HoldingClock.FOREIGN_24M,
        )


def test_alien_lot_cannot_use_india_clock() -> None:
    fx = usd_rate(Decimal("95.69"), source="yahoo_usdinr_working", as_of=AS_OF)
    with pytest.raises(ClockContamination, match="foreign_24m"):
        JoinLot(
            lot_id="bad-usd",
            desk=Desk.ALIEN,
            symbol="CSPX",
            acquired=date(2025, 7, 15),
            native_cost=Decimal(100),
            native_value=Decimal(110),
            native_currency="USD",
            fx_cost=fx,
            fx_value=fx,
            clock=HoldingClock.INDIA_12M,
        )


def test_csus_vxua_join_as_alien_usd_line() -> None:
    ledger = from_desks(india=_india_lots(), alien=_csus_vxua_lots(), as_of=AS_OF)
    assert {lot.symbol for lot in ledger.alien_lots()} == {"CSUS", "VXUA"}
    assert all(lot.desk is Desk.ALIEN for lot in ledger.alien_lots())
    assert all(lot.clock is HoldingClock.FOREIGN_24M for lot in ledger.alien_lots())
    assert all(lot.native_currency == "USD" for lot in ledger.alien_lots())
    assert ledger.alien_cost_usd() == Decimal("1000.00")
    assert ledger.alien_value_usd() == Decimal("1100.00")
    assert {lot.symbol for lot in ledger.india_lots()} == {"N50"}
    assert all(lot.desk is Desk.INDIA for lot in ledger.india_lots())
    assert all(lot.clock is HoldingClock.INDIA_12M for lot in ledger.india_lots())
    assert all(lot.native_currency == "INR" for lot in ledger.india_lots())


def test_india_lookthrough_is_not_an_india_desk_lot() -> None:
    ledger = from_desks(india=_india_lots(), alien=_csus_vxua_lots(), as_of=AS_OF)
    exposure = total_india_exposure(ledger)
    assert exposure.india_desk_inr == Decimal(21500)
    assert exposure.usd_line_india_lookthrough_inr == WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_INR
    assert exposure.usd_line_india_lookthrough_inr != Decimal(0)
    assert all(lot.symbol not in USD_LINE_SYMBOLS for lot in ledger.india_lots())
    assert all(lot.symbol != "VXUA" for lot in ledger.india_lots())
    assert all(lot.symbol != "CSUS" for lot in ledger.india_lots())


def test_vxua_tagged_india_12m_is_caught() -> None:
    fx = usd_rate(Decimal("95.69"), source="yahoo_usdinr_working", as_of=AS_OF)
    with pytest.raises(ClockContamination, match="foreign_24m"):
        JoinLot(
            lot_id="bad-vxua-clock",
            desk=Desk.ALIEN,
            symbol="VXUA",
            acquired=date(2025, 8, 1),
            native_cost=Decimal(400),
            native_value=Decimal(440),
            native_currency="USD",
            fx_cost=fx,
            fx_value=fx,
            clock=HoldingClock.INDIA_12M,
        )
    inr = inr_native_rate(AS_OF)
    with pytest.raises(ClockContamination, match="only the Indian book uses the India line"):
        JoinLot(
            lot_id="bad-vxua-desk",
            desk=Desk.INDIA,
            symbol="VXUA",
            acquired=date(2025, 8, 1),
            native_cost=Decimal(400),
            native_value=Decimal(440),
            native_currency="INR",
            fx_cost=inr,
            fx_value=inr,
            clock=HoldingClock.INDIA_12M,
        )


def test_only_indian_book_uses_india_line() -> None:
    inr = inr_native_rate(AS_OF)
    for symbol in sorted(USD_LINE_SYMBOLS):
        with pytest.raises(ClockContamination, match="only the Indian book uses the India line"):
            JoinLot(
                lot_id=f"bad-{symbol.lower()}",
                desk=Desk.INDIA,
                symbol=symbol,
                acquired=date(2025, 4, 1),
                native_cost=Decimal(1000),
                native_value=Decimal(1100),
                native_currency="INR",
                fx_cost=inr,
                fx_value=inr,
                clock=HoldingClock.INDIA_12M,
            )


def test_fa_register_and_india_lookthrough_are_populated() -> None:
    ledger = from_desks(india=_india_lots(), alien=_alien_lots(), as_of=AS_OF)
    assert fa_line_count(ledger) == 2
    exposure = total_india_exposure(ledger)
    assert exposure.tagged_working
    assert exposure.usd_line_india_lookthrough_weight == WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_WEIGHT
    assert exposure.usd_line_india_lookthrough_usd == WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_USD
    assert exposure.usd_line_india_lookthrough_inr == WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_INR
    assert exposure.total_inr == Decimal(21500) + WORKING_CSUS_VXUA_INDIA_LOOKTHROUGH_INR
    assert exposure.india_desk_inr == ledger.india_value_inr()
    assert "working" in exposure.source
    assert "CSUS+VXUA" in exposure.source
    assert "look-through" in exposure.source
    assert "not an India-desk lot" in exposure.source
    assert "not a tax conclusion" in exposure.source


def test_cspx_xuse_lookthrough_is_zero_counterfactual() -> None:
    ledger = from_desks(india=_india_lots(), alien=_alien_lots(), as_of=AS_OF)
    exposure = total_india_exposure(
        ledger,
        usd_line_india_lookthrough_usd=Decimal(0),
        usd_line_india_lookthrough_inr=Decimal(0),
        usd_line_india_lookthrough_weight=Decimal(0),
        source="CSPX+XUSE counterfactual; USD-line India look-through 0; not the live default",
    )
    assert exposure.usd_line_india_lookthrough_usd == Decimal(0)
    assert exposure.usd_line_india_lookthrough_inr == Decimal(0)
    assert exposure.usd_line_india_lookthrough_weight == Decimal(0)
    assert exposure.total_inr == Decimal(21500)


def test_vwra_lookthrough_is_unchosen_substitute() -> None:
    ledger = from_desks(india=_india_lots(), alien=_alien_lots(), as_of=AS_OF)
    exposure = total_india_exposure(
        ledger,
        usd_line_india_lookthrough_usd=WORKING_VWRA_INDIA_LOOKTHROUGH_USD,
        usd_line_india_lookthrough_inr=WORKING_VWRA_INDIA_LOOKTHROUGH_INR,
        usd_line_india_lookthrough_weight=WORKING_VWRA_INDIA_LOOKTHROUGH_WEIGHT,
        source=WORKING_VWRA_INDIA_LOOKTHROUGH_SOURCE,
    )
    assert exposure.usd_line_india_lookthrough_usd == Decimal(3900)
    assert exposure.total_inr == Decimal(21500) + WORKING_VWRA_INDIA_LOOKTHROUGH_INR
    assert "unchosen substitute" in exposure.source


def test_fx_basis_swap_is_a_rerun() -> None:
    ledger = from_desks(india=_india_lots(), alien=_alien_lots(), as_of=AS_OF)
    old = ledger.alien_lots()[0]
    new_fx = usd_rate(
        Decimal(100), source="rule_115_tt_buying", as_of=date(2026, 9, 14)
    )
    rerun = revalue(old, fx_cost=new_fx, fx_value=new_fx)
    assert rerun.fx_cost.source == "rule_115_tt_buying"
    assert rerun.value_inr != old.value_inr


def test_household_has_no_transfer_primitive() -> None:
    assert not hasattr(household, "transfer")
    assert "transfer" not in dir(household.HouseholdLedger)


def test_vanguard_fixture_reproduces_usd_to_one_cent() -> None:
    text = VANGUARD_FIXTURE.read_text(encoding="utf-8")
    parsed = parse_vanguard_cost_basis(text)
    assert len(parsed) == 5
    assert {lot.symbol for lot in parsed} == {"VTI", "VXUS", "VOO", "VTV"}
    assert parsed[0].quantity == Decimal("2.0000")
    assert [lot.lot_id for lot in parsed] == [
        "vti-2025-07-28-0",
        "vti-2026-03-13-0",
        "vxus-2026-03-13-0",
        "voo-2026-06-12-0",
        "vtv-2026-06-23-0",
    ]
    alien = load_alien_from_vanguard(VANGUARD_FIXTURE)
    ledger = from_desks(india=_india_lots(), alien=alien, as_of=AS_OF)
    assert ledger.alien_cost_usd() == Decimal("1510.00")
    assert ledger.alien_value_usd() == Decimal("1605.75")
    assert abs(ledger.alien_cost_usd() - Decimal("1510.00")) <= USD_CENT
    assert abs(ledger.alien_value_usd() - Decimal("1605.75")) <= USD_CENT
    assert all(lot.fx_value.source == "yahoo_usdinr_working" for lot in alien)
    assert all(lot.fx_value.as_of == VANGUARD_MARK_DATE for lot in alien)
    assert not hasattr(parsed[0], "account")


def test_vanguard_parser_does_not_write_lots(tmp_path: Path) -> None:
    dest = tmp_path / "costbasis.csv"
    dest.write_text(VANGUARD_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    before = dest.read_text(encoding="utf-8")
    load_alien_from_vanguard(dest)
    assert dest.read_text(encoding="utf-8") == before
    assert not hasattr(household, "write_vanguard_cost_basis")


@pytest.mark.skipif(
    not VANGUARD_COST_BASIS_PATH.is_file(),
    reason="private Vanguard cost-basis download absent",
)
def test_private_vanguard_export_reproduces_usd_mark() -> None:
    alien = load_alien_from_vanguard(VANGUARD_COST_BASIS_PATH)
    ledger = from_desks(india=(), alien=alien, as_of=AS_OF)
    assert len(alien) == 38
    assert ledger.alien_cost_usd() == Decimal("307061.36")
    assert ledger.alien_value_usd() == USD_BOOK_MARK_USD
    assert ledger.alien_value_usd() == Decimal("354097.28")
    assert {lot.symbol for lot in alien} == {"VTI", "VXUS", "VOO", "VTV"}
    us = sum(
        (lot.native_value for lot in ledger.alien_lots() if lot.symbol in {"VTI", "VOO", "VTV"}),
        Decimal(0),
    )
    intl = sum(
        (lot.native_value for lot in ledger.alien_lots() if lot.symbol == "VXUS"),
        Decimal(0),
    )
    assert us == Decimal("212505.26")
    assert intl == Decimal("141592.02")
    fx = float(alien[0].fx_value.inr_per_unit)
    score = score_lots(
        tuple(
            StepLot(
                acquisition_date=lot.acquired,
                usd_cost=float(lot.usd_cost),
                usd_value=float(lot.usd_value),
                inr_per_usd_acquire=fx,
                inr_per_usd_now=fx,
            )
            for lot in alien
        ),
        cliff_date=date(2028, 3, 31),
        source="real",
    )
    assert score.step_up_bps_of_capital >= STEP_UP_HURDLE_BPS
    assert score.n_lots == 38
