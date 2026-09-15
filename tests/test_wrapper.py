"""W0 wrapper arithmetic against published TERs/yields and IRC 2001 estate tax."""

import pytest

from src.books.wrapper import (
    CSPX,
    CSUS,
    VTI,
    VTI_SEC_YIELD,
    VWRA,
    VXUA,
    VXUS,
    WRAPPER_SAVING_HURDLE_BPS,
    XUSE,
    dividend_as_ltcg_bps,
    estate_table,
    irish_pair_costs,
    lse_dealing_amortised_bps,
    measured_pair,
    ror_cliff_table,
    us_listed_costs,
    us_nra_estate_tax,
    vwra_costs,
    w0_passes,
    zero_situs_path_documented,
)


def test_published_ters_locked() -> None:
    assert VTI.ter == pytest.approx(0.0003)
    assert VXUS.ter == pytest.approx(0.0005)
    assert CSPX.ter == pytest.approx(0.0007)
    assert XUSE.ter == pytest.approx(0.0015)
    assert VWRA.ter == pytest.approx(0.0014)


def test_published_yield_and_irish_zero_situs() -> None:
    assert VTI_SEC_YIELD == pytest.approx(0.0102)
    assert VTI.situs_us and VXUS.situs_us
    assert not CSPX.situs_us and not XUSE.situs_us and not VWRA.situs_us
    assert CSPX.accumulation and XUSE.accumulation and VWRA.accumulation
    assert CSPX.domicile == XUSE.domicile == VWRA.domicile == "IE"
    assert zero_situs_path_documented()


def test_withholding_as_fraction_of_gross_income() -> None:
    assert VTI.withheld_of_gross_income == pytest.approx(0.25)
    assert VXUS.withheld_of_gross_income == pytest.approx(0.25)
    assert CSPX.withheld_of_gross_income == pytest.approx(0.15)
    assert XUSE.withheld_of_gross_income == pytest.approx(0.0)


def test_us_listed_blended_ter_is_36_bps() -> None:
    naive = us_listed_costs(us_yield=0.0102, exus_yield=0.0276)
    assert naive.blended_ter_bps == pytest.approx(3.6)


def test_irish_pair_blended_ter_from_published() -> None:
    irish = irish_pair_costs(us_yield=0.0102)
    assert irish.blended_ter_bps == pytest.approx(9.4)
    assert irish.exus_investor_wht_bps == pytest.approx(0.0)


def test_exus_double_withholding_is_the_largest_us_listed_leak() -> None:
    naive = us_listed_costs(us_yield=0.0102, exus_yield=0.0276)
    irish = irish_pair_costs(us_yield=0.0102)
    assert naive.exus_investor_wht_bps == pytest.approx(20.7)
    assert naive.exus_investor_wht_bps > naive.us_leg_wht_bps
    assert irish.exus_investor_wht_bps == pytest.approx(0.0)


def test_measured_saving_clears_n9() -> None:
    naive, irish, saving = measured_pair()
    assert saving == pytest.approx(naive.total_bps - irish.total_bps)
    assert saving >= WRAPPER_SAVING_HURDLE_BPS
    assert not irish.situs_on_core
    assert irish.rnor_after_tax == pytest.approx(irish.ror_after_tax)
    assert naive.ror_after_tax < naive.rnor_after_tax
    assert naive.ror_governs_after_tax == naive.ror_after_tax
    assert w0_passes()


def test_working_yields_reproduce_blueprint_shape() -> None:
    naive = us_listed_costs(us_yield=0.013, exus_yield=0.029)
    irish = irish_pair_costs(us_yield=0.013)
    assert naive.blended_ter_bps == pytest.approx(3.6)
    assert naive.us_leg_wht_bps == pytest.approx(22.75)
    assert naive.exus_investor_wht_bps == pytest.approx(21.75)
    assert naive.total_bps == pytest.approx(48.1)
    assert irish.us_leg_wht_bps == pytest.approx(13.65)
    assert irish.exus_investor_wht_bps == pytest.approx(0.0)
    saving = naive.total_bps - irish.total_bps
    assert saving >= WRAPPER_SAVING_HURDLE_BPS


def test_vwra_also_clears_hurdle_and_is_zero_situs() -> None:
    naive, _irish, _saving = measured_pair()
    vwra = vwra_costs(us_yield=0.0102)
    assert not vwra.situs_on_core
    assert naive.total_bps - vwra.total_bps >= WRAPPER_SAVING_HURDLE_BPS


def test_estate_table_irc_2001_minus_nra_credit() -> None:
    assert us_nra_estate_tax(60_000.0) == pytest.approx(0.0)
    assert us_nra_estate_tax(100_000.0) == pytest.approx(10_800.0)
    assert us_nra_estate_tax(200_000.0) == pytest.approx(41_800.0)
    assert us_nra_estate_tax(500_000.0) == pytest.approx(142_800.0)
    assert us_nra_estate_tax(1_000_000.0) == pytest.approx(332_800.0)
    rows = estate_table()
    assert [row.situs_usd for row in rows] == [60_000.0, 100_000.0, 200_000.0, 500_000.0, 1_000_000.0]
    assert rows[3].pct_of_situs == pytest.approx(0.2856)
    irish_core_tax = us_nra_estate_tax(0.0)
    assert irish_core_tax == pytest.approx(0.0)


def test_ror_cliff_distributing_vs_accumulating() -> None:
    rows = ror_cliff_table(us_yield=0.0102, exus_yield=0.0276)
    distributing, accumulating = rows
    assert distributing.form_67 is True
    assert accumulating.form_67 is False
    assert distributing.annual_india_dividend_tax_bps > 0
    assert accumulating.annual_india_dividend_tax_bps == pytest.approx(0.0)
    assert accumulating.dividend_as_ltcg_bps == pytest.approx(
        dividend_as_ltcg_bps(us_yield=0.0102, exus_yield=0.0276)
    )
    working_bps = ror_cliff_table(us_yield=0.013, exus_yield=0.029)[0].annual_india_dividend_tax_bps
    assert working_bps == pytest.approx(11.036)


def test_lse_dealing_amortised_under_one_bp_per_year() -> None:
    small = lse_dealing_amortised_bps(clip_usd=25_000.0)
    large = lse_dealing_amortised_bps(clip_usd=100_000.0)
    book = lse_dealing_amortised_bps(clip_usd=500_000.0)
    assert small == pytest.approx(11.5 / 20.0)
    assert large == pytest.approx(6.0 / 20.0)
    assert book == pytest.approx(large)
    assert small < 1.0
    assert large < 1.0


def test_csus_vxua_are_irish_usd_line_facts_not_w0() -> None:
    assert CSUS.isin == "IE00B52SFT06"
    assert VXUA.isin == "IE0009A5ADV9"
    assert not CSUS.situs_us and not VXUA.situs_us
    assert CSUS.accumulation and VXUA.accumulation
    assert CSUS.domicile == VXUA.domicile == "IE"
    assert CSUS.ter == pytest.approx(0.0003)
    assert VXUA.ter == pytest.approx(0.0012)
    irish = irish_pair_costs(us_yield=0.0102)
    assert irish.label == "Irish physical acc CSPX+XUSE"
    assert irish.blended_ter_bps == pytest.approx(9.4)
