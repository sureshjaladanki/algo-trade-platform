import polars as pl


def add_ema(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    """
    Adds 'ema_{period}' (EMA of close, span=period) and
    'close_ema_{period}_pct' (percent difference of close vs EMA).

    The output column names embed the period so multiple EMAs can coexist
    on the same dataframe.
    """
    ema_col = f"ema_{period}"
    pct_col = f"close_ema_{period}_pct"

    df = df.with_columns(
        pl.col("close").ewm_mean(span=period, adjust=False).alias(ema_col)
    )
    df = df.with_columns(
        ((pl.col("close") - pl.col(ema_col)) / pl.col(ema_col)).alias(pct_col)
    )
    return df
