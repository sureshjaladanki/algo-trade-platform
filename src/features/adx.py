import polars as pl
from polars_ta.prefix.tdx import ts_ADX


def add_adx(df: pl.DataFrame, period: int = 14, zscore_period: int = 5) -> pl.DataFrame:
    """
    Adds 'adx' (ADX from high/low/close with `period`-bar lookback) and
    'adx_zscore' (Z-score of ADX over its `zscore_period`).

    Timeperiod-agnostic: produces generic column names regardless of the bar
    interval of the input dataframe. The caller is responsible for renaming
    the columns to a timeframe-specific scheme (e.g. 'adx_5m') if desired.

    Pure: operates only on the input dataframe's 'high', 'low', 'close' columns.
    """
    df = df.with_columns(
        ts_ADX(pl.col("high"), pl.col("low"), pl.col("close"), period).alias("adx")
    )
    df = df.with_columns([
        pl.col("adx").rolling_mean(window_size=zscore_period).alias("adx_mean"),
        pl.col("adx").rolling_std(window_size=zscore_period).alias("adx_std")
    ])
    df = df.with_columns(
        ((pl.col("adx") - pl.col("adx_mean")) / pl.col("adx_std")).alias("adx_zscore")
    )
    df = df.with_columns(
        pl.when(pl.col("adx_zscore").is_infinite()).then(float("nan")).otherwise(pl.col("adx_zscore")).alias("adx_zscore")
    )
    df = df.drop(["adx_mean", "adx_std"])
    return df
