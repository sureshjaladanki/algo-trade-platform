"""P0: costs reproduces the Zerodha published schedule to within ₹1. No bps literals."""

from decimal import Decimal

from src.costs import (
    BookKind,
    Product,
    Side,
    Venue,
    brokerage,
    dp_charge,
    exchange_charge,
    exercise_or_square_off,
    gst,
    ipft,
    round_trip_bps,
    sebi_turnover_fee,
    stamp_duty,
    stt,
)


def _d(value: str) -> Decimal:
    return Decimal(value)


def test_stt_delivery_both_legs() -> None:
    value = _d("100000")
    assert stt(Product.DELIVERY, Side.BUY, value) == _d("100.00")
    assert stt(Product.DELIVERY, Side.SELL, value) == _d("100.00")


def test_stt_etf_sell_only() -> None:
    value = _d("100000")
    assert stt(Product.ETF, Side.BUY, value) == _d("0.00")
    assert stt(Product.ETF, Side.SELL, value) == _d("1.00")


def test_stt_intraday_futures_options_exercise() -> None:
    assert stt(Product.INTRADAY, Side.BUY, _d("100000")) == _d("0.00")
    assert stt(Product.INTRADAY, Side.SELL, _d("100000")) == _d("25.00")
    assert stt(Product.FUTURES, Side.SELL, _d("1552000")) == _d("776.00")
    assert stt(Product.OPTIONS, Side.SELL, _d("0"), premium=_d("11700")) == _d("17.55")
    assert stt(Product.OPTIONS, Side.BUY, _d("0"), intrinsic=_d("13000")) == _d("19.50")


def test_brokerage_floor_is_per_order() -> None:
    clip = _d("100000")
    one = brokerage(Product.INTRADAY, clip, 1)
    two = brokerage(Product.INTRADAY, clip, 2)
    assert one == _d("20.00")
    assert two == _d("40.00")
    assert brokerage(Product.DELIVERY, clip, 2) == _d("0.00")
    assert brokerage(Product.OPTIONS, clip, 4) == _d("80.00")


def test_gst_excludes_stt_and_stamp() -> None:
    assert gst(_d("0"), _d("6.14"), _d("0.20")) == _d("1.14")


def test_dp_charge_per_isin() -> None:
    assert dp_charge(0) == _d("0.00")
    assert dp_charge(1) == _d("15.34")
    assert dp_charge(3) == _d("46.02")


def test_cash_delivery_round_trip_within_one_rupee() -> None:
    """Zerodha calculator substitution; ₹1 lakh NSE delivery, 1 ISIN sold."""
    trip = round_trip_bps(
        product=Product.DELIVERY,
        venue=Venue.NSE,
        buy_value=_d("100000"),
        sell_value=_d("100000"),
        n_buy_orders=1,
        n_sell_orders=1,
        book=BookKind.CAPITAL_GAINS,
        n_isins_sold=1,
    )
    assert trip.stt == _d("200.00")
    assert trip.stamp == stamp_duty(Product.DELIVERY, _d("100000"))
    assert trip.dp == _d("15.34")
    assert not trip.stt_deductible
    assert abs(trip.rupees - _d("238.02")) <= _d("1")


def test_etf_delivery_round_trip_within_one_rupee() -> None:
    trip = round_trip_bps(
        product=Product.ETF,
        venue=Venue.NSE,
        buy_value=_d("100000"),
        sell_value=_d("100000"),
        n_buy_orders=1,
        n_sell_orders=1,
        book=BookKind.CAPITAL_GAINS,
        n_isins_sold=1,
    )
    assert trip.stt == _d("1.00")
    assert abs(trip.rupees - _d("39.02")) <= _d("1")


def test_intraday_round_trip_within_one_rupee() -> None:
    trip = round_trip_bps(
        product=Product.INTRADAY,
        venue=Venue.NSE,
        buy_value=_d("100000"),
        sell_value=_d("100000"),
        n_buy_orders=1,
        n_sell_orders=1,
        book=BookKind.SPECULATIVE,
    )
    assert trip.stt_deductible
    assert trip.dp == _d("0.00")
    assert trip.brokerage == _d("40.00")
    assert abs(trip.rupees - _d("82.88")) <= _d("1")


def test_index_futures_round_trip_within_one_rupee() -> None:
    notional = _d("1552000")
    trip = round_trip_bps(
        product=Product.FUTURES,
        venue=Venue.NSE,
        buy_value=notional,
        sell_value=notional,
        n_buy_orders=1,
        n_sell_orders=1,
        book=BookKind.NON_SPECULATIVE,
    )
    assert trip.stt == _d("776.00")
    assert trip.brokerage == _d("40.00")
    assert abs(trip.rupees - _d("940.45")) <= _d("1")


def test_index_options_round_trip_within_one_rupee() -> None:
    """ATM straddle: two sells at 90×65, two buy-backs at 45×65."""
    sell_prem = _d("5850")
    buy_prem = _d("2925")
    trip = round_trip_bps(
        product=Product.OPTIONS,
        venue=Venue.NSE,
        buy_value=buy_prem,
        sell_value=sell_prem,
        n_buy_orders=2,
        n_sell_orders=2,
        book=BookKind.NON_SPECULATIVE,
        buy_premium=buy_prem,
        sell_premium=sell_prem,
    )
    assert trip.brokerage == _d("80.00")
    assert trip.stt == stt(Product.OPTIONS, Side.SELL, _d("0"), premium=sell_prem) * 2
    assert abs(trip.rupees - _d("119.62")) <= _d("1")


def test_exercised_option_stt() -> None:
    intrinsic = _d("200") * 65 * 1
    assert stt(Product.OPTIONS, Side.BUY, _d("0"), intrinsic=intrinsic) == _d("19.50")


def test_exercise_or_square_off_flips_with_intrinsic() -> None:
    shallow = exercise_or_square_off(_d("200"), lot=65, n_lots=1)
    deep = exercise_or_square_off(_d("1000"), lot=65, n_lots=1)
    assert shallow.action == "exercise"
    assert deep.action == "square_off"
    assert shallow.exercise_stt == _d("19.50")
    assert deep.exercise_stt == _d("97.50")


def test_bse_futures_exchange_is_zero() -> None:
    assert exchange_charge(Venue.BSE, Product.FUTURES, _d("1552000")) == _d("0.00")


def test_sebi_and_ipft_line_items() -> None:
    value = _d("100000")
    assert sebi_turnover_fee(value) == _d("0.10")
    assert ipft(Product.DELIVERY, value) == _d("0.10")
    assert ipft(Product.FUTURES, _d("1552000")) == _d("7.76")


def test_round_trip_bps_is_derived_from_rupees() -> None:
    trip = round_trip_bps(
        product=Product.DELIVERY,
        venue=Venue.NSE,
        buy_value=_d("100000"),
        sell_value=_d("100000"),
        n_buy_orders=1,
        n_sell_orders=1,
        book=BookKind.CAPITAL_GAINS,
        n_isins_sold=1,
    )
    expected = (trip.rupees / _d("100000") * _d("10000")).quantize(_d("0.1"))
    assert trip.bps == expected
