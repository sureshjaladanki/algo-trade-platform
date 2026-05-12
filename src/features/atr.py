import polars as pl


def add_natr(
    df: pl.DataFrame,
    datetime_col: str = "timestamp",
    period: int = 8,
    zscore_period: int = 3,
) -> pl.DataFrame:
    """
    Adds 'natr' (Normalized SMA of true range over `period` bars) and 'natr_zscore'
    (Z-score of NATR over its `zscore_period` bars).

    The first 5m bar of each calendar trading day uses HL-only true range so
    the session open gap does not inflate TR.

    Timeperiod-agnostic: generic column names. The caller may rename to a
    timeframe-specific scheme (e.g. 'natr_5m', 'natr_5m_zscore').
    """
    df = df.with_columns(pl.col(datetime_col).dt.date().alias("trading_day"))
    df = df.with_columns(pl.col("close").shift(1).alias("prev_close"))
    df = df.with_columns(
        (
            pl.col("trading_day").shift(1).is_null()
            | (pl.col("trading_day") != pl.col("trading_day").shift(1))
        ).alias("is_first_bar_of_day")
    )
    hl_range = pl.col("high") - pl.col("low")
    standard_tr = pl.max_horizontal(
        hl_range,
        (pl.col("high") - pl.col("prev_close")).abs(),
        (pl.col("low") - pl.col("prev_close")).abs(),
    )
    df = df.with_columns(
        pl.when(pl.col("is_first_bar_of_day"))
        .then(hl_range)
        .otherwise(standard_tr)
        .alias("tr")
    )
    df = df.with_columns((pl.col("tr").rolling_mean(window_size=period) / pl.col("close")).alias("natr"))
    df = df.with_columns([
        pl.col("natr").rolling_mean(window_size=zscore_period).alias("natr_mean"),
        pl.col("natr").rolling_std(window_size=zscore_period).alias("natr_std")
    ])
    df = df.with_columns(
        ((pl.col("natr") - pl.col("natr_mean")) / pl.col("natr_std")).alias("natr_zscore")
    )
    df = df.with_columns(
        pl.when(pl.col("natr_zscore").is_infinite()).then(float("nan")).otherwise(pl.col("natr_zscore")).alias("natr_zscore")
    )
    return df.drop("trading_day", "prev_close", "is_first_bar_of_day", "tr", "natr_mean", "natr_std")
