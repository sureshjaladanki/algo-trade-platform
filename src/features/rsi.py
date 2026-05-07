import polars as pl
from polars_ta.prefix.tdx import ts_RSI


def add_rsi(df: pl.DataFrame, period: int = 14, roc_period: int = 5) -> pl.DataFrame:
    """
    Adds 'rsi' (RSI of close with `period`-bar lookback) and 'rsi_roc'
    (rate of change as the difference of RSI from its `roc_period` SMA).

    Timeperiod-agnostic: produces generic column names regardless of the bar
    interval of the input dataframe. The caller is responsible for renaming
    the columns to a timeframe-specific scheme (e.g. 'rsi_5m') if desired.

    Pure: operates only on the input dataframe's 'close' column.
    """
    df = df.with_columns(
        ts_RSI(pl.col("close"), period).alias("rsi")
    )
    df = df.with_columns(
        (pl.col("rsi") - pl.col("rsi").rolling_mean(window_size=roc_period)).alias("rsi_roc")
    )
    return df
