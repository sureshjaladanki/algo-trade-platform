import polars as pl
from polars_ta.prefix.tdx import ts_ADX


def add_adx(df: pl.DataFrame, period: int = 14, roc_period: int = 5) -> pl.DataFrame:
    """
    Adds 'adx' (ADX from high/low/close with `period`-bar lookback) and
    'adx_roc' (rate of change as the difference of ADX from its
    `roc_period` SMA).

    Timeperiod-agnostic: produces generic column names regardless of the bar
    interval of the input dataframe. The caller is responsible for renaming
    the columns to a timeframe-specific scheme (e.g. 'adx_5m') if desired.

    Pure: operates only on the input dataframe's 'high', 'low', 'close' columns.
    """
    df = df.with_columns(
        ts_ADX(pl.col("high"), pl.col("low"), pl.col("close"), period).alias("adx")
    )
    df = df.with_columns(
        pl.col("adx")
        .pct_change()
        .shift(1)
        .rolling_mean(window_size=roc_period)
        .alias("adx_roc")
    )
    return df
