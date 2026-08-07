"""Tier 2 Horizon stock features (shared Long/Short core + Short asymmetry)."""

import math

import polars as pl

def calculate_horizon_features(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    sector_df: pl.DataFrame,
    daily_stock_df: pl.DataFrame,
    daily_nifty_df: pl.DataFrame,
    daily_regime_df: pl.DataFrame,
    tod_lookback_days: int = 60,
) -> pl.DataFrame:
    """
    Calculates Tier 2 Long and Short features.

    Inputs:
    - stock_df: 15m stock OHLCV (date, open, high, low, close, volume, symbol, sector)
    - nifty_df: 15m Nifty with at least date, close; preferably r_15 and vwap_dist
      (Tier 1 emissions) for relative strength / index_vwap_dist pass-through
    - sector_df: 15m sector closes (date, sector, close)
    - daily_stock_df / daily_nifty_df: EOD bars
    - daily_regime_df: Tier 1 daily features with date + vol_regime_ratio

    Daily EOD features are lagged one session before joining to intraday (no same-day leak).
    TOD norms are causal: per (symbol, clock bucket), rolling over prior sessions only.
    """
    stock_df = stock_df.sort(["symbol", "date"])
    nifty_df = nifty_df.sort("date")
    sector_df = sector_df.sort(["sector", "date"])
    daily_stock_df = daily_stock_df.sort(["symbol", "date"])
    daily_nifty_df = daily_nifty_df.sort("date")

    # --- Daily (lagged to T−1 for use on session T) ---
    daily_joined = daily_stock_df.join(
        daily_nifty_df.select(["date", pl.col("close").alias("nifty_close")]),
        on="date",
        how="left",
    ).with_columns(
        stock_ret=pl.col("close").pct_change().over("symbol"),
        nifty_ret=pl.col("nifty_close").pct_change().over("symbol"),
    )

    daily_joined = daily_joined.with_columns(
        cov_60d=pl.rolling_cov(
            pl.col("stock_ret"), pl.col("nifty_ret"), window_size=60
        ).over("symbol"),
        var_60d=pl.col("nifty_ret").rolling_var(window_size=60).over("symbol"),
        adv_20d=pl.col("volume").rolling_mean(window_size=20).over("symbol"),
        tr=pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - pl.col("close").shift(1).over("symbol")).abs(),
            (pl.col("low") - pl.col("close").shift(1).over("symbol")).abs(),
        ),
        high_20d=pl.col("high").rolling_max(window_size=20).over("symbol"),
        high_52w=pl.col("high").rolling_max(window_size=252).over("symbol"),
        ema20=pl.col("close").ewm_mean(span=20, adjust=False).over("symbol"),
    ).with_columns(
        atr14=pl.col("tr").rolling_mean(window_size=14).over("symbol"),
        rolling_beta_60d=pl.col("cov_60d") / pl.col("var_60d"),
        trend_strength_daily=(pl.col("close") / pl.col("ema20")) - 1.0,
        adv_rank_20d=(
            pl.col("adv_20d").rank(method="average").over("date")
            / pl.len().over("date")
        ),
        prev_high=pl.col("high").shift(1).over("symbol"),
        prev_low=pl.col("low").shift(1).over("symbol"),
    ).with_columns(
        prev_atr14=pl.col("atr14").shift(1).over("symbol"),
    )

    # Lag structural daily features so intraday date T sees T−1 EOD only.
    # prev_* already lagged one day from raw OHLC.
    lag_cols = [
        "rolling_beta_60d",
        "adv_rank_20d",
        "trend_strength_daily",
        "high_20d",
        "high_52w",
    ]
    daily_joined = daily_joined.with_columns(
        [pl.col(c).shift(1).over("symbol").alias(c) for c in lag_cols]
    )

    # --- Intraday base ---
    stock_df = stock_df.with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
    ).with_columns(
        log_ret=(
            pl.col("close") / pl.col("close").shift(1).over("symbol")
        ).log(),
        range_pct=(
            (pl.col("high") - pl.col("low")) / pl.col("close").shift(1).over("symbol")
        ),
    )

    stock_df = stock_df.with_columns(
        typ_price=(pl.col("high") + pl.col("low") + pl.col("close")) / 3.0,
    ).with_columns(
        cum_vol=pl.col("volume").cum_sum().over(["symbol", "date_only"]),
        cum_pv=(pl.col("typ_price") * pl.col("volume")).cum_sum().over(
            ["symbol", "date_only"]
        ),
    ).with_columns(
        vwap=pl.col("cum_pv") / pl.col("cum_vol"),
    )

    # Causal TOD norms: prior sessions only within (symbol, clock bucket).
    min_periods = max(10, tod_lookback_days // 4)
    stock_df = stock_df.sort(["symbol", "time_only", "date_only"]).with_columns(
        r_15_std=pl.col("log_ret")
        .shift(1)
        .rolling_std(window_size=tod_lookback_days, min_periods=min_periods)
        .over(["symbol", "time_only"]),
        rv_15_mean=pl.col("range_pct")
        .shift(1)
        .rolling_mean(window_size=tod_lookback_days, min_periods=min_periods)
        .over(["symbol", "time_only"]),
        vol_mean=pl.col("volume")
        .shift(1)
        .rolling_mean(window_size=tod_lookback_days, min_periods=min_periods)
        .over(["symbol", "time_only"]),
        vol_std=pl.col("volume")
        .shift(1)
        .rolling_std(window_size=tod_lookback_days, min_periods=min_periods)
        .over(["symbol", "time_only"]),
    ).sort(["symbol", "date"]).with_columns(
        stock_r_15=pl.col("log_ret") / pl.col("r_15_std"),
        stock_rv_15=pl.col("range_pct") / pl.col("rv_15_mean"),
        stock_volz_15=(pl.col("volume") - pl.col("vol_mean")) / pl.col("vol_std"),
    )

    stock_df = stock_df.join(
        daily_joined.select(
            [
                "symbol",
                "date",
                "rolling_beta_60d",
                "adv_rank_20d",
                "prev_high",
                "prev_low",
                "prev_atr14",
                "trend_strength_daily",
                "high_20d",
                "high_52w",
            ]
        ),
        left_on=["symbol", "date_only"],
        right_on=["symbol", "date"],
        how="left",
    ).with_columns(
        stock_vwap_dist=(
            ((pl.col("close") - pl.col("vwap")) / pl.col("vwap"))
            / (pl.col("prev_atr14") / pl.col("close"))
        ),
    )

    # Nifty relative + index_vwap_dist pass-through.
    nifty_cols = ["date", pl.col("close").alias("nifty_close")]
    if "r_15" in nifty_df.columns:
        nifty_cols.append(pl.col("r_15").alias("nifty_r_15"))
    if "vwap_dist" in nifty_df.columns:
        nifty_cols.append(pl.col("vwap_dist").alias("index_vwap_dist"))

    stock_df = stock_df.join(nifty_df.select(nifty_cols), on="date", how="left")

    if "nifty_r_15" not in stock_df.columns:
        # Fallback: TOD-normalize nifty log ret with causal index-level TOD.
        nifty_tmp = (
            nifty_df.sort("date")
            .with_columns(
                date_only=pl.col("date").dt.date(),
                time_only=pl.col("date").dt.time(),
                log_ret=(pl.col("close") / pl.col("close").shift(1)).log(),
            )
            .sort(["time_only", "date_only"])
            .with_columns(
                nifty_r_15_std=pl.col("log_ret")
                .shift(1)
                .rolling_std(window_size=tod_lookback_days, min_periods=min_periods)
                .over("time_only"),
            )
            .with_columns(nifty_r_15=pl.col("log_ret") / pl.col("nifty_r_15_std"))
            .select(["date", "nifty_r_15"])
        )
        stock_df = stock_df.join(nifty_tmp, on="date", how="left")

    if "index_vwap_dist" not in stock_df.columns:
        stock_df = stock_df.with_columns(index_vwap_dist=pl.lit(None, dtype=pl.Float64))

    # Trailing-4-bar returns stay inside the session so they never span the
    # overnight gap (gap risk is carried by the prior-day distance features).
    session = ["symbol", "date_only"]
    stock_df = stock_df.with_columns(
        nifty_ret_60=(
            pl.col("nifty_close") / pl.col("nifty_close").shift(4).over(session) - 1
        ),
        stock_ret_60=(pl.col("close") / pl.col("close").shift(4).over(session) - 1),
    ).with_columns(
        rel_ret_15_vs_nifty=pl.col("stock_r_15") - pl.col("nifty_r_15"),
        rel_ret_60_vs_nifty=pl.col("stock_ret_60") - pl.col("nifty_ret_60"),
    )

    # Sector RS / weakness (60m).
    stock_df = stock_df.join(
        sector_df.select(
            ["date", "sector", pl.col("close").alias("sector_close")]
        ),
        on=["date", "sector"],
        how="left",
    ).with_columns(
        sector_ret_60=(
            pl.col("sector_close") / pl.col("sector_close").shift(4).over(session)
            - 1
        ),
    ).with_columns(
        sector_rel_strength=pl.col("stock_ret_60") - pl.col("sector_ret_60"),
        sector_rel_weakness=pl.col("sector_ret_60") - pl.col("stock_ret_60"),
    )

    stock_df = stock_df.with_columns(
        dist_to_prev_day_high=(pl.col("close") - pl.col("prev_high"))
        / pl.col("prev_atr14"),
        dist_to_prev_day_low=(pl.col("close") - pl.col("prev_low"))
        / pl.col("prev_atr14"),
        pct_from_20d_high=(pl.col("close") - pl.col("high_20d")) / pl.col("high_20d"),
        pct_from_52w_high=(pl.col("close") - pl.col("high_52w")) / pl.col("high_52w"),
    )

    # ORB reference = auction bleed bar only (09:15–09:30; bar-end stamp 09:30).
    orb_df = (
        stock_df.filter(pl.col("time_only") == pl.time(9, 30))
        .group_by(["symbol", "date_only"])
        .agg(orb_high=pl.col("high").max(), orb_low=pl.col("low").min())
    )
    stock_df = stock_df.join(orb_df, on=["symbol", "date_only"], how="left").with_columns(
        orb_breakout_flag=pl.when(pl.col("close") > pl.col("orb_high"))
        .then(1)
        .otherwise(0),
        orb_breakdown_flag=pl.when(pl.col("close") < pl.col("orb_low"))
        .then(1)
        .otherwise(0),
    )

    # Cyclic TOD (minutes from session open 09:15; session length 375m).
    two_pi = 2.0 * math.pi
    stock_df = stock_df.with_columns(
        mins_from_open=(
            (pl.col("time_only").dt.hour() - 9) * 60
            + pl.col("time_only").dt.minute()
            - 15
        ),
    ).with_columns(
        tod_sin=(two_pi * pl.col("mins_from_open") / 375.0).sin(),
        tod_cos=(two_pi * pl.col("mins_from_open") / 375.0).cos(),
    )

    stock_df = stock_df.with_columns(
        ret_3bar=(pl.col("close") / pl.col("close").shift(3).over(session) - 1),
    ).with_columns(
        # Baseline distribution is trailing across sessions (causal); the 3-bar
        # move being scored is intraday-only.
        ret_3bar_mean=pl.col("ret_3bar").rolling_mean(window_size=20).over("symbol"),
        ret_3bar_std=pl.col("ret_3bar").rolling_std(window_size=20).over("symbol"),
        down_range=pl.max_horizontal(
            pl.lit(0.0),
            pl.col("close").shift(4).over(session) - pl.col("close"),
        ),
        total_range=(
            pl.col("high").rolling_max(window_size=4).over(session)
            - pl.col("low").rolling_min(window_size=4).over(session)
        ),
    ).with_columns(
        bounce_risk_zscore=(pl.col("ret_3bar") - pl.col("ret_3bar_mean"))
        / pl.col("ret_3bar_std"),
        downside_acceleration=pl.col("down_range") / pl.col("total_range"),
    )

    # Tier 1 daily vol pass-through (same column name as Regime).
    if "vol_regime_ratio" not in daily_regime_df.columns:
        raise ValueError("daily_regime_df must include vol_regime_ratio")
    stock_df = stock_df.join(
        daily_regime_df.select(["date", "vol_regime_ratio"]),
        left_on="date_only",
        right_on="date",
        how="left",
    )

    return stock_df
