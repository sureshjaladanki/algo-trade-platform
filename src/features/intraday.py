import polars as pl
from .core import log_return, pct_distance, z_score, range_pct, vwap, atr

def calculate_intraday_features(df: pl.DataFrame, daily_df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates Intraday Regime HMM emissions with TOD normalization by composing core generic features.
    
    Inputs:
    - df: 15m Nifty data (date, open, high, low, close, volume)
    - daily_df: EOD Nifty data for ATR scaling (date, open, high, low, close)
    """
    # 1. Parse dates
    df = df.with_columns(
        datetime=pl.col("date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S") 
                 if df["date"].dtype == pl.Utf8 else pl.col("date").cast(pl.Datetime)
    ).with_columns(
        date_only=pl.col("datetime").dt.date(),
        time_only=pl.col("datetime").dt.time()
    )
    
    daily_df = daily_df.with_columns(
        date=pl.col("date").str.strptime(pl.Date, "%Y-%m-%d") 
             if daily_df["date"].dtype == pl.Utf8 else pl.col("date").cast(pl.Date)
    )

    # 2. Calculate daily ATR14 and shift by 1 to prevent lookahead bias intraday
    daily_df = daily_df.sort("date").with_columns(
        prev_atr14=atr("high", "low", "close", window=14).shift(1)
    )
    
    # 3. Simple left join on date
    df = df.join(daily_df.select(["date", "prev_atr14"]), left_on="date_only", right_on="date", how="left")
    
    # 4. Calculate Intraday VWAP (Session VWAP resets daily)
    df = df.sort("datetime").with_columns(
        vwap=vwap("high", "low", "close", "volume").over("date_only")
    )
    
    # 5. Calculate base features
    df = df.with_columns(
        log_ret=log_return("close"),
        range_pct=range_pct("high", "low", "close"),
        vwap_dist_raw=pct_distance("close", "vwap")
    )
    
    # 6. Compute TOD aggregations
    tod_stats = df.group_by("time_only").agg(
        r_15_std=pl.col("log_ret").std(),
        rv_15_mean=pl.col("range_pct").mean(),
        vol_mean=pl.col("volume").mean(),
        vol_std=pl.col("volume").std()
    )
    
    df = df.join(tod_stats, on="time_only", how="left")
    
    # 7. Final normalized features
    df = df.with_columns(
        r_15=pl.col("log_ret") / pl.col("r_15_std"),
        rv_15=pl.col("range_pct") / pl.col("rv_15_mean"),
        volz_15=z_score("volume", "vol_mean", "vol_std"),
        # VWAP dist scaled by Previous Day's ATR% to avoid lookahead
        vwap_dist=pl.col("vwap_dist_raw") / (pl.col("prev_atr14") / pl.col("close"))
    )
    
    return df.select([
        "datetime",
        pl.col("date_only").alias("date"),
        pl.col("time_only").alias("time"),
        "r_15", "rv_15", "volz_15", "vwap_dist"
    ])
