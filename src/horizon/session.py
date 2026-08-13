"""NSE session masks for Tier 2 Horizon entries / MIS-safe exits."""

import datetime as dt
import warnings

import polars as pl

from src.regime.intraday import NSE_OPEN_BLEED_BAR
from src.utils.eval_common import BAR_MINUTES, H_BARS

# Short last entry is one bar earlier than Long at the same H (flatten / squeeze buffer).
SHORT_ENTRY_BUFFER_BARS = 1

# Two MIS clocks (do not conflate):
# - Wall-clock: live / 1m flatten before broker ~15:15 square-off.
MIS_FLAT_BY = dt.time(15, 0)
# - 15m bar-end stamp of the last allowed exit candle (interval 15:00–15:15).
MIS_EXIT_BAR_END = dt.time(15, 15)


def last_entry_for_horizon(horizon_bars: int, *, short: bool = False) -> dt.time:
    """Latest bar-end entry so the H-bar exit stamp stays ≤ ``MIS_EXIT_BAR_END``.

    Long: exit = entry + ``horizon_bars``.
    Short: same plus ``SHORT_ENTRY_BUFFER_BARS`` (one bar earlier than Long).
    """
    offset_bars = horizon_bars + (SHORT_ENTRY_BUFFER_BARS if short else 0)
    exit_dt = dt.datetime.combine(dt.date(2000, 1, 1), MIS_EXIT_BAR_END)
    entry_dt = exit_dt - dt.timedelta(minutes=BAR_MINUTES * offset_bars)
    return entry_dt.time()


# 15m ``date`` is bar-end (close time).
# H=6: Long 13:45 → exit 15:15; Short 13:30 (one-bar buffer).
LONG_LAST_ENTRY = last_entry_for_horizon(H_BARS, short=False)
SHORT_LAST_ENTRY = last_entry_for_horizon(H_BARS, short=True)


def auction_bleed_entry_expr(time_col: str = "time_only") -> pl.Expr:
    """True on the 09:15–09:30 call-auction bleed bar (bar-end stamp 09:30).

    Deprecated: unused. Prefer ``long_entry_ok_expr`` / ``short_entry_ok_expr``,
    which already exclude the bleed bar via ``t > NSE_OPEN_BLEED_BAR``.
    """
    warnings.warn(
        "auction_bleed_entry_expr is deprecated; "
        "long_entry_ok_expr / short_entry_ok_expr already exclude the bleed bar",
        DeprecationWarning,
        stacklevel=2,
    )
    return pl.col(time_col) == NSE_OPEN_BLEED_BAR


def long_entry_ok_expr(time_col: str = "time_only") -> pl.Expr:
    t = pl.col(time_col)
    return (t > NSE_OPEN_BLEED_BAR) & (t <= LONG_LAST_ENTRY)


def short_entry_ok_expr(time_col: str = "time_only") -> pl.Expr:
    t = pl.col(time_col)
    return (t > NSE_OPEN_BLEED_BAR) & (t <= SHORT_LAST_ENTRY)
