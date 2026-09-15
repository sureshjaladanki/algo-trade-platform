"""Book J — measured cross-book set-off value and realisation ordering.

GL1 measured the working value below 25 bps of combined capital. The book is
closed. This module keeps the folded sequencing rule for India Book L and
alien Book R. It is not a live book and emits no orders. household is kept.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.household import DualNumber, dual
from src.tax import (
    INDIA_FOREIGN_LTCG_RATE,
    INDIA_FOREIGN_STCG_RATE,
    RealisedLine,
    ResidencyCalendar,
    cross_book_set_off,
    prefer_realising_inr_book,
    rnor_reporting_calendar,
    ror_realisation_tax,
    ror_reporting_calendar,
    working_residency_calendar,
)

# GS3: 25 bps of ≈ ₹3.89 crore combined (₹3.39 crore USD book + ₹50 lakh India).
GS3_COMBINED_CAPITAL_INR = Decimal(38900000)
GS3_KILL_INR = Decimal(97000)
KILL_BPS = Decimal(25)
# Analysis working volume: sheltering ₹5 lakh of gain (G27).
WORKING_SHELTER_INR = Decimal(500000)
WORKING_FY_ROR = date(2028, 6, 15)


def realisation_order() -> tuple[str, ...]:
    """Realise the INR book first. Sequencing, not a hedge and not a reallocation."""
    return prefer_realising_inr_book()


def usd_book_costs_more_per_unit() -> bool:
    """Same native 10% gain: USD INR-measured gain includes FX accretion."""
    india = ror_realisation_tax(
        desk="india",
        native_cost=Decimal(100000),
        native_proceeds=Decimal(110000),
        inr_per_unit_cost=Decimal(1),
        inr_per_unit_proceeds=Decimal(1),
        long_term=True,
    )
    alien = ror_realisation_tax(
        desk="alien",
        native_cost=Decimal(1000),
        native_proceeds=Decimal(1100),
        inr_per_unit_cost=Decimal(80),
        inr_per_unit_proceeds=Decimal(90),
        long_term=True,
    )
    return alien > india


def working_lines(*, closed: date = WORKING_FY_ROR) -> tuple[RealisedLine, ...]:
    return (
        RealisedLine(
            desk="alien",
            gain_inr=WORKING_SHELTER_INR,
            long_term=True,
            closed=closed,
            other_asset=True,
        ),
        RealisedLine(
            desk="india",
            gain_inr=-WORKING_SHELTER_INR,
            long_term=False,
            closed=closed,
            other_asset=False,
        ),
    )


def measure_set_off(
    lines: tuple[RealisedLine, ...] | None = None,
    *,
    calendar: ResidencyCalendar | None = None,
) -> Decimal:
    used = lines if lines is not None else working_lines()
    cal = calendar if calendar is not None else working_residency_calendar()
    result = cross_book_set_off(used, calendar=cal, cross_book=True)
    return result.value_inr


def book_j_value() -> DualNumber:
    rnor = measure_set_off(working_lines(), calendar=rnor_reporting_calendar())
    ror = measure_set_off(working_lines(), calendar=ror_reporting_calendar())
    return dual("book_j_set_off", rnor=rnor, ror=ror)


def book_j_bps(value_inr: Decimal, *, capital: Decimal = GS3_COMBINED_CAPITAL_INR) -> Decimal:
    return (value_inr / capital) * Decimal(10000)


def book_j_passes(value_inr: Decimal, *, kill: Decimal = GS3_KILL_INR) -> bool:
    return value_inr >= kill


def ltcg_working_value() -> Decimal:
    return WORKING_SHELTER_INR * INDIA_FOREIGN_LTCG_RATE


def stcg_sensitivity_value() -> Decimal:
    return WORKING_SHELTER_INR * INDIA_FOREIGN_STCG_RATE
