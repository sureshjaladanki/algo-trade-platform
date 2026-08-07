"""NSE session masks for Tier 2 Horizon entries / MIS-safe exits."""

import datetime as dt
import warnings

import polars as pl

from src.regime.intraday import NSE_OPEN_BLEED_BAR

# 15m ``date`` is bar-end (close time). Same physical candles as the old
# bar-start cutoffs, shifted +15m.
# Long: last entry 14:15 → H=4 exit stamp 15:15.
# Short: last entry 14:00 → earlier flatten / squeeze buffer.
LONG_LAST_ENTRY = dt.time(14, 15)
SHORT_LAST_ENTRY = dt.time(14, 0)

# Two MIS clocks (do not conflate):
# - Wall-clock: live / 1m flatten before broker ~15:15 square-off.
MIS_FLAT_BY = dt.time(15, 0)
# - 15m bar-end stamp of the last allowed exit candle (interval 15:00–15:15).
MIS_EXIT_BAR_END = dt.time(15, 15)


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
