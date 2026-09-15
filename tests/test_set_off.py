"""Book J measurement against the 25 bps / ₹97,000 kill, and the folded order rule."""

from decimal import Decimal

from src.books import ledger, step_up
from src.books.set_off import (
    GS3_KILL_INR,
    WORKING_SHELTER_INR,
    book_j_bps,
    book_j_passes,
    book_j_value,
    ltcg_working_value,
    realisation_order,
    stcg_sensitivity_value,
    usd_book_costs_more_per_unit,
)
from src.tax import INDIA_FOREIGN_LTCG_RATE, prefer_realising_inr_book


def test_realisation_order_is_inr_then_usd() -> None:
    assert realisation_order() == ("india", "alien")
    assert ledger.realisation_order() == realisation_order()
    assert step_up.realisation_order() == realisation_order()
    assert prefer_realising_inr_book() == realisation_order()
    assert usd_book_costs_more_per_unit()


def test_book_j_rnor_is_zero_ror_governs() -> None:
    numbers = book_j_value()
    assert numbers.rnor == Decimal(0)
    assert numbers.ror == WORKING_SHELTER_INR * INDIA_FOREIGN_LTCG_RATE
    assert numbers.ror == Decimal(65000)
    assert numbers.governs == numbers.ror
    assert numbers.ror == ltcg_working_value()


def test_book_j_is_below_kill_at_ror_ltcg() -> None:
    value = book_j_value().governs
    assert value == Decimal(65000)
    assert value < GS3_KILL_INR
    assert not book_j_passes(value)
    bps = book_j_bps(value)
    assert Decimal(16) < bps < Decimal(18)
    # STCG 31.2% sensitivity is above the line; it does not govern.
    assert stcg_sensitivity_value() == Decimal(156000)
    assert stcg_sensitivity_value() > GS3_KILL_INR
