import polars as pl


def add_relative_volume(df: pl.DataFrame, datetime_col: str = "timestamp", period: int = 14) -> pl.DataFrame:
    """
    Adds 'rvol' (volume / rel_vol) where rel_vol is the average volume for the
    same minute_of_day over the previous `period` days.

    Requires the 'minute_of_day' column to be present.
    """
    # We shift by 1 day to avoid including today's volume. Since we are grouped by minute_of_day,
    # shift(1) gets the previous day's volume for this specific minute.
    df = df.with_columns(
        pl.col("volume").sort_by(datetime_col).shift(1).rolling_mean(window_size=period).over("minute_of_day").alias("rel_vol")
    )
    df = df.with_columns(
        (pl.col("volume") / pl.col("rel_vol")).alias("rvol")
    )
    # rel_vol can be 0 on illiquid minutes -> division yields +/-inf.
    # Replace with NaN so XGBoost can route it through its missing-value branch.
    df = df.with_columns(
        pl.when(pl.col("rvol").is_infinite())
          .then(float("nan"))
          .otherwise(pl.col("rvol"))
          .alias("rvol")
    )
    df = df.drop("rel_vol")
    return df
