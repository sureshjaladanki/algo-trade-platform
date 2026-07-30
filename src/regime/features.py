import polars as pl
import numpy as np

def calculate_daily_features(nifty_df: pl.DataFrame, vix_df: pl.DataFrame, breadth_df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates Daily Regime features.
    
    Inputs:
    - nifty_df: EOD Nifty data (date, open, high, low, close)
    - vix_df: EOD India VIX data (date, close)
    - breadth_df: EOD Breadth data (date, pct_above_20dma)
    """
    
    # Calculate Nifty features
    nifty = nifty_df.sort("date")
    nifty = nifty.with_columns(
        ema20=pl.col("close").ewm_mean(span=20, ignore_nulls=True),
        prev_close=pl.col("close").shift(1),
        tr=pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - pl.col("close").shift(1)).abs(),
            (pl.col("low") - pl.col("close").shift(1)).abs()
        )
    )
    nifty = nifty.with_columns(
        atr14=pl.col("tr").rolling_mean(14),
        nifty_trend=(pl.col("close") - pl.col("ema20")) / pl.col("ema20") * 100,
        gap=(pl.col("open") - pl.col("prev_close"))
    )
    nifty = nifty.with_columns(
        shock=pl.col("gap") / pl.col("atr14")
    )
    
    # Calculate VIX features
    vix = vix_df.sort("date").select([
        pl.col("date"),
        pl.col("close").alias("vix_close"),
        pl.col("close").rolling_median(60).alias("vix_median_60d"),
        (pl.col("close") / pl.col("close").shift(1) - 1.0).alias("vol_regime_delta")
    ])
    vix = vix.with_columns(
        vol_regime_ratio=pl.col("vix_close") / pl.col("vix_median_60d")
    )
    
    # Breadth features
    breadth = breadth_df.select([
        pl.col("date"),
        pl.col("pct_above_20dma").alias("breadth_div")
    ])
    
    # Join everything
    daily_features = nifty.join(vix, on="date", how="left").join(breadth, on="date", how="left")
    
    return daily_features.select([
        "date", "nifty_trend", "vol_regime_ratio", "vol_regime_delta", "shock", "breadth_div"
    ])


def calculate_intraday_features(intraday_df: pl.DataFrame, daily_df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates Intraday Regime HMM emissions with TOD normalization.
    
    Inputs:
    - intraday_df: 15m Nifty data (datetime, date, time, open, high, low, close, volume, vwap)
    - daily_df: EOD Nifty data for ATR scaling (date, atr14)
    """
    df = intraday_df.sort("datetime").join(daily_df.select(["date", "atr14"]), on="date", how="left")
    
    df = df.with_columns(
        log_ret=np.log(pl.col("close") / pl.col("close").shift(1)),
        range_pct=(pl.col("high") - pl.col("low")) / pl.col("close"),
        vwap_dist_raw=(pl.col("close") - pl.col("vwap")) / pl.col("vwap")
    )
    
    # Compute TOD aggregations using expanding or rolling windows in practice, 
    # but for simplicity here we compute historical global TOD baseline.
    tod_stats = df.group_by("time").agg(
        r_15_std=pl.col("log_ret").std(),
        rv_15_mean=pl.col("range_pct").mean(),
        vol_mean=pl.col("volume").mean(),
        vol_std=pl.col("volume").std()
    )
    
    df = df.join(tod_stats, on="time", how="left")
    
    # Downweight 9:15-9:30 bar and handle 15:15 bar if needed.
    
    df = df.with_columns(
        r_15=pl.col("log_ret") / pl.col("r_15_std"),
        rv_15=pl.col("range_pct") / pl.col("rv_15_mean"),
        volz_15=(pl.col("volume") - pl.col("vol_mean")) / pl.col("vol_std"),
        # VWAP dist scaled by Daily ATR% 
        vwap_dist=pl.col("vwap_dist_raw") / (pl.col("atr14") / pl.col("close"))
    )
    
    return df.select([
        "datetime", "date", "time", "r_15", "rv_15", "volz_15", "vwap_dist"
    ])
