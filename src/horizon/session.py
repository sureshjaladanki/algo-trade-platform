"""NSE session masks for Tier 2 Horizon entries / MIS-safe exits."""

import datetime as dt

import polars as pl

from src.regime.session import NSE_OPEN_BLEED_BAR

# Bar timestamps are bar *starts* (group_by_dynamic convention).
# Long: last entry 14:00 → exit at 15:00 for H=4.
# Short: last entry 13:45 → earlier flatten / squeeze buffer.
LONG_LAST_ENTRY = dt.time(14, 0)
SHORT_LAST_ENTRY = dt.time(13, 45)
# Positions flat by ~15:00 (before broker ~15:15 square-off).
MIS_FLAT_BY = dt.time(15, 0)


def auction_bleed_entry_expr(time_col: str = "time_only") -> pl.Expr:
    """True on the 09:15–09:30 call-auction bleed bar (bar start 09:15)."""
    return pl.col(time_col) == NSE_OPEN_BLEED_BAR


def long_entry_ok_expr(time_col: str = "time_only") -> pl.Expr:
    t = pl.col(time_col)
    return (t > NSE_OPEN_BLEED_BAR) & (t <= LONG_LAST_ENTRY)


def short_entry_ok_expr(time_col: str = "time_only") -> pl.Expr:
    t = pl.col(time_col)
    return (t > NSE_OPEN_BLEED_BAR) & (t <= SHORT_LAST_ENTRY)
