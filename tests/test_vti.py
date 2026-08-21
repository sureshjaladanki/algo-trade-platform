"""After-tax VTI hold series vs published Vanguard calendar-year total return."""

import csv
from datetime import date
from pathlib import Path

import pytest

from src.tax import QD_RATE
from src.vti import (
    PUBLISHED_CAGR_TOLERANCE,
    DailyBar,
    after_tax_vti_series,
    calendar_year_returns,
    dividend_tax_drag_bps,
    fetch_yahoo_bars,
    published_cagr_error,
    total_return_series,
    write_after_tax_series,
    write_daily_bars,
)

GOLDEN = Path(__file__).parent / "golden" / "vti_published_total_return.csv"
DAILY = Path(__file__).resolve().parent.parent / "data" / "raw" / "vti_daily.csv"


def _published(column: str) -> dict[int, float]:
    with GOLDEN.open(newline="", encoding="utf-8") as handle:
        return {int(row["year"]): float(row[column]) for row in csv.DictReader(handle)}


def test_dividend_reinvestment_hand_worked() -> None:
    bars = [
        DailyBar(date(2020, 1, 2), close=100.0, dividend=0.0),
        DailyBar(date(2020, 1, 3), close=100.0, dividend=2.0),
        DailyBar(date(2020, 1, 6), close=100.0, dividend=0.0),
    ]
    before = dict(total_return_series(bars, dividend_tax_rate=0.0))
    after = dict(total_return_series(bars, dividend_tax_rate=QD_RATE))
    assert before[date(2020, 1, 6)] == pytest.approx(1.02)
    assert after[date(2020, 1, 6)] == pytest.approx(1.016)


def test_after_tax_is_below_before_tax_and_drag_is_dividend_sized() -> None:
    bars = [
        DailyBar(date(2010, 1, 4), close=50.0),
        DailyBar(date(2010, 3, 15), close=51.0, dividend=0.25),
        DailyBar(date(2010, 6, 15), close=52.0, dividend=0.25),
        DailyBar(date(2010, 9, 15), close=53.0, dividend=0.25),
        DailyBar(date(2010, 12, 15), close=54.0, dividend=0.25),
        DailyBar(date(2010, 12, 31), close=55.0),
    ]
    points = after_tax_vti_series(bars)
    assert points[-1].after_tax < points[-1].before_tax
    drag = dividend_tax_drag_bps(points)
    assert drag > 0


def _load_or_fetch_bars() -> list[DailyBar]:
    if DAILY.exists():
        from src.vti import load_daily_bars

        return load_daily_bars(DAILY)
    bars = fetch_yahoo_bars()
    write_daily_bars(bars, DAILY)
    return bars


def test_constructed_vti_tracks_vanguard_market_price_within_5bps_per_year() -> None:
    bars = _load_or_fetch_bars()
    points = after_tax_vti_series(bars)
    write_after_tax_series(points)
    published = _published("market_price_total_return")
    error = published_cagr_error(points, published)
    assert abs(error) <= PUBLISHED_CAGR_TOLERANCE, f"CAGR error {error:.6f} exceeds 5 bps/yr"
    constructed = calendar_year_returns(points, field="before_tax")
    assert 2011 in constructed and 2025 in constructed
    drag = dividend_tax_drag_bps(
        [p for p in points if date(2011, 1, 1) <= p.date <= date(2025, 12, 31)]
    )
    assert 10 < drag < 50
