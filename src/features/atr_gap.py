import polars as pl


def add_atr_gap(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    """
    Adds 'gap_atr' (today's open gap from previous day close, normalized by
    the previous day's `period`-day ATR).

    Requires the 'trading_day' column. Drops the intermediate previous-day
    columns at the end.
    """
    # Compute daily metrics first
    df_daily = df.group_by("trading_day").agg([
        pl.col("high").max().alias("daily_high"),
        pl.col("low").min().alias("daily_low"),
        pl.col("close").last().alias("daily_close")
    ]).sort("trading_day")

    # Compute True Range and ATR
    df_daily = df_daily.with_columns([
        pl.col("daily_close").shift(1).alias("prev_daily_close")
    ])

    df_daily = df_daily.with_columns([
        pl.max_horizontal(
            pl.col("daily_high") - pl.col("daily_low"),
            (pl.col("daily_high") - pl.col("prev_daily_close")).abs(),
            (pl.col("daily_low") - pl.col("prev_daily_close")).abs()
        ).alias("tr")
    ])

    df_daily = df_daily.with_columns([
        pl.col("tr").rolling_mean(window_size=period).alias("daily_atr")
    ])

    # Shift to get previous day's values for today
    df_daily = df_daily.with_columns([
        pl.col("daily_close").shift(1).alias("prev_day_close"),
        pl.col("daily_atr").shift(1).alias("prev_day_atr")
    ])

    # Join back to 1m data
    df = df.join(df_daily.select(["trading_day", "prev_day_close", "prev_day_atr"]), on="trading_day", how="left")
    df = df.with_columns(
        ((pl.col("close") - pl.col("prev_day_close")) / pl.col("prev_day_atr")).alias("gap_atr")
    )
    df = df.with_columns(
        pl.when(pl.col("gap_atr").is_infinite()).then(None).otherwise(pl.col("gap_atr")).alias("gap_atr")
    )
    # prev_day_atr can be 0 on a flat day -> division yields +/-inf.
    # Replace with NaN so XGBoost can route it through its missing-value branch.
    df = df.with_columns(
        pl.when(pl.col("gap_atr").is_infinite())
          .then(float("nan"))
          .otherwise(pl.col("gap_atr"))
          .alias("gap_atr")
    )

    # Drop intermediate columns
    df = df.drop(["prev_day_close", "prev_day_atr"])
    return df
