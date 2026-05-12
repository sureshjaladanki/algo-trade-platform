import polars as pl
from polars_ta.prefix.tdx import ts_RSI


def add_rsi(df: pl.DataFrame, period: int = 14, zscore_period: int = 5) -> pl.DataFrame:
    """
    Adds 'rsi' (RSI of close with `period`-bar lookback) and 'rsi_zscore'
    (Z-score of RSI over its `zscore_period`).

    Timeperiod-agnostic: produces generic column names regardless of the bar
    interval of the input dataframe. The caller is responsible for renaming
    the columns to a timeframe-specific scheme (e.g. 'rsi_5m') if desired.

    Pure: operates only on the input dataframe's 'close' column.
    """
    df = df.with_columns(
        ts_RSI(pl.col("close"), period).alias("rsi")
    )
    df = df.with_columns([
        pl.col("rsi").rolling_mean(window_size=zscore_period).alias("rsi_mean"),
        pl.col("rsi").rolling_std(window_size=zscore_period).alias("rsi_std")
    ])
    df = df.with_columns(
        ((pl.col("rsi") - pl.col("rsi_mean")) / pl.col("rsi_std")).alias("rsi_zscore")
    )
    df = df.with_columns(
        pl.when(pl.col("rsi_zscore").is_infinite()).then(float("nan")).otherwise(pl.col("rsi_zscore")).alias("rsi_zscore")
    )
    df = df.drop(["rsi_mean", "rsi_std"])
    return df
