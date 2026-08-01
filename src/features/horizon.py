import polars as pl
import numpy as np

def calculate_horizon_features(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    sector_df: pl.DataFrame,
    daily_stock_df: pl.DataFrame,
    daily_nifty_df: pl.DataFrame
) -> pl.DataFrame:
    """
    Calculates Tier 2 Long and Short features.
    
    Inputs:
    - stock_df: 15m stock data (datetime, open, high, low, close, volume, symbol)
    - nifty_df: 15m Nifty data (datetime, close, r_15)
    - sector_df: 15m Sector data (datetime, close, sector)
    - daily_stock_df: EOD stock data (date, high, low, close, volume, symbol)
    - daily_nifty_df: EOD Nifty data (date, close)
    """
    # Ensure datetime sorting
    stock_df = stock_df.sort(["symbol", "datetime"])
    nifty_df = nifty_df.sort("datetime")
    if sector_df is not None:
        sector_df = sector_df.sort(["sector", "datetime"])
    daily_stock_df = daily_stock_df.sort(["symbol", "date"])
    daily_nifty_df = daily_nifty_df.sort("date")

    # 1. Daily features (rolling beta, trend strength, ADV rank, prev day high/low, etc.)
    # Join Nifty daily to Stock daily for beta
    daily_joined = daily_stock_df.join(
        daily_nifty_df.select(["date", pl.col("close").alias("nifty_close")]),
        on="date", how="left"
    )
    
    daily_joined = daily_joined.with_columns(
        stock_ret=pl.col("close").pct_change(),
        nifty_ret=pl.col("nifty_close").pct_change()
    )
    
    # Rolling beta 60d (covariance / variance)
    daily_joined = daily_joined.with_columns(
        cov_60d=pl.rolling_cov(pl.col("stock_ret"), pl.col("nifty_ret"), window_size=60).over("symbol"),
        var_60d=pl.col("nifty_ret").rolling_var(window_size=60)
    ).with_columns(
        rolling_beta_60d=pl.col("cov_60d") / pl.col("var_60d")
    )
    
    # 20d ADV
    daily_joined = daily_joined.with_columns(
        adv_20d=pl.col("volume").rolling_mean(window_size=20).over("symbol")
    )
    
    # ADV rank 20d (percentile within date across symbols)
    daily_joined = daily_joined.with_columns(
        adv_rank_20d=pl.col("adv_20d").rank(descending=False) / pl.count("symbol").over("date")
    )
    
    # Prev day high, low, close, ATR14
    daily_joined = daily_joined.with_columns(
        tr=pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - pl.col("close").shift(1)).abs(),
            (pl.col("low") - pl.col("close").shift(1)).abs()
        ).over("symbol")
    ).with_columns(
        atr14=pl.col("tr").rolling_mean(window_size=14).over("symbol")
    )
    
    daily_joined = daily_joined.with_columns(
        prev_high=pl.col("high").shift(1).over("symbol"),
        prev_low=pl.col("low").shift(1).over("symbol"),
        prev_atr14=pl.col("atr14").shift(1).over("symbol"),
        high_20d=pl.col("high").rolling_max(window_size=20).over("symbol"),
        high_52w=pl.col("high").rolling_max(window_size=252).over("symbol"),
    )
    
    # Trend strength daily (EMA20 slope proxy: close / EMA20 - 1)
    daily_joined = daily_joined.with_columns(
        ema20=pl.col("close").ewm_mean(span=20, adjust=False).over("symbol")
    ).with_columns(
        trend_strength_daily=(pl.col("close") / pl.col("ema20")) - 1.0
    )
    
    # 2. Intraday features
    # Calculate stock TOD normalized features
    stock_df = stock_df.with_columns(
        date_only=pl.col("datetime").dt.date(),
        time_only=pl.col("datetime").dt.time()
    )
    
    # Calculate log_ret, range_pct
    stock_df = stock_df.with_columns(
        log_ret=pl.col("close").log() - pl.col("close").shift(1).log().over("symbol"),
        range_pct=(pl.col("high") - pl.col("low")) / pl.col("close").shift(1).over("symbol")
    )
    
    # VWAP
    stock_df = stock_df.with_columns(
        typ_price=(pl.col("high") + pl.col("low") + pl.col("close")) / 3
    ).with_columns(
        cum_vol=pl.col("volume").cum_sum().over(["symbol", "date_only"]),
        cum_pv=(pl.col("typ_price") * pl.col("volume")).cum_sum().over(["symbol", "date_only"])
    ).with_columns(
        vwap=pl.col("cum_pv") / pl.col("cum_vol")
    )
    
    # TOD stats
    tod_stats = stock_df.group_by(["symbol", "time_only"]).agg(
        r_15_std=pl.col("log_ret").std(),
        rv_15_mean=pl.col("range_pct").mean(),
        vol_mean=pl.col("volume").mean(),
        vol_std=pl.col("volume").std()
    )
    
    stock_df = stock_df.join(tod_stats, on=["symbol", "time_only"], how="left")
    
    stock_df = stock_df.with_columns(
        stock_r_15=pl.col("log_ret") / pl.col("r_15_std"),
        stock_rv_15=pl.col("range_pct") / pl.col("rv_15_mean"),
        stock_volz_15=(pl.col("volume") - pl.col("vol_mean")) / pl.col("vol_std")
    )
    
    # Join Daily features to Intraday
    stock_df = stock_df.join(
        daily_joined.select([
            "symbol", "date", "rolling_beta_60d", "adv_rank_20d", 
            "prev_high", "prev_low", "prev_atr14", "trend_strength_daily",
            "high_20d", "high_52w"
        ]),
        left_on=["symbol", "date_only"], right_on=["symbol", "date"], how="left"
    )
    
    # VWAP dist
    stock_df = stock_df.with_columns(
        stock_vwap_dist=((pl.col("close") - pl.col("vwap")) / pl.col("vwap")) / (pl.col("prev_atr14") / pl.col("close"))
    )
    
    # Join Nifty intraday
    stock_df = stock_df.join(
        nifty_df.select(["datetime", pl.col("r_15").alias("nifty_r_15"), pl.col("close").alias("nifty_close")]),
        on="datetime", how="left"
    )
    
    # Nifty 60m return (4 bars)
    stock_df = stock_df.with_columns(
        nifty_ret_60=(pl.col("nifty_close") / pl.col("nifty_close").shift(4) - 1).over("symbol"),
        stock_ret_60=(pl.col("close") / pl.col("close").shift(4) - 1).over("symbol")
    )
    
    stock_df = stock_df.with_columns(
        rel_ret_15_vs_nifty=pl.col("stock_r_15") - pl.col("nifty_r_15"),
        rel_ret_60_vs_nifty=pl.col("stock_ret_60") - pl.col("nifty_ret_60")
    )
    
    # Sector relative strength
    if sector_df is not None:
        # Assume stock_df has 'sector' column or we join it
        # For simplicity, if sector_df is provided, we join on datetime and sector
        stock_df = stock_df.join(
            sector_df.select(["datetime", "sector", pl.col("close").alias("sector_close")]),
            on=["datetime", "sector"], how="left"
        )
        stock_df = stock_df.with_columns(
            sector_ret_60=(pl.col("sector_close") / pl.col("sector_close").shift(4) - 1).over("symbol")
        )
        stock_df = stock_df.with_columns(
            sector_rel_strength=pl.col("stock_ret_60") - pl.col("sector_ret_60"),
            sector_rel_weakness=pl.col("sector_ret_60") - pl.col("stock_ret_60")
        )
    else:
        stock_df = stock_df.with_columns(
            sector_rel_strength=pl.lit(0.0),
            sector_rel_weakness=pl.lit(0.0)
        )
        
    # dist_to_prev_day_high / low
    stock_df = stock_df.with_columns(
        dist_to_prev_day_high=(pl.col("close") - pl.col("prev_high")) / pl.col("prev_atr14"),
        dist_to_prev_day_low=(pl.col("close") - pl.col("prev_low")) / pl.col("prev_atr14")
    )
    
    # pct_from_20d_high / 52w_high
    stock_df = stock_df.with_columns(
        pct_from_20d_high=(pl.col("close") - pl.col("high_20d")) / pl.col("high_20d"),
        pct_from_52w_high=(pl.col("close") - pl.col("high_52w")) / pl.col("high_52w")
    )
    
    # ORB (Open Range Breakout) 9:15-9:30
    # First 15m bar of the day is 9:15-9:30. Let's get its high and low.
    orb_df = stock_df.filter(
        (pl.col("time_only") >= pl.time(9, 15)) & (pl.col("time_only") <= pl.time(9, 30))
    ).group_by(["symbol", "date_only"]).agg(
        orb_high=pl.col("high").max(),
        orb_low=pl.col("low").min()
    )
    
    stock_df = stock_df.join(orb_df, on=["symbol", "date_only"], how="left")
    
    stock_df = stock_df.with_columns(
        orb_breakout_flag=pl.when(pl.col("close") > pl.col("orb_high")).then(1).otherwise(0),
        orb_breakdown_flag=pl.when(pl.col("close") < pl.col("orb_low")).then(1).otherwise(0)
    )
    
    # TOD sin/cos
    # Minutes from 9:15
    stock_df = stock_df.with_columns(
        mins_from_open=(pl.col("time_only").dt.hour() - 9) * 60 + pl.col("time_only").dt.minute() - 15
    )
    # Total minutes in trading day (9:15 to 15:30 = 6 hours 15 mins = 375 mins)
    stock_df = stock_df.with_columns(
        tod_sin=np.sin(2 * np.pi * pl.col("mins_from_open") / 375),
        tod_cos=np.cos(2 * np.pi * pl.col("mins_from_open") / 375)
    )
    
    # bounce_risk_zscore (Z of trailing 3-bar cum return)
    stock_df = stock_df.with_columns(
        ret_3bar=(pl.col("close") / pl.col("close").shift(3) - 1).over("symbol")
    )
    stock_df = stock_df.with_columns(
        ret_3bar_mean=pl.col("ret_3bar").rolling_mean(window_size=20).over("symbol"),
        ret_3bar_std=pl.col("ret_3bar").rolling_std(window_size=20).over("symbol")
    ).with_columns(
        bounce_risk_zscore=(pl.col("ret_3bar") - pl.col("ret_3bar_mean")) / pl.col("ret_3bar_std")
    )
    
    # downside_acceleration: Down-range / total range over last 4 bars
    stock_df = stock_df.with_columns(
        down_range=pl.max_horizontal(pl.lit(0), pl.col("close").shift(4) - pl.col("close")).over("symbol"),
        total_range=(pl.col("high").rolling_max(window_size=4) - pl.col("low").rolling_min(window_size=4)).over("symbol")
    ).with_columns(
        downside_acceleration=pl.col("down_range") / pl.col("total_range")
    )
    
    return stock_df
