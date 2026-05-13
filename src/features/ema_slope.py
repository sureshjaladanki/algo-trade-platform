import polars as pl

def add_ema_slope(df: pl.DataFrame, period: int = 5) -> pl.DataFrame:
    """
    Adds 'ema_slope_{period}' which measures the percentage change of the EMA
    from the previous bar.
    """
    ema_col = f"ema_{period}"
    slope_col = f"ema_slope_{period}"
    
    df = df.with_columns(
        pl.col("close").ewm_mean(span=period, adjust=False).alias(ema_col)
    )
    df = df.with_columns(
        (pl.col(ema_col) / pl.col(ema_col).shift(1) - 1.0).alias(slope_col)
    )
    df = df.drop(ema_col)
    
    return df
