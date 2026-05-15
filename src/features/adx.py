import polars as pl
from polars_ta.prefix.tdx import ts_ADX, ts_MINUS_DI, ts_PLUS_DI


def add_adx(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    """
    Adds 'adx' (ADX), 'plus_di' (+DI), and 'minus_di' (-DI) from high/low/close
    with `period`-bar lookback.

    Timeperiod-agnostic: produces generic column names regardless of the bar
    interval of the input dataframe. The caller is responsible for renaming
    the columns to a timeframe-specific scheme (e.g. 'adx_5m') if desired.

    Pure: operates only on the input dataframe's 'high', 'low', 'close' columns.
    """
    df = df.with_columns(
        ts_ADX(pl.col("high"), pl.col("low"), pl.col("close"), period).alias("adx"),
        ts_PLUS_DI(pl.col("high"), pl.col("low"), pl.col("close"), period).alias("plus_di"),
        ts_MINUS_DI(pl.col("high"), pl.col("low"), pl.col("close"), period).alias("minus_di")
    )
    df = df.with_columns(
        ((pl.col("plus_di") - pl.col("minus_di")) / (pl.col("plus_di") + pl.col("minus_di"))).alias("di_diff"),
    )
    df = df.drop(["plus_di", "minus_di"])

    return df
