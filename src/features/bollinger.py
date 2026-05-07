import polars as pl


def add_bollinger(df: pl.DataFrame, period: int = 20) -> pl.DataFrame:
    """
    Adds 'bb_pct_b' (Bollinger %B) using a rolling window of `period`
    and 2 standard-deviation bands.
    """
    df = df.with_columns([
        pl.col("close").rolling_mean(window_size=period).alias("bb_mean"),
        pl.col("close").rolling_std(window_size=period).alias("bb_std")
    ])
    df = df.with_columns([
        (pl.col("bb_mean") + 2 * pl.col("bb_std")).alias("bb_upper"),
        (pl.col("bb_mean") - 2 * pl.col("bb_std")).alias("bb_lower")
    ])
    df = df.with_columns(
        ((pl.col("close") - pl.col("bb_lower")) / (pl.col("bb_upper") - pl.col("bb_lower"))).alias("bb_pct_b")
    )
    df = df.drop(["bb_mean", "bb_std", "bb_upper", "bb_lower"])
    return df
