import polars as pl


def add_zscore(df: pl.DataFrame, period: int = 5) -> pl.DataFrame:
    """
    Z-score on `close`: rolling Z-score over `period` bars.

    Pure indicator: operates on the input dataframe's 'close' column.
    Output column: `zscore`.
    """
    df = df.with_columns([
        pl.col("close").rolling_mean(window_size=period).alias("close_mean"),
        pl.col("close").rolling_std(window_size=period).alias("close_std")
    ])
    df = df.with_columns(
        ((pl.col("close") - pl.col("close_mean")) / pl.col("close_std")).alias("zscore")
    )
    df = df.with_columns(
        pl.when(pl.col("zscore").is_infinite())
          .then(None)
          .otherwise(pl.col("zscore"))
          .alias("zscore")
    )
    return df.drop(["close_mean", "close_std"])
