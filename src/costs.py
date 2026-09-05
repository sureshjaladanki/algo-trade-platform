"""Indian statutory and broker friction. No book computes its own cost."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

PAISE = Decimal("0.01")
GST_RATE = Decimal("0.18")
SEBI_TURNOVER_RATE = Decimal("0.000001")  # ₹10 / crore
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

# Zerodha published schedule as of 2026-09-05 (upper end of NSE's cash/futures range).
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
    """STT is deductible only against business income (L2)."""

    CAPITAL_GAINS = "capital_gains"
    SPECULATIVE = "speculative"
    NON_SPECULATIVE = "non_speculative"


def _money(value: Decimal) -> Decimal:
    return value.quantize(PAISE, rounding=ROUND_HALF_UP)


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
    """Indian Stamp Act schedule; buyer only."""
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
    """₹20 floor is per executed order, not an average of the clip."""
    if n_orders < 1:
        raise ValueError("n_orders")
    if product in {Product.DELIVERY, Product.ETF}:
        return Decimal("0.00")
    if product is Product.OPTIONS:
        return _money(ORDER_BROKERAGE_CAP * n_orders)
    per_order = min(value * INTRADAY_FUTURES_BROKERAGE_RATE, ORDER_BROKERAGE_CAP)
    return _money(per_order * n_orders)


def gst(
    brokerage_amt: Decimal,
    exchange_amt: Decimal,
    sebi_fee: Decimal,
) -> Decimal:
    """18% on brokerage + exchange transaction + SEBI. Not on STT, stamp, or IPFT."""
    return _money((brokerage_amt + exchange_amt + sebi_fee) * GST_RATE)


def dp_charge(n_isins_sold: int) -> Decimal:
    """₹15.34 per ISIN per day of sale; zero on buys, intraday and F&O."""
    if n_isins_sold < 0:
        raise ValueError("n_isins_sold")
    return _money(DP_PER_ISIN * n_isins_sold)


@dataclass(frozen=True)
class RoundTrip:
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


def round_trip_bps(
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
) -> RoundTrip:
    """Composite round trip. `buy_value` / `sell_value` are per-order notionals (or premium)."""
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
        exchange_charge(venue, product, buy_base) * n_buy_orders
        if n_buy_orders
        else Decimal("0.00")
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
        dp_charge(n_isins_sold)
        if product in {Product.DELIVERY, Product.ETF}
        else Decimal("0.00")
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
    deductible = book is not BookKind.CAPITAL_GAINS
    return RoundTrip(
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
        stt_deductible=deductible,
    )


@dataclass(frozen=True)
class ExerciseOrClose:
    action: str
    exercise_stt: Decimal
    square_off_cost: Decimal


def exercise_or_square_off(
    intrinsic: Decimal,
    lot: int,
    n_lots: int,
    venue: Venue = Venue.NSE,
) -> ExerciseOrClose:
    """Exercise STT (0.15% of intrinsic, purchaser) versus closing the long on the screen."""
    intrinsic_value = intrinsic * Decimal(lot) * Decimal(n_lots)
    exercise_amt = stt(Product.OPTIONS, Side.BUY, Decimal(0), intrinsic=intrinsic_value)
    close = round_trip_bps(
        product=Product.OPTIONS,
        venue=venue,
        buy_value=Decimal(0),
        sell_value=Decimal(0),
        n_buy_orders=0,
        n_sell_orders=1,
        book=BookKind.NON_SPECULATIVE,
        sell_premium=Decimal(0),
    )
    action = "exercise" if exercise_amt <= close.rupees else "square_off"
    return ExerciseOrClose(
        action=action,
        exercise_stt=exercise_amt,
        square_off_cost=close.rupees,
    )
