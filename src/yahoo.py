"""Public Yahoo chart bars. Cached under data/raw/yahoo; safe to re-fetch."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "data" / "raw" / "yahoo"
USER_AGENT = "algo-trade-platform/0.1 (research)"
PERIOD_END = 1_893_456_000  # 2030-01-01 UTC


@dataclass(frozen=True)
class DailyBar:
    date: date
    close: float
    dividend: float = 0.0
    volume: float = 0.0


def _parse_day(value: str) -> date:
    return date.fromisoformat(value[:10])


def cache_path(symbol: str, directory: Path = CACHE_DIR) -> Path:
    safe = symbol.replace("^", "_").replace("/", "-")
    return directory / f"{safe}.csv"


def load_daily_bars(path: Path) -> list[DailyBar]:
    import csv

    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        bars = [
            DailyBar(
                date=_parse_day(row["date"]),
                close=float(row["close"]),
                dividend=float(row.get("dividend") or 0.0),
                volume=float(row.get("volume") or 0.0),
            )
            for row in rows
        ]
    return [bar for bar in bars if bar.close > 0]


def write_daily_bars(bars: list[DailyBar], path: Path) -> None:
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["date", "close", "dividend", "volume"]
        )
        writer.writeheader()
        for bar in bars:
            writer.writerow(
                {
                    "date": bar.date.isoformat(),
                    "close": f"{bar.close:.6f}",
                    "dividend": f"{bar.dividend:.6f}",
                    "volume": f"{bar.volume:.0f}",
                }
            )


def _chart_url(symbol: str, start: date) -> str:
    period1 = int(datetime(start.year, start.month, start.day, tzinfo=UTC).timestamp())
    encoded = urllib.parse.quote(symbol, safe="")
    return (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}"
        f"?period1={period1}&period2={PERIOD_END}&interval=1d&events=div%2Csplit"
    )


def fetch_yahoo_bars(symbol: str, *, start: date = date(2005, 1, 1)) -> list[DailyBar]:
    request = urllib.request.Request(
        _chart_url(symbol, start),
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read())
    result = payload["chart"]["result"][0]
    timestamps: list[int] = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    closes: list[float | None] = quote["close"]
    volumes: list[float | None] = quote.get("volume") or [None] * len(closes)
    events = result.get("events") or {}
    raw_divs = events.get("dividends") or {}
    div_by_day: dict[date, float] = {}
    for item in raw_divs.values():
        day = datetime.fromtimestamp(int(item["date"]), tz=UTC).date()
        div_by_day[day] = div_by_day.get(day, 0.0) + float(item["amount"])
    bars: list[DailyBar] = []
    for ts, close, volume in zip(timestamps, closes, volumes, strict=True):
        if close is None:
            continue
        day = datetime.fromtimestamp(int(ts), tz=UTC).date()
        bars.append(
            DailyBar(
                date=day,
                close=float(close),
                dividend=div_by_day.get(day, 0.0),
                volume=float(volume or 0.0),
            )
        )
    return [bar for bar in bars if bar.date >= start]


def load_or_fetch(
    symbol: str,
    *,
    start: date = date(2005, 1, 1),
    directory: Path = CACHE_DIR,
) -> list[DailyBar]:
    path = cache_path(symbol, directory)
    if path.exists():
        return [bar for bar in load_daily_bars(path) if bar.date >= start]
    bars = fetch_yahoo_bars(symbol, start=start)
    write_daily_bars(bars, path)
    return bars
