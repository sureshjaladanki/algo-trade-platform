"""After-tax VTI hold series — the denominator of every later claim.

Before-tax total return is close-to-close plus dividend reinvestment.
The 3 bps expense ratio is already inside VTI's price; it is not subtracted again.
After-tax hold: qualified-dividend tax (working 20%) is paid from each dividend
and only the remainder is reinvested. Unrealized price appreciation is not taxed.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.tax import QD_RATE, Wrapper, dividend_tax
from src.yahoo import DailyBar
from src.yahoo import fetch_yahoo_bars as fetch_symbol_bars

VTI_START = date(2005, 1, 1)
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DAILY_CSV = REPO_ROOT / "data" / "raw" / "vti_daily.csv"
DEFAULT_DERIVED_CSV = REPO_ROOT / "data" / "derived" / "vti_after_tax.csv"
PUBLISHED_CAGR_TOLERANCE = 0.0005  # 5 bps/yr


@dataclass(frozen=True)
class IndexPoint:
    date: date
    before_tax: float
    after_tax: float


def _parse_day(value: str) -> date:
    return date.fromisoformat(value[:10])


def load_daily_bars(path: Path = DEFAULT_DAILY_CSV) -> list[DailyBar]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        bars = [
            DailyBar(
                date=_parse_day(row["date"]),
                close=float(row["close"]),
                dividend=float(row["dividend"]),
            )
            for row in rows
        ]
    return [bar for bar in bars if bar.date >= VTI_START and bar.close > 0]


def fetch_yahoo_bars() -> list[DailyBar]:
    return fetch_symbol_bars("VTI", start=VTI_START)


def write_daily_bars(bars: list[DailyBar], path: Path = DEFAULT_DAILY_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "close", "dividend"])
        writer.writeheader()
        for bar in bars:
            writer.writerow(
                {
                    "date": bar.date.isoformat(),
                    "close": f"{bar.close:.6f}",
                    "dividend": f"{bar.dividend:.6f}",
                }
            )


def total_return_series(
    bars: list[DailyBar],
    *,
    dividend_tax_rate: float,
) -> list[tuple[date, float]]:
    if not bars:
        raise ValueError("bars must be non-empty")
    shares = 1.0 / bars[0].close
    out: list[tuple[date, float]] = []
    for bar in bars:
        if bar.dividend:
            cash = shares * bar.dividend * (1.0 - dividend_tax_rate)
            shares += cash / bar.close
        out.append((bar.date, shares * bar.close))
    return out


def after_tax_vti_series(bars: list[DailyBar]) -> list[IndexPoint]:
    before = dict(total_return_series(bars, dividend_tax_rate=0.0))
    after = dict(
        total_return_series(bars, dividend_tax_rate=QD_RATE)
    )
    return [
        IndexPoint(date=bar.date, before_tax=before[bar.date], after_tax=after[bar.date])
        for bar in bars
    ]


def write_after_tax_series(
    points: list[IndexPoint], path: Path = DEFAULT_DERIVED_CSV
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["date", "before_tax", "after_tax"]
        )
        writer.writeheader()
        for point in points:
            writer.writerow(
                {
                    "date": point.date.isoformat(),
                    "before_tax": f"{point.before_tax:.8f}",
                    "after_tax": f"{point.after_tax:.8f}",
                }
            )


def calendar_year_returns(points: list[IndexPoint], *, field: str) -> dict[int, float]:
    first_of_year: dict[int, float] = {}
    last_of_year: dict[int, float] = {}
    for point in points:
        value = getattr(point, field)
        year = point.date.year
        if year not in first_of_year:
            first_of_year[year] = value
        last_of_year[year] = value
    out: dict[int, float] = {}
    prior_last: float | None = None
    for year in sorted(last_of_year):
        start = prior_last if prior_last is not None else first_of_year[year]
        out[year] = last_of_year[year] / start - 1.0
        prior_last = last_of_year[year]
    return out


def annualized_return(points: list[IndexPoint], *, field: str) -> float:
    if len(points) < 2:
        raise ValueError("need at least two points")
    start = getattr(points[0], field)
    end = getattr(points[-1], field)
    years = (points[-1].date - points[0].date).days / 365.25
    return (end / start) ** (1.0 / years) - 1.0


def published_cagr_error(
    points: list[IndexPoint],
    published_year_returns: dict[int, float],
) -> float:
    """Annualized difference between constructed before-tax TR and a published series."""
    constructed = calendar_year_returns(points, field="before_tax")
    years = sorted(year for year in published_year_returns if year in constructed)
    if not years:
        raise ValueError("no overlapping years with the published series")
    growth_constructed = 1.0
    growth_published = 1.0
    for year in years:
        growth_constructed *= 1.0 + constructed[year]
        growth_published *= 1.0 + published_year_returns[year]
    n = len(years)
    cagr_constructed = growth_constructed ** (1.0 / n) - 1.0
    cagr_published = growth_published ** (1.0 / n) - 1.0
    return cagr_constructed - cagr_published


def dividend_tax_drag_bps(points: list[IndexPoint]) -> float:
    """Before-tax minus after-tax, annualized, in bps. Sanity check vs ~26 bps working."""
    before = annualized_return(points, field="before_tax")
    after = annualized_return(points, field="after_tax")
    return 1e4 * (before - after)


def qualified_dividend_tax_amount(gross_dividend: float) -> float:
    return dividend_tax(
        gross_dividend, qualified=True, wrapper=Wrapper.TAXABLE
    )
