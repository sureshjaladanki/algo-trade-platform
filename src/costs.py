"""Round-trip cost model. Every backtest imports this; none re-implements it.

Working constants follow Blueprint §0.2 until fill calibration replaces them.
Section 31 and FINRA TAF reset on a published schedule; the values here are
the plan's working numbers, not a live feed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
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
SPX_MULTIPLIER = 100.0

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

# USD share lines carry no FX conversion. LSE round-trip lives on the wrapper
# module, not as a ProductBucket (GL-L2 / GL-H4). Irish accumulating USD share
# classes dealt from already-held USD (GL-L1 / FEMA s.6(4)): W0 CSPX/XUSE/VWRA
# and dated GL2 CSUS+VXUA. Zero FX on this line. Not the India (INR) line.
USD_LINE_FX_BPS = 0.0
USD_LINE_IRISH_ACC_ISINS: frozenset[str] = frozenset(
    {
        "IE00B5BMR087",  # CSPX (W0)
        "IE000R4ZNTN3",  # XUSE (W0)
        "IE00BK5BQT80",  # VWRA (W0 substitute)
        "IE00B52SFT06",  # CSUS (GL2 dated)
        "IE0009A5ADV9",  # VXUA (GL2 dated)
    }
)

# Frozen US-person table. A new venue bucket must be named in
# GL_H4_PASSED_VENUE_BUCKETS after a recorded GL-H4 pass at the $25,000 floor.
US_PERSON_PRODUCT_BUCKETS: frozenset[str] = frozenset(
    {
        "liquid_etf",
        "large_cap",
        "mid_cap",
        "small_cap",
        "mes",
        "es",
        "spx_atm_30_45",
        "xsp_atm_30_45",
        "spx_10d_wing",
        "spy_option_atm",
    }
)
GL_H4_PASSED_VENUE_BUCKETS: frozenset[str] = frozenset()


def unauthorized_venue_buckets() -> tuple[str, ...]:
    present = {bucket.value for bucket in ProductBucket}
    allowed = US_PERSON_PRODUCT_BUCKETS | GL_H4_PASSED_VENUE_BUCKETS
    return tuple(sorted(present - allowed))


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


@dataclass(frozen=True)
class SpreadRoundTrip:
    """All-in cost of a two-leg vertical, open and close, as a fraction of credit."""

    credit: float
    credit_usd: float
    quoted_spread_both_legs: float
    quoted_pct_of_credit: float
    fees_usd: float
    all_in_usd: float
    all_in_pct_of_credit: float
    retained_fraction: float


def vertical_spread_round_trip(
    *,
    short_bid: float,
    short_ask: float,
    long_bid: float,
    long_ask: float,
    contracts: int = 1,
    multiplier: float = SPX_MULTIPLIER,
) -> SpreadRoundTrip:
    """Round-trip a credit vertical: pay the full quoted spread on both legs plus fees.

    Open: sell the short leg, buy the long. Close: buy the short, sell the long.
    That is one full bid–ask on each leg. Fees are two option series, each open+close.
    """
    if short_ask < short_bid or long_ask < long_bid:
        raise ValueError("ask must be >= bid")
    if contracts <= 0:
        raise ValueError("contracts must be > 0")
    short_mid = (short_bid + short_ask) / 2.0
    long_mid = (long_bid + long_ask) / 2.0
    credit = short_mid - long_mid
    if credit <= 0:
        raise ValueError("spread credit must be > 0")
    credit_usd = credit * multiplier * contracts
    quoted = (short_ask - short_bid) + (long_ask - long_bid)
    quoted_usd = quoted * multiplier * contracts
    fees = 2.0 * option_fees_round_trip_usd(contracts)
    all_in = quoted_usd + fees
    return SpreadRoundTrip(
        credit=credit,
        credit_usd=credit_usd,
        quoted_spread_both_legs=quoted,
        quoted_pct_of_credit=100.0 * quoted / credit,
        fees_usd=fees,
        all_in_usd=all_in,
        all_in_pct_of_credit=100.0 * all_in / credit_usd,
        retained_fraction=1.0 - all_in / credit_usd,
    )


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


def _us_round_trip_bps(bucket: ProductBucket) -> float:
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


# India statutory stack (in-equity Book L). ProductBucket / GL-H4 stay US-only.
_PAISE = Decimal("0.01")
GST_RATE = Decimal("0.18")
SEBI_TURNOVER_RATE = Decimal("0.000001")
DP_PER_ISIN = Decimal("15.34")
ORDER_BROKERAGE_CAP = Decimal(20)
INTRADAY_FUTURES_BROKERAGE_RATE = Decimal("0.0003")
STT_DELIVERY = Decimal("0.001")
STT_ETF_SELL = Decimal("0.00001")
STT_INTRADAY_SELL = Decimal("0.00025")
STT_FUTURES_SELL = Decimal("0.0005")
STT_OPTIONS_PREMIUM_SELL = Decimal("0.0015")
STT_EXERCISE = Decimal("0.0015")
STAMP_DELIVERY = Decimal("0.00015")
STAMP_INTRADAY = Decimal("0.00003")
STAMP_FUTURES = Decimal("0.00002")
STAMP_OPTIONS = Decimal("0.00003")
NSE_CASH_TXN = Decimal("0.0000307")
BSE_CASH_TXN = Decimal("0.0000375")
NSE_FUTURES_TXN = Decimal("0.0000183")
BSE_FUTURES_TXN = Decimal(0)
NSE_OPTIONS_TXN = Decimal("0.0003553")
BSE_OPTIONS_TXN = Decimal("0.000325")
IPFT_CASH = Decimal("0.000001")
IPFT_FNO = Decimal("0.000005")


class Product(StrEnum):
    DELIVERY = "delivery"
    ETF = "etf"
    INTRADAY = "intraday"
    FUTURES = "futures"
    OPTIONS = "options"


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class Venue(StrEnum):
    NSE = "nse"
    BSE = "bse"


class BookKind(StrEnum):
    CAPITAL_GAINS = "capital_gains"
    SPECULATIVE = "speculative"
    NON_SPECULATIVE = "non_speculative"


def _money(value: Decimal) -> Decimal:
    return value.quantize(_PAISE, rounding=ROUND_HALF_UP)


def stt(
    product: Product,
    side: Side,
    value: Decimal,
    premium: Decimal | None = None,
    intrinsic: Decimal | None = None,
) -> Decimal:
    """STT as levied from 1 April 2026 (Finance Act, 2026)."""
    if product is Product.DELIVERY:
        return _money(value * STT_DELIVERY)
    if product is Product.ETF:
        if side is Side.BUY:
            return Decimal("0.00")
        return _money(value * STT_ETF_SELL)
    if product is Product.INTRADAY:
        if side is Side.BUY:
            return Decimal("0.00")
        return _money(value * STT_INTRADAY_SELL)
    if product is Product.FUTURES:
        if side is Side.BUY:
            return Decimal("0.00")
        return _money(value * STT_FUTURES_SELL)
    if product is Product.OPTIONS:
        if intrinsic is not None:
            return _money(intrinsic * STT_EXERCISE)
        if side is Side.BUY:
            return Decimal("0.00")
        return _money((premium if premium is not None else value) * STT_OPTIONS_PREMIUM_SELL)
    raise ValueError(product)


def stamp_duty(product: Product, buy_value: Decimal) -> Decimal:
    rates = {
        Product.DELIVERY: STAMP_DELIVERY,
        Product.ETF: STAMP_DELIVERY,
        Product.INTRADAY: STAMP_INTRADAY,
        Product.FUTURES: STAMP_FUTURES,
        Product.OPTIONS: STAMP_OPTIONS,
    }
    return _money(buy_value * rates[product])


def exchange_charge(venue: Venue, product: Product, value: Decimal) -> Decimal:
    cash = product in {Product.DELIVERY, Product.ETF, Product.INTRADAY}
    if cash:
        rate = NSE_CASH_TXN if venue is Venue.NSE else BSE_CASH_TXN
        return _money(value * rate)
    if product is Product.FUTURES:
        rate = NSE_FUTURES_TXN if venue is Venue.NSE else BSE_FUTURES_TXN
        return _money(value * rate)
    rate = NSE_OPTIONS_TXN if venue is Venue.NSE else BSE_OPTIONS_TXN
    return _money(value * rate)


def sebi_turnover_fee(value: Decimal) -> Decimal:
    return _money(value * SEBI_TURNOVER_RATE)


def ipft(product: Product, value: Decimal) -> Decimal:
    rate = IPFT_CASH if product in {Product.DELIVERY, Product.ETF, Product.INTRADAY} else IPFT_FNO
    return _money(value * rate)


def brokerage(product: Product, value: Decimal, n_orders: int) -> Decimal:
    if n_orders < 1:
        raise ValueError("n_orders")
    if product in {Product.DELIVERY, Product.ETF}:
        return Decimal("0.00")
    if product is Product.OPTIONS:
        return _money(ORDER_BROKERAGE_CAP * n_orders)
    per_order = min(value * INTRADAY_FUTURES_BROKERAGE_RATE, ORDER_BROKERAGE_CAP)
    return _money(per_order * n_orders)


def gst(brokerage_amt: Decimal, exchange_amt: Decimal, sebi_fee: Decimal) -> Decimal:
    return _money((brokerage_amt + exchange_amt + sebi_fee) * GST_RATE)


def dp_charge(n_isins_sold: int) -> Decimal:
    if n_isins_sold < 0:
        raise ValueError("n_isins_sold")
    return _money(DP_PER_ISIN * n_isins_sold)


@dataclass(frozen=True)
class IndiaRoundTrip:
    rupees: Decimal
    bps: Decimal
    stt: Decimal
    stamp: Decimal
    exchange: Decimal
    sebi: Decimal
    ipft: Decimal
    brokerage: Decimal
    gst: Decimal
    dp: Decimal
    stt_deductible: bool


def india_round_trip_bps(
    product: Product,
    venue: Venue,
    buy_value: Decimal,
    sell_value: Decimal,
    n_buy_orders: int,
    n_sell_orders: int,
    book: BookKind,
    n_isins_sold: int = 0,
    buy_premium: Decimal | None = None,
    sell_premium: Decimal | None = None,
    intrinsic: Decimal | None = None,
) -> IndiaRoundTrip:
    buy_base = buy_premium if buy_premium is not None else buy_value
    sell_base = sell_premium if sell_premium is not None else sell_value
    stt_buy = (
        stt(product, Side.BUY, buy_value, premium=buy_premium, intrinsic=intrinsic) * n_buy_orders
        if n_buy_orders
        else Decimal("0.00")
    )
    stt_sell = (
        stt(product, Side.SELL, sell_value, premium=sell_premium) * n_sell_orders
        if n_sell_orders
        else Decimal("0.00")
    )
    stt_amt = stt_buy + stt_sell
    stamp_amt = stamp_duty(product, buy_base) * n_buy_orders if n_buy_orders else Decimal("0.00")
    exch_buy = (
        exchange_charge(venue, product, buy_base) * n_buy_orders if n_buy_orders else Decimal("0.00")
    )
    exch_sell = (
        exchange_charge(venue, product, sell_base) * n_sell_orders
        if n_sell_orders
        else Decimal("0.00")
    )
    exch_amt = exch_buy + exch_sell
    sebi_amt = sebi_turnover_fee(buy_base) * n_buy_orders + sebi_turnover_fee(sell_base) * n_sell_orders
    ipft_amt = ipft(product, buy_base) * n_buy_orders + ipft(product, sell_base) * n_sell_orders
    brok_buy = brokerage(product, buy_value, n_buy_orders) if n_buy_orders else Decimal("0.00")
    brok_sell = brokerage(product, sell_value, n_sell_orders) if n_sell_orders else Decimal("0.00")
    brok_amt = brok_buy + brok_sell
    gst_amt = gst(brok_amt, exch_amt, sebi_amt)
    dp_amt = (
        dp_charge(n_isins_sold) if product in {Product.DELIVERY, Product.ETF} else Decimal("0.00")
    )
    rupees = stt_amt + stamp_amt + exch_amt + sebi_amt + ipft_amt + brok_amt + gst_amt + dp_amt
    notional = buy_value * n_buy_orders if n_buy_orders else sell_value * n_sell_orders
    if notional == 0:
        notional = sell_base * n_sell_orders if n_sell_orders else buy_base * n_buy_orders
    bps = (
        (rupees / notional * Decimal(10000)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        if notional
        else Decimal("0.0")
    )
    return IndiaRoundTrip(
        rupees=_money(rupees),
        bps=bps,
        stt=stt_amt,
        stamp=stamp_amt,
        exchange=exch_amt,
        sebi=sebi_amt,
        ipft=ipft_amt,
        brokerage=brok_amt,
        gst=gst_amt,
        dp=dp_amt,
        stt_deductible=book is not BookKind.CAPITAL_GAINS,
    )


def round_trip_bps(bucket: ProductBucket | None = None, **kwargs):
    """US ProductBucket → float bps. India Book L kwargs → IndiaRoundTrip."""
    if kwargs:
        return india_round_trip_bps(**kwargs)
    if bucket is None:
        raise TypeError("round_trip_bps requires a ProductBucket or India kwargs")
    return _us_round_trip_bps(bucket)
