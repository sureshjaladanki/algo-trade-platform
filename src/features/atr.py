import polars as pl


def add_atr(
    df: pl.DataFrame,
    datetime_col: str = "timestamp",
    period: int = 8,
) -> pl.DataFrame:
    """
    Adds ``atr`` (SMA of true range over ``period`` bars).

    The first bar of each calendar trading day uses HL-only true range so the
    session open gap does not inflate TR.

    Timeframe-agnostic column names; callers may rename (e.g. ``atr_5m``).
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
    df = df.with_columns(pl.col("tr").rolling_mean(window_size=period).alias("atr"))
    return df.drop("trading_day", "prev_close", "is_first_bar_of_day", "tr")
