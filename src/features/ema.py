import polars as pl


def add_ema(
    df: pl.DataFrame,
    *,
    fast_period: int = 8,
    slow_period: int = 21,
) -> pl.DataFrame:
    """
    Adds EMA-derived features for fast and slow spans:
    - 'fast_ema_slope': percentage change of the fast EMA vs prior bar
    - 'close_slow_ema_pct': percent difference of close vs slow EMA
    - 'fast_slow_ema_ratio': fast EMA divided by slow EMA
    """
    fast_ema = f"ema_{fast_period}"
    slope_col = "fast_ema_slope"
    slow_ema = f"ema_{slow_period}"
    pct_col = "close_slow_ema_pct"
    ratio_col = "fast_slow_ema_ratio"

    df = df.with_columns(
        pl.col("close").ewm_mean(span=fast_period, adjust=False).alias(fast_ema),
        pl.col("close").ewm_mean(span=slow_period, adjust=False).alias(slow_ema),
    )
    df = df.with_columns(
        (pl.col(fast_ema) / pl.col(fast_ema).shift(1) - 1.0).alias(slope_col),
        ((pl.col("close") - pl.col(slow_ema)) / pl.col(slow_ema)).alias(pct_col),
        ((pl.col(fast_ema) / pl.col(slow_ema)) - 1.0).alias(ratio_col),
    )
    df = df.with_columns(
        pl.when(pl.col(slope_col).is_infinite()).then(None).otherwise(pl.col(slope_col)).alias(slope_col),
        pl.when(pl.col(pct_col).is_infinite()).then(None).otherwise(pl.col(pct_col)).alias(pct_col),
        pl.when(pl.col(ratio_col).is_infinite()).then(None).otherwise(pl.col(ratio_col)).alias(ratio_col),
    )
    # df = df.drop(fast_ema, slow_ema)

    return df
  