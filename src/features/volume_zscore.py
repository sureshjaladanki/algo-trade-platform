import polars as pl


def add_volume_zscore(df: pl.DataFrame, period: int = 20) -> pl.DataFrame:
    """
    Adds 'vol_z_score' (rolling `period`-bar z-score of volume).
    """
    df = df.with_columns([
        pl.col("volume").rolling_mean(window_size=period).alias("vol_mean"),
        pl.col("volume").rolling_std(window_size=period).alias("vol_std")
    ])
    df = df.with_columns(
        ((pl.col("volume") - pl.col("vol_mean")) / pl.col("vol_std")).alias("vol_z_score")
    )
    df = df.drop(["vol_mean", "vol_std"])
    return df
