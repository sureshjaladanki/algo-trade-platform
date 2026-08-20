"""Close-to-close residual vs Nifty over a pre-registered session window."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.events.constants import BPS


def session_index(dates: list[dt.date]) -> dict[dt.date, int]:
    ordered = sorted(dates)
    return {d: i for i, d in enumerate(ordered)}


def first_session_on_or_after(
    calendar: list[dt.date],
    day: dt.date,
) -> dt.date | None:
    for session in sorted(calendar):
        if session >= day:
            return session
    return None


def first_session_strictly_after(
    calendar: list[dt.date],
    day: dt.date,
) -> dt.date | None:
    for session in sorted(calendar):
        if session > day:
            return session
    return None


def first_close_containing(
    calendar: list[dt.date],
    event_at: dt.datetime,
    close_time: dt.time,
    index: dict[dt.date, int] | None = None,
) -> dt.date | None:
    """First session close that is known to contain the broadcast.

    Date-only stamps (midnight) cannot prove the same-day close contained
    the filing; those map to the first session strictly after the date.
    Filings at or after ``close_time`` map the same way.
    """
    day = event_at.date()
    if event_at.time() == dt.time.min or event_at.time() >= close_time:
        return first_session_strictly_after(calendar, day)
    sessions = index if index is not None else session_index(calendar)
    if day in sessions:
        return day
    return first_session_on_or_after(calendar, day)


def offset_date(
    calendar: list[dt.date],
    index: dict[dt.date, int],
    day: dt.date,
    offset: int,
) -> dt.date | None:
    pos = index.get(day)
    if pos is None:
        return None
    dest = pos + offset
    if dest < 0 or dest >= len(calendar):
        return None
    return calendar[dest]


def close_on(panel: pl.DataFrame, symbol: str, day: dt.date) -> float | None:
    hit = panel.filter((pl.col("symbol") == symbol) & (pl.col("date") == day))
    if hit.height == 0:
        return None
    value = hit["close"][0]
    if value is None:
        raise RuntimeError(f"{symbol} {day}: null close")
    return float(value)


def nifty_close_on(panel: pl.DataFrame, day: dt.date) -> float:
    hit = panel.filter(pl.col("date") == day)
    if hit.height == 0:
        raise RuntimeError(f"{day}: date missing from panel")
    value = hit["nifty_close"][0]
    if value is None:
        raise RuntimeError(f"{day}: null nifty_close")
    return float(value)


def residual_bps(start_px: float, end_px: float, start_n: float, end_n: float) -> float:
    stock_ret = end_px / start_px - 1.0
    nifty_ret = end_n / start_n - 1.0
    return (stock_ret - nifty_ret) * BPS


def window_residual_bps(
    panel: pl.DataFrame,
    symbol: str,
    start: dt.date,
    end: dt.date,
) -> float | None:
    """Residual over [start close, end close]. None if a close is absent.

    Does not interpolate.
    """
    start_px = close_on(panel, symbol, start)
    end_px = close_on(panel, symbol, end)
    if start_px is None or end_px is None:
        return None
    return residual_bps(
        start_px,
        end_px,
        nifty_close_on(panel, start),
        nifty_close_on(panel, end),
    )
