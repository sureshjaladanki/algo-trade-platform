"""L1: Book L ledger arithmetic traces to costs and tax."""

from datetime import date
from decimal import Decimal

from src.books.ledger import (
    DESIGN_CAPITAL,
    KILL_BPS,
    Lot,
    etf_vs_constituents,
    etf_vs_index_fund,
    realisation_schedule,
    routing_saving,
    schedule_delta_bps,
    tax_schedule_delta,
)
from src.tax import long_term_holding, ltcg, stcg


def test_tax_delta_matches_blueprint_41990() -> None:
    delta = tax_schedule_delta(DESIGN_CAPITAL)
    assert abs(delta - Decimal("41990.00")) <= Decimal(100)
    assert delta / DESIGN_CAPITAL * Decimal(10000) == Decimal("83.98")
    gain = DESIGN_CAPITAL * Decimal("0.60") * Decimal("0.11")
    assert delta == stcg(gain) - ltcg(gain, Decimal(0))


def test_routing_saving_matches_blueprint_5970() -> None:
    saving = routing_saving(DESIGN_CAPITAL * Decimal("0.60"))
    assert abs(saving - Decimal("5970.00")) <= Decimal(100)


def test_full_year_realisation_tax_delta() -> None:
    gain = DESIGN_CAPITAL * Decimal("0.11")
    assert stcg(gain) - ltcg(gain, Decimal(0)) == Decimal("59150.00")


def test_schedule_delta_clears_50_bps_kill() -> None:
    bps = schedule_delta_bps(DESIGN_CAPITAL)
    assert bps >= KILL_BPS


def test_etf_vs_constituents_flips_when_spread_exceeds_stt_gap() -> None:
    notional = Decimal(100000)
    tight = etf_vs_constituents(notional, Decimal(11))
    wide = etf_vs_constituents(notional, Decimal(20))
    assert tight.venue == "etf"
    assert wide.venue == "constituents"
    assert wide.stt_gap_bps < Decimal(20)
    assert wide.stt_gap_bps > Decimal(19)


def test_etf_vs_index_fund_crossover_and_four_turns() -> None:
    choice = etf_vs_index_fund(
        capital=DESIGN_CAPITAL,
        annual_turns=Decimal(4),
        ter_etf=Decimal("0.0004"),
        ter_fund=Decimal("0.0004"),
        spread_bps=Decimal(11),
        exit_load=Decimal("0.01"),
    )
    assert choice.crossover_turns == Decimal(0)
    assert choice.vehicle == "index_fund"
    assert choice.fund_drag_bps < choice.etf_drag_bps


def test_realisation_schedule_fifo_and_exemption() -> None:
    lots = [
        Lot(
            symbol="RELIANCE",
            quantity=Decimal(100),
            acquired=date(2025, 1, 1),
            cost_per_share=Decimal(1000),
            price=Decimal(1100),
        ),
        Lot(
            symbol="RELIANCE",
            quantity=Decimal(100),
            acquired=date(2026, 6, 1),
            cost_per_share=Decimal(1000),
            price=Decimal(1100),
        ),
        Lot(
            symbol="TCS",
            quantity=Decimal(50),
            acquired=date(2025, 1, 1),
            cost_per_share=Decimal(2000),
            price=Decimal(2200),
        ),
    ]
    as_of = date(2026, 9, 5)
    assert long_term_holding(date(2025, 1, 1), as_of)
    assert not long_term_holding(date(2026, 6, 1), as_of)
    total = Decimal(100) * Decimal(1100) * 2 + Decimal(50) * Decimal(2200)
    rel_w = Decimal(110000) / total
    tcs_w = Decimal(110000) / total
    schedule = realisation_schedule(lots, {"RELIANCE": rel_w, "TCS": tcs_w}, as_of)
    assert len(schedule.sells) == 1
    sell = schedule.sells[0]
    assert sell.acquired == date(2025, 1, 1)
    assert sell.long_term is True
    assert sell.gain == Decimal(10000)
    assert sell.tax == ltcg(Decimal(10000), Decimal(0))
    assert sell.tax == Decimal("0.00")
