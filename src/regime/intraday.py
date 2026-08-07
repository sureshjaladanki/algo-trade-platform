"""NSE session masks for Tier 1 intraday regime."""

import datetime as dt

import polars as pl

from .types import IntradayRegime

# 15m ``date`` is bar-end (close time). See ``resample_15m``.
# 09:30 stamp = 09:15–09:30 call-auction bleed candle.
NSE_OPEN_BLEED_BAR = dt.time(9, 30)
# Watch window wall 14:30–15:15 → bar-end stamps 14:45, 15:00, 15:15.
NSE_WATCH_START = dt.time(14, 45)
NSE_WATCH_END = dt.time(15, 30)


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

# Hard rules to override intraday regime.
def override_intraday_regime(df: pl.DataFrame) -> pl.DataFrame:
    """
    Pipeline hard rule: label open-auction bleed bars as intraday NO_TRADE.

    Applied after HMM predict on gated rows (model never sees these bars).
    Requires `intraday_regime` / `intraday_regime_raw` and a datetime `date` column.
    """
    no_trade = IntradayRegime.NO_TRADE.value
    return df.with_columns(
        pl.when(open_auction_bleed_expr('date'))
        .then(pl.lit(no_trade))
        .otherwise(pl.col("intraday_regime_raw"))
        .alias("intraday_regime_raw"),
        pl.when(open_auction_bleed_expr('date'))
        .then(pl.lit(no_trade))
        .otherwise(pl.col("intraday_regime"))
        .alias("intraday_regime"),
    )
