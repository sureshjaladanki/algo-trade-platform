"""A0.5 vertical put-spread round-trip. ThetaData FREE. Not A1."""

from datetime import date, timedelta

import pytest

from src.books.vrp_spread import (
    A05_HYPOTHESIZED,
    A05_N_PLAN,
    A05_SIGMA,
    CREDIT_RETAIN_MIN,
    black_scholes_put,
    black_scholes_put_delta,
    black_scholes_put_vega,
    construct_spreads,
    entry_date,
    implied_vol_put,
    is_monthly_expiry,
    is_third_friday,
    monthly_expiries,
    pick_put_spread,
    put_iv_delta,
    run_spread_screen,
    screen_declaration,
)
from src.costs import (
    WORKING_TABLE,
    ProductBucket,
    option_fees_round_trip_usd,
    vertical_spread_round_trip,
)
from src.harness import MdeGateError, print_mde, reset
from src.theta import OptionQuote, quotes_from_records
from src.yahoo import DailyBar


def setup_function() -> None:
    reset()


def test_vertical_spread_round_trip_uses_costs_fees() -> None:
    cost = vertical_spread_round_trip(
        short_bid=9.8,
        short_ask=10.2,
        long_bid=3.9,
        long_ask=4.1,
    )
    assert cost.credit == pytest.approx(6.0)
    assert cost.quoted_spread_both_legs == pytest.approx(0.6)
    assert cost.quoted_pct_of_credit == pytest.approx(10.0)
    assert cost.fees_usd == pytest.approx(2.0 * option_fees_round_trip_usd(1))
    assert cost.all_in_usd == pytest.approx(0.6 * 100.0 + cost.fees_usd)
    assert cost.retained_fraction == pytest.approx(1.0 - cost.all_in_usd / cost.credit_usd)
    assert cost.retained_fraction > CREDIT_RETAIN_MIN


def test_fat_spread_eats_credit_retention() -> None:
    cost = vertical_spread_round_trip(
        short_bid=4.0,
        short_ask=8.0,
        long_bid=1.0,
        long_ask=3.0,
    )
    assert cost.credit == pytest.approx(4.0)
    assert cost.quoted_spread_both_legs == pytest.approx(6.0)
    assert cost.retained_fraction < CREDIT_RETAIN_MIN


def test_atm_put_delta_near_half() -> None:
    price = black_scholes_put(100.0, 100.0, 1.0, rate=0.0, div=0.0, vol=0.2)
    assert price == pytest.approx(7.965567, rel=1e-4)
    delta = black_scholes_put_delta(100.0, 100.0, 1.0, rate=0.0, div=0.0, vol=0.2)
    assert delta == pytest.approx(-0.460172, rel=1e-3)
    vol = implied_vol_put(price, 100.0, 100.0, 1.0, rate=0.0, div=0.0)
    assert vol == pytest.approx(0.2, rel=1e-3)
    vega = black_scholes_put_vega(100.0, 100.0, 1.0, rate=0.0, div=0.0, vol=0.2)
    assert vega == pytest.approx(39.695, rel=1e-3)
    from src.theta import OptionQuote

    quote = OptionQuote(
        expiry=date(2025, 1, 2),
        trade_date=date(2024, 1, 2),
        strike=100.0,
        right="P",
        bid=7.9,
        ask=8.0,
    )
    solved = put_iv_delta(quote, 100.0)
    assert solved is not None


def test_third_friday_and_entry_date() -> None:
    assert is_third_friday(date(2024, 1, 19))
    assert not is_third_friday(date(2024, 1, 12))
    assert is_monthly_expiry(date(2012, 2, 16))
    assert is_monthly_expiry(date(2012, 2, 17))
    assert is_monthly_expiry(date(2012, 2, 18))
    assert not is_monthly_expiry(date(2012, 2, 10))


def test_monthly_expiries_one_per_month_prefers_friday() -> None:
    import polars as pl

    from src.books.vrp_existence import monthly_expiries

    frame = pl.DataFrame(
        {
            "expire_date": [
                date(2012, 1, 19),
                date(2016, 1, 15),
                date(2016, 1, 14),
            ]
        }
    )
    got = monthly_expiries(frame)
    assert got == [date(2012, 1, 19), date(2016, 1, 15)]
    days = [date(2023, 12, 1) + timedelta(days=i) for i in range(80)]
    days = [day for day in days if day.weekday() < 5]
    entry = entry_date(date(2024, 1, 19), days)
    assert entry is not None
    assert 30 <= (date(2024, 1, 19) - entry).days <= 45
    early = [date(2012, 1, 3) + timedelta(days=i) for i in range(80)]
    early = [day for day in early if day.weekday() < 5]
    jan = date(2012, 2, 17)
    assert is_third_friday(jan)
    old = entry_date(jan, early, start=date(2012, 1, 1))
    assert old is not None
    assert entry_date(jan, early) is None


def _quote(strike: float, bid: float, ask: float, *, trade=date(2024, 1, 2), expiry=date(2024, 2, 16)) -> OptionQuote:
    return OptionQuote(
        expiry=expiry,
        trade_date=trade,
        strike=strike,
        right="P",
        bid=bid,
        ask=ask,
    )


def test_pick_put_spread_selects_20_25_delta_and_50_width(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_delta(quote: OptionQuote, spot: float) -> float | None:
        mapping = {4700.0: -0.12, 4750.0: -0.225, 4800.0: -0.40}
        return mapping.get(quote.strike)

    monkeypatch.setattr("src.books.vrp_spread.put_delta", fake_delta)
    chain = [
        _quote(4700.0, 8.9, 9.1),
        _quote(4750.0, 14.8, 15.2),
        _quote(4800.0, 24.0, 26.0),
    ]
    spread = pick_put_spread(chain, 5000.0)
    assert spread is not None
    assert spread.short_strike == 4750.0
    assert spread.long_strike == 4700.0
    assert spread.round_trip.credit == pytest.approx(6.0)


def test_spread_screen_kills_when_retention_fails() -> None:
    fat = vertical_spread_round_trip(
        short_bid=4.0, short_ask=8.0, long_bid=1.0, long_ask=3.0
    )
    from src.books.vrp_spread import SpreadQuote

    quotes = [
        SpreadQuote(
            trade_date=date(2024, 1, 2),
            expiry=date(2024, 2, 16),
            dte=45,
            short_strike=4750.0,
            long_strike=4700.0,
            short_delta=-0.22,
            round_trip=fat,
        )
        for _ in range(12)
    ]
    screen = run_spread_screen(quotes, n_expiries=12)
    assert screen.retain_ok is False
    assert screen.authorize_a1 is False
    assert screen.n == 12
    assert screen.atm_all_in_high == WORKING_TABLE[ProductBucket.SPX_ATM_30_45].all_in_high


def test_a05_mde_closes_certification() -> None:
    decl = screen_declaration(A05_N_PLAN)
    assert decl.sigma == A05_SIGMA
    assert decl.hypothesized_effect == A05_HYPOTHESIZED
    assert decl.mde == pytest.approx(2.8 * 150.0 / (38**0.5), rel=1e-4)
    assert decl.mde_ratio > 0.5
    with pytest.raises(MdeGateError):
        print_mde(decl)


def test_quotes_from_records_skips_zero_bid() -> None:
    quotes = quotes_from_records(
        [
            {
                "expiry": "2024-02-16",
                "trade_date": "2024-01-02",
                "strike": 4750.0,
                "right": "put",
                "bid": 9.8,
                "ask": 10.2,
                "close": 10.0,
            },
            {
                "expiry": "2024-02-16",
                "trade_date": "2024-01-02",
                "strike": 1000.0,
                "right": "P",
                "bid": 0.0,
                "ask": 0.01,
                "close": 0.0,
            },
        ]
    )
    assert len(quotes) == 1
    assert quotes[0].strike == pytest.approx(4750.0)
    assert quotes[0].bid == pytest.approx(9.8)
    assert quotes[0].right == "P"


def test_construct_spreads_one_monthly_cycle(monkeypatch: pytest.MonkeyPatch) -> None:
    expiry = date(2024, 1, 19)
    trade = date(2023, 12, 13)
    spx = [DailyBar(trade, close=4700.0), DailyBar(expiry, close=4710.0)]

    def fake_loader(*, root: str, expiry: date, trade_date: date) -> list[OptionQuote]:
        assert root == "SPX"
        return [
            _quote(4600.0, 8.9, 9.1, trade=trade_date, expiry=expiry),
            _quote(4650.0, 14.8, 15.2, trade=trade_date, expiry=expiry),
        ]

    def fake_delta(quote: OptionQuote, spot: float) -> float | None:
        return {-0.12: quote.strike == 4600.0, -0.225: quote.strike == 4650.0} and (
            -0.12 if quote.strike == 4600.0 else -0.225
        )

    monkeypatch.setattr("src.books.vrp_spread.put_delta", fake_delta)
    spreads = construct_spreads(spx=spx, expiries=[expiry], chain_loader=fake_loader)
    assert len(spreads) == 1
    assert spreads[0].short_strike == 4650.0
    assert spreads[0].long_strike == 4600.0
    assert monthly_expiries([expiry]) == [expiry]
