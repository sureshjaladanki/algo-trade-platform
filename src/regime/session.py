"""NSE session masks for Tier 1 intraday regime."""

import datetime as dt

import polars as pl

# Bar timestamps from group_by_dynamic are bar *starts*.
# 09:15 bar = 09:15–09:30 call-auction bleed.
NSE_OPEN_BLEED_BAR = dt.time(9, 15)
# Watch window 14:30–15:15 → bars 14:30, 14:45, 15:00.
NSE_WATCH_START = dt.time(14, 30)
NSE_WATCH_END = dt.time(15, 15)


def open_auction_bleed_expr(datetime_col: str = "date") -> pl.Expr:
    return pl.col(datetime_col).dt.time() == NSE_OPEN_BLEED_BAR


def session_watch_expr(datetime_col: str = "date") -> pl.Expr:
    t = pl.col(datetime_col).dt.time()
    return (t >= NSE_WATCH_START) & (t < NSE_WATCH_END)


def with_session_flags(df: pl.DataFrame, datetime_col: str = "date") -> pl.DataFrame:
    """Attach open-auction bleed and afternoon watch flags."""
    return df.with_columns(
        open_auction_bleed=open_auction_bleed_expr(datetime_col),
        session_watch=session_watch_expr(datetime_col),
        # Actionable confidence: open bleed is low-confidence for sleeve routing.
        intraday_low_confidence=open_auction_bleed_expr(datetime_col),
    )


def exclude_open_auction_bleed(df: pl.DataFrame, datetime_col: str = "date") -> pl.DataFrame:
    """Drop 09:15–09:30 bars (call auction bleed) from HMM fit/score/decode."""
    return df.filter(~open_auction_bleed_expr(datetime_col))
