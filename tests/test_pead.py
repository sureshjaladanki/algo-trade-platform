"""Book B $0 listed PEAD screen. EDGAR dates × Yahoo survivors. Not B1."""

from datetime import date, timedelta

import pytest

from src.books.pead import (
    KILL_BPS,
    Event,
    build_events,
    expensive_round_trip_bps,
    parse_constituents_csv,
    parse_wiki_tickers,
    pooled_net_bps,
    run_pead_screen,
    screen_declaration,
)
from src.costs import WORKING_TABLE, ProductBucket
from src.edgar import Filing, parse_company_tickers
from src.harness import HarnessGuardError, MdeGateError, print_mde, reset, run_declared
from src.universe import LiquidityBucket
from src.yahoo import DailyBar


def setup_function() -> None:
    reset()


def _weekdays(start: date, n: int) -> list[date]:
    days: list[date] = []
    day = start
    while len(days) < n:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


def test_expensive_mid_cap_cost_is_blueprint_high() -> None:
    assert expensive_round_trip_bps(LiquidityBucket.MID_CAP) == WORKING_TABLE[
        ProductBucket.MID_CAP
    ].all_in_high


def test_wiki_and_csv_ticker_parsers() -> None:
    csv_text = "Symbol,Security\nAAPL,Apple\nBRK.B,Berkshire\n"
    assert parse_constituents_csv(csv_text) == ["AAPL", "BRK-B"]
    wiki = """
{| class="wikitable sortable"
|-
! Symbol
|-
| ABC
| Alpha
|-
| {{NasdaqSymbol|WXYZ}}
| {{NyseSymbol|AA}}
|}
"""
    tickers = parse_wiki_tickers(wiki)
    assert "ABC" in tickers
    assert "WXYZ" in tickers
    assert "AA" in tickers


def test_company_tickers_strip_cik_zeros() -> None:
    mapping = parse_company_tickers(
        {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple"}}
    )
    assert mapping["320193"] == "AAPL"


def _mid_prices() -> list[DailyBar]:
    days = _weekdays(date(2020, 1, 2), 45)
    bars: list[DailyBar] = []
    for i, day in enumerate(days):
        close = 40.0
        if i == 19:
            close = 40.0
        if i == 21:
            close = 40.8
        if i == 41:
            close = 41.412
        bars.append(DailyBar(day, close=close, volume=700_000.0))
    return bars


def test_long_only_event_nets_expensive_mid_cap_cost() -> None:
    bars = _mid_prices()
    days = [bar.date for bar in bars]
    filings = [
        Filing("1", "Mid One", "8-K", days[20], "000-1", "edgar/data/1/000-1.txt"),
        Filing("1", "Mid One", "8-K", days[10], "000-2", "edgar/data/1/000-2.txt"),
    ]
    events = build_events(
        filings=filings,
        cik_to_ticker={"1": "MID1"},
        universe={"MID1"},
        prices={"MID1": bars},
    )
    assert len(events) == 1
    event = events[0]
    assert event.bucket is LiquidityBucket.MID_CAP
    surprise = 40.8 / 40.0 - 1.0
    fwd = 41.412 / 40.8 - 1.0
    assert event.surprise == pytest.approx(surprise)
    assert event.fwd == pytest.approx(fwd)
    assert event.net_bps == pytest.approx(1e4 * fwd - 25.0)


def test_negative_surprise_is_dropped() -> None:
    days = _weekdays(date(2020, 1, 2), 45)
    bars = []
    for i, day in enumerate(days):
        close = 40.0 if i != 21 else 39.0
        bars.append(DailyBar(day, close=close, volume=700_000.0))
    filings = [Filing("1", "Mid One", "8-K", days[20], "000-1", "edgar/data/1/000-1.txt")]
    events = build_events(
        filings=filings,
        cik_to_ticker={"1": "MID1"},
        universe={"MID1"},
        prices={"MID1": bars},
    )
    assert events == []


def test_harness_prints_mde_before_peek_and_kill_uses_40bps() -> None:
    cheap = Event(
        symbol="MID1",
        event_date=date(2020, 3, 16),
        surprise=0.02,
        fwd=0.005,
        adv_usd=30_000_000.0,
        bucket=LiquidityBucket.MID_CAP,
        net_bps=25.0,
    )
    with pytest.raises(HarnessGuardError):
        run_declared(lambda: run_pead_screen([cheap]))
    with pytest.raises(MdeGateError):
        print_mde(screen_declaration(100))
    reset()
    # Large n so the gate opens; the kill is still the 40 bps mean.
    print_mde(screen_declaration(12_000))
    screen = run_declared(lambda: run_pead_screen([cheap]))
    assert screen.kill is True
    assert screen.buy_polygon is False
    assert screen.mean_mid_bps == pytest.approx(25.0)
    assert KILL_BPS == 40.0


def test_pooled_mean() -> None:
    a = Event("A", date(2020, 1, 2), 0.02, 0.01, 30e6, LiquidityBucket.MID_CAP, 100.0)
    b = Event("B", date(2020, 1, 3), 0.02, 0.01, 30e6, LiquidityBucket.MID_CAP, 50.0)
    assert pooled_net_bps([a, b]) == pytest.approx(75.0)
