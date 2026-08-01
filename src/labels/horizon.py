import polars as pl

def calculate_horizon_labels(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    horizon_bars: int = 4
) -> pl.DataFrame:
    """
    Calculates forward excess return labels for Tier 2 models.
    
    Inputs:
    - stock_df: 15m stock data (datetime, close, symbol)
    - nifty_df: 15m Nifty data (datetime, close)
    - horizon_bars: Number of bars for forward return (default 4 = 60m)
    
    Returns:
    - DataFrame with forward returns and excess returns.
    """
    stock_df = stock_df.sort(["symbol", "datetime"])
    nifty_df = nifty_df.sort("datetime")
    
    # Join Nifty to Stock
    df = stock_df.join(
        nifty_df.select(["datetime", pl.col("close").alias("nifty_close")]),
        on="datetime", how="left"
    )
    
    # Forward returns
    df = df.with_columns(
        fwd_stock_ret=(pl.col("close").shift(-horizon_bars) / pl.col("close") - 1).over("symbol"),
        fwd_nifty_ret=(pl.col("nifty_close").shift(-horizon_bars) / pl.col("nifty_close") - 1).over("symbol")
    )
    
    # Excess return
    df = df.with_columns(
        fwd_excess_ret=pl.col("fwd_stock_ret") - pl.col("fwd_nifty_ret")
    )
    
    # Filter out entries that cross MIS square-off (15:15)
    # If horizon is 4 bars (60m), last entry is 14:15. Wait, 14:15 + 60m = 15:15.
    # So time_only <= 14:15.
    # Let's calculate the time of the exit bar.
    df = df.with_columns(
        exit_time=pl.col("datetime").shift(-horizon_bars).dt.time().over("symbol"),
        exit_date=pl.col("datetime").shift(-horizon_bars).dt.date().over("symbol"),
        entry_date=pl.col("datetime").dt.date()
    )
    
    # Invalidate labels if the exit crosses to the next day
    df = df.with_columns(
        valid_label=pl.when(
            (pl.col("exit_date") == pl.col("entry_date")) & 
            (pl.col("exit_time") <= pl.time(15, 15))
        ).then(True).otherwise(False)
    )
    
    # Set invalid labels to null
    df = df.with_columns(
        fwd_excess_ret=pl.when(pl.col("valid_label")).then(pl.col("fwd_excess_ret")).otherwise(None)
    )
    
    return df.select(["symbol", "datetime", "fwd_excess_ret", "valid_label"])
