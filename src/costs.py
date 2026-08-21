"""Round-trip cost model. Every backtest imports this; none re-implements it.

Working constants follow Blueprint §0.2 until fill calibration replaces them.
Section 31 and FINRA TAF reset on a published schedule; the values here are
the plan's working numbers, not a live feed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class ProductBucket(StrEnum):
    LIQUID_ETF = "liquid_etf"
    LARGE_CAP = "large_cap"
    MID_CAP = "mid_cap"
    SMALL_CAP = "small_cap"
    MES = "mes"
    ES = "es"
    SPX_ATM_30_45 = "spx_atm_30_45"
    XSP_ATM_30_45 = "xsp_atm_30_45"
    SPX_10D_WING = "spx_10d_wing"
    SPY_OPTION_ATM = "spy_option_atm"


# --- working fee schedule (Blueprint §0.2) ---
SECTION_31_PER_MILLION = 27.80
FINRA_TAF_PER_SHARE = 0.000166
FINRA_TAF_CAP = 8.30
OCC_PER_CONTRACT = 0.02
BROKER_PER_CONTRACT = 0.65
ORF_INDEX_PER_CONTRACT = 0.08
TAF_OPTIONS_PER_CONTRACT = 0.00279

MES_TICK_USD = 1.25
MES_FEES_ROUND_TURN_USD = 1.20
MES_NOTIONAL_USD = 32_000.0
ES_TICK_USD = 12.50
ES_FEES_ROUND_TURN_USD = 4.50
ES_NOTIONAL_USD = 320_000.0

EQUITY_CALIBRATION_TOLERANCE_BPS = 3.0
OPTION_CALIBRATION_TOLERANCE_PCT = 0.3


class CostUnit(StrEnum):
    BPS = "bps"
    PCT_PREMIUM = "pct_premium"


@dataclass(frozen=True)
class BucketSpec:
    quoted_low: float
    quoted_high: float
    fees_round_trip: float
    all_in_low: float
    all_in_high: float
    unit: CostUnit
    kind: Literal["equity", "future", "option"]


# Blueprint §0.2 table. quoted_* is the spread the desk pays (bps or % of premium
# per side for options). all_in_* is the working round-trip the backtest uses.
WORKING_TABLE: dict[ProductBucket, BucketSpec] = {
    ProductBucket.LIQUID_ETF: BucketSpec(1.0, 1.5, 0.4, 1.2, 2.0, CostUnit.BPS, "equity"),
    ProductBucket.LARGE_CAP: BucketSpec(0.5, 2.0, 0.5, 1.5, 3.0, CostUnit.BPS, "equity"),
    ProductBucket.MID_CAP: BucketSpec(5.0, 15.0, 0.6, 10.0, 25.0, CostUnit.BPS, "equity"),
    ProductBucket.SMALL_CAP: BucketSpec(20.0, 60.0, 0.8, 45.0, 120.0, CostUnit.BPS, "equity"),
    ProductBucket.MES: BucketSpec(0.39, 0.39, 0.375, 0.6, 0.9, CostUnit.BPS, "future"),
    ProductBucket.ES: BucketSpec(0.39, 0.39, 0.141, 0.5, 0.7, CostUnit.BPS, "future"),
    ProductBucket.SPX_ATM_30_45: BucketSpec(0.3, 0.6, 0.0, 1.0, 2.0, CostUnit.PCT_PREMIUM, "option"),
    ProductBucket.XSP_ATM_30_45: BucketSpec(2.0, 4.0, 0.0, 5.0, 9.0, CostUnit.PCT_PREMIUM, "option"),
    ProductBucket.SPX_10D_WING: BucketSpec(5.0, 15.0, 0.0, 12.0, 30.0, CostUnit.PCT_PREMIUM, "option"),
    ProductBucket.SPY_OPTION_ATM: BucketSpec(0.5, 1.0, 0.0, 1.5, 3.0, CostUnit.PCT_PREMIUM, "option"),
}


@dataclass(frozen=True)
class RoundTrip:
    value: float
    unit: CostUnit
    bucket: ProductBucket


class BorrowProhibited(Exception):
    """Short stock is closed in v1. Hedge with MES."""


def section_31_fee(sell_proceeds_usd: float) -> float:
    if sell_proceeds_usd < 0:
        raise ValueError("sell_proceeds_usd must be >= 0")
    return sell_proceeds_usd * SECTION_31_PER_MILLION / 1_000_000.0


def finra_taf(shares_sold: float) -> float:
    if shares_sold < 0:
        raise ValueError("shares_sold must be >= 0")
    return min(shares_sold * FINRA_TAF_PER_SHARE, FINRA_TAF_CAP)


def occ_fee(contracts: int) -> float:
    if contracts < 0:
        raise ValueError("contracts must be >= 0")
    return contracts * OCC_PER_CONTRACT


def exchange_orf(contracts: int) -> float:
    if contracts < 0:
        raise ValueError("contracts must be >= 0")
    return contracts * ORF_INDEX_PER_CONTRACT


def broker_per_contract_fee(contracts: int) -> float:
    if contracts < 0:
        raise ValueError("contracts must be >= 0")
    return contracts * BROKER_PER_CONTRACT


def equity_sell_fees_usd(*, shares: float, sell_price: float) -> float:
    return section_31_fee(shares * sell_price) + finra_taf(shares)


def equity_sell_fees_bps(*, shares: float, sell_price: float) -> float:
    notional = shares * sell_price
    if notional <= 0:
        raise ValueError("notional must be > 0")
    return 1e4 * equity_sell_fees_usd(shares=shares, sell_price=sell_price) / notional


def option_fees_round_trip_usd(contracts: int) -> float:
    """Both sides: broker + OCC + ORF. TAF is sell-side only and is inside the ~$ figure."""
    per_side = (
        broker_per_contract_fee(contracts)
        + occ_fee(contracts)
        + exchange_orf(contracts)
    )
    sell_taf = contracts * TAF_OPTIONS_PER_CONTRACT
    return 2.0 * per_side + sell_taf


def futures_round_turn_usd(bucket: ProductBucket) -> float:
    if bucket is ProductBucket.MES:
        return MES_TICK_USD + MES_FEES_ROUND_TURN_USD
    if bucket is ProductBucket.ES:
        return ES_TICK_USD + ES_FEES_ROUND_TURN_USD
    raise ValueError(f"{bucket} is not a futures bucket")


def futures_round_turn_bps(bucket: ProductBucket) -> float:
    if bucket is ProductBucket.MES:
        return 1e4 * futures_round_turn_usd(bucket) / MES_NOTIONAL_USD
    if bucket is ProductBucket.ES:
        return 1e4 * futures_round_turn_usd(bucket) / ES_NOTIONAL_USD
    raise ValueError(f"{bucket} is not a futures bucket")


def working_all_in(bucket: ProductBucket) -> float:
    """Midpoint of the Blueprint all-in range. Backtests use this until calibration."""
    spec = WORKING_TABLE[bucket]
    return (spec.all_in_low + spec.all_in_high) / 2.0


def round_trip(bucket: ProductBucket) -> RoundTrip:
    spec = WORKING_TABLE[bucket]
    if spec.kind == "future":
        return RoundTrip(futures_round_turn_bps(bucket), CostUnit.BPS, bucket)
    return RoundTrip(working_all_in(bucket), spec.unit, bucket)


def round_trip_bps(bucket: ProductBucket) -> float:
    result = round_trip(bucket)
    if result.unit is not CostUnit.BPS:
        raise ValueError(f"{bucket} cost is {result.unit}, not bps")
    return result.value


def round_trip_pct_of_premium(bucket: ProductBucket) -> float:
    result = round_trip(bucket)
    if result.unit is not CostUnit.PCT_PREMIUM:
        raise ValueError(f"{bucket} cost is {result.unit}, not pct_premium")
    return result.value


def borrow_rate_annual(*_args: object, **_kwargs: object) -> float:
    raise BorrowProhibited("short stock prohibited in v1; hedge with MES")


@dataclass(frozen=True)
class Fill:
    fill_id: str
    symbol: str
    bucket: ProductBucket
    side: Literal["buy", "sell"]
    quantity: float
    price: float
    nbbo_mid: float
    product_kind: Literal["equity", "option", "future"]
    premium: float | None = None


@dataclass(frozen=True)
class CalibrationReport:
    n_fills: int
    equity_error_bps: float | None
    option_error_pct_of_premium: float | None
    equity_within_tolerance: bool
    option_within_tolerance: bool

    @property
    def passed(self) -> bool:
        return self.equity_within_tolerance and self.option_within_tolerance


def _one_way_equity_bps(fill: Fill) -> float:
    signed = 1.0 if fill.side == "buy" else -1.0
    return 1e4 * signed * (fill.price - fill.nbbo_mid) / fill.nbbo_mid


def _one_way_option_pct(fill: Fill) -> float:
    if fill.premium is None or fill.premium <= 0:
        raise ValueError(f"fill {fill.fill_id} missing premium")
    signed = 1.0 if fill.side == "buy" else -1.0
    return 100.0 * signed * (fill.price - fill.nbbo_mid) / fill.premium


def calibrate_fills(fills: Sequence[Fill]) -> CalibrationReport:
    """Mean round-trip-equivalent error vs the working model.

    One-way effective cost is doubled so it compares to modelled round trip.
    P0 exit: equities within 3 bps, options within 0.3% of premium.
    """
    equity_errors: list[float] = []
    option_errors: list[float] = []
    for fill in fills:
        modelled = round_trip(fill.bucket)
        if fill.product_kind == "option":
            realized_rt = 2.0 * _one_way_option_pct(fill)
            option_errors.append(realized_rt - modelled.value)
        else:
            realized_rt = 2.0 * _one_way_equity_bps(fill)
            equity_errors.append(realized_rt - modelled.value)

    equity_err = (
        sum(equity_errors) / len(equity_errors) if equity_errors else None
    )
    option_err = (
        sum(option_errors) / len(option_errors) if option_errors else None
    )
    equity_ok = equity_err is None or abs(equity_err) <= EQUITY_CALIBRATION_TOLERANCE_BPS
    option_ok = (
        option_err is None or abs(option_err) <= OPTION_CALIBRATION_TOLERANCE_PCT
    )
    return CalibrationReport(
        n_fills=len(fills),
        equity_error_bps=equity_err,
        option_error_pct_of_premium=option_err,
        equity_within_tolerance=equity_ok,
        option_within_tolerance=option_ok,
    )
