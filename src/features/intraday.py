import polars as pl

from .core import atr, log_return, pct_distance, range_pct


def calculate_intraday_features(
    df: pl.DataFrame, daily_df: pl.DataFrame, tod_lookback_days: int = 60
) -> pl.DataFrame:
    """
    Calculates Intraday Regime HMM emissions with TOD normalization.

    Inputs:
    - df: 15m Nifty data (date, open, high, low, close, volume)
    - daily_df: EOD Nifty data for ATR scaling (date, open, high, low, close)

    Cash-index feeds (^NSEI) have zero volume. Per Tier-1 judge lock:
    - drop participation (`volz_15`) rather than fake it with a range proxy
    - `vwap_dist` is ATR-scaled distance to session TWAP (equal-weight typical price)
    """
    # 1. Parse dates
    df = df.with_columns(
        datetime=pl.col("date").str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S")
        if df["date"].dtype == pl.Utf8
        else pl.col("date").cast(pl.Datetime)
    ).with_columns(
        date_only=pl.col("datetime").dt.date(),
        time_only=pl.col("datetime").dt.time(),
    )

    daily_df = daily_df.with_columns(
        date=pl.col("date").str.strptime(pl.Date, "%Y-%m-%d")
        if daily_df["date"].dtype == pl.Utf8
        else pl.col("date").cast(pl.Date)
    )

    # 2. Calculate daily ATR14 and shift by 1 to prevent lookahead bias intraday
    daily_df = daily_df.sort("date").with_columns(
        prev_atr14=atr("high", "low", "close", window=14).shift(1)
    )

    # 3. Simple left join on date
    df = df.join(
        daily_df.select(["date", "prev_atr14"]),
        left_on="date_only",
        right_on="date",
        how="left",
    )

    # 4. Session TWAP: cumulative equal-weight typical price (no volume dependency)
    df = df.sort("datetime").with_columns(
        _typical=(pl.col("high") + pl.col("low") + pl.col("close")) / 3.0,
    ).with_columns(
        twap=(
            pl.col("_typical").cum_sum().over("date_only")
            / pl.col("_typical").cum_count().over("date_only")
        )
    )

    # 5. Calculate base features
    df = df.with_columns(
        log_ret=log_return("close").fill_nan(0.0),
        range_pct=range_pct("high", "low", "close").fill_nan(0.0),
        vwap_dist_raw=pct_distance("close", "twap").fill_nan(0.0),
    )

    # 6. Causal TOD aggregations: per clock bucket, rolling over prior N sessions only
    min_periods = max(10, tod_lookback_days // 4)
    df = df.sort(["time_only", "date_only"]).with_columns(
        r_15_std=pl.col("log_ret")
        .shift(1)
        .rolling_std(window_size=tod_lookback_days, min_periods=min_periods)
        .over("time_only"),
        rv_15_mean=pl.col("range_pct")
        .shift(1)
        .rolling_mean(window_size=tod_lookback_days, min_periods=min_periods)
        .over("time_only"),
    )

    # 7. Final normalized features (restore session order)
    # Feature name `vwap_dist` kept for downstream compatibility; semantics are TWAP.
    df = df.sort("datetime").with_columns(
        r_15=pl.col("log_ret") / pl.col("r_15_std"),
        rv_15=pl.col("range_pct") / pl.col("rv_15_mean"),
        vwap_dist=pl.col("vwap_dist_raw") / (pl.col("prev_atr14") / pl.col("close")),
    )

    return df.select([
        "date",
        "r_15", "rv_15", "vwap_dist",
    ])
