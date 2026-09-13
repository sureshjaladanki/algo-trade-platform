"""Book R — INR-measured embedded-gain arithmetic for the pre-cliff step-up.

R0 scores a household lot ledger. The plan's 200k/400k/62/92 book is an
illustration of this identity, not this desk's Exit. Exit requires the
investor's own lots; those are not in the repo and are not invented.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REAL_LOTS_PATH = REPO_ROOT / "data" / "private" / "r0-lots.csv"

# N9 Book R minimum (alien plan). Accounting identity, not a statistical peek.
STEP_UP_HURDLE_BPS = 100.0
INDIA_LTCG_RATE = 0.13
INDIA_STCG_RATE = 0.312
LONG_HOLD_MONTHS = 24

# Plan R0 working illustration. Replaced by real lots when they exist.
ILLUSTRATION_USD_COST = 200_000.0
ILLUSTRATION_USD_VALUE = 400_000.0
ILLUSTRATION_INR_PER_USD_ACQUIRE = 62.0
ILLUSTRATION_INR_PER_USD_NOW = 92.0


@dataclass(frozen=True)
class Lot:
    acquisition_date: date
    usd_cost: float
    usd_value: float
    inr_per_usd_acquire: float
    inr_per_usd_now: float


@dataclass(frozen=True)
class StepUpScore:
    usd_cost: float
    usd_value: float
    usd_unrealised: float
    inr_cost: float
    inr_value: float
    inr_unrealised: float
    fx_accretion_inr: float
    tax_if_sold_after_cliff: float
    tax_stcg_short_lots: float
    step_up_bps_of_capital: float
    n_lots: int
    source: str


def bps_of_capital(*, tax_inr: float, inr_value: float) -> float:
    return (tax_inr / inr_value) * 10_000.0


def months_held(*, acquired: date, as_of: date) -> int:
    return (as_of.year - acquired.year) * 12 + (as_of.month - acquired.month)


def score_lots(lots: tuple[Lot, ...], *, cliff_date: date, source: str) -> StepUpScore:
    if not lots:
        raise ValueError("lot ledger is empty")
    usd_cost = sum(lot.usd_cost for lot in lots)
    usd_value = sum(lot.usd_value for lot in lots)
    inr_cost = sum(lot.usd_cost * lot.inr_per_usd_acquire for lot in lots)
    inr_value = sum(lot.usd_value * lot.inr_per_usd_now for lot in lots)
    fx_accretion = sum(
        lot.usd_cost * (lot.inr_per_usd_now - lot.inr_per_usd_acquire) for lot in lots
    )
    inr_unrealised = inr_value - inr_cost
    tax_ltcg = 0.0
    tax_stcg = 0.0
    for lot in lots:
        lot_inr_gain = lot.usd_value * lot.inr_per_usd_now - lot.usd_cost * lot.inr_per_usd_acquire
        if months_held(acquired=lot.acquisition_date, as_of=cliff_date) < LONG_HOLD_MONTHS:
            tax_stcg += INDIA_STCG_RATE * lot_inr_gain
        else:
            tax_ltcg += INDIA_LTCG_RATE * lot_inr_gain
    tax_after_cliff = tax_ltcg + tax_stcg
    return StepUpScore(
        usd_cost=usd_cost,
        usd_value=usd_value,
        usd_unrealised=usd_value - usd_cost,
        inr_cost=inr_cost,
        inr_value=inr_value,
        inr_unrealised=inr_unrealised,
        fx_accretion_inr=fx_accretion,
        tax_if_sold_after_cliff=tax_after_cliff,
        tax_stcg_short_lots=tax_stcg,
        step_up_bps_of_capital=bps_of_capital(tax_inr=tax_after_cliff, inr_value=inr_value),
        n_lots=len(lots),
        source=source,
    )


def illustration_lot() -> Lot:
    return Lot(
        acquisition_date=date(2016, 1, 15),
        usd_cost=ILLUSTRATION_USD_COST,
        usd_value=ILLUSTRATION_USD_VALUE,
        inr_per_usd_acquire=ILLUSTRATION_INR_PER_USD_ACQUIRE,
        inr_per_usd_now=ILLUSTRATION_INR_PER_USD_NOW,
    )


def illustration_score(*, cliff_date: date = date(2028, 3, 31)) -> StepUpScore:
    return score_lots((illustration_lot(),), cliff_date=cliff_date, source="illustration")


def load_lots(path: Path) -> tuple[Lot, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = tuple(csv.DictReader(handle))
    lots = tuple(
        Lot(
            acquisition_date=date.fromisoformat(row["acquisition_date"]),
            usd_cost=float(row["usd_cost"]),
            usd_value=float(row["usd_value"]),
            inr_per_usd_acquire=float(row["inr_per_usd_acquire"]),
            inr_per_usd_now=float(row["inr_per_usd_now"]),
        )
        for row in rows
    )
    if not lots:
        raise ValueError(f"{path} has a header but no lots")
    return lots


def real_lots_present() -> bool:
    return REAL_LOTS_PATH.is_file()


def r0_passes(score: StepUpScore) -> bool:
    return score.source == "real" and score.step_up_bps_of_capital >= STEP_UP_HURDLE_BPS
