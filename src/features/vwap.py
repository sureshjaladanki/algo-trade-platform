import polars as pl


def add_vwap(df: pl.DataFrame) -> pl.DataFrame:
    """
    Adds 'vwap' (cumulative VWAP per trading day) and 'close_vwap_zscore'
    (z-score of close relative to cumulative VWAP).

    Requires the 'trading_day' column to be present.
    """
    # VWAP = cumulative sum(Close * Volume) / cumulative sum(Volume)
    df = df.with_columns([
        (pl.col("close") * pl.col("volume")).alias("price_volume")
    ])

    df = df.with_columns([
        (pl.col("price_volume").cum_sum().over("trading_day") /
         pl.col("volume").cum_sum().over("trading_day")).alias("vwap")
    ])

    # Standard Deviation of VWAP (Cumulative std dev of price around VWAP)
    df = df.with_columns([
        (pl.col("volume") * (pl.col("close") - pl.col("vwap"))**2).alias("vol_price_diff_sq")
    ])
    df = df.with_columns([
        (pl.col("vol_price_diff_sq").cum_sum().over("trading_day") /
         pl.col("volume").cum_sum().over("trading_day")).sqrt().alias("vwap_std")
    ])
    df = df.with_columns([
        ((pl.col("close") - pl.col("vwap")) / pl.col("vwap_std")).alias("close_vwap_zscore")
    ])

    # Drop intermediate columns
    df = df.drop(["price_volume", "vol_price_diff_sq", "vwap_std"])
    return df
