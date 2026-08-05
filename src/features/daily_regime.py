import polars as pl

from .core import atr, ema, gap, pct_distance, pct_return, rolling_median


def calculate_daily_vix_features(vix_df: pl.DataFrame) -> pl.DataFrame:
    """
    Pre-open VIX regime features for session date T.

    Uses prior-session VIX (T−1 close vs T−1 60d median, and T−1 1d ΔVIX),
    which is available at the 9:08–9:15 gate.
    """
    return (
        vix_df.sort("date")
        .select(
            pl.col("date"),
            pl.col("close").alias("vix_close"),
            vix_median_60d=rolling_median("close", 60),
            vol_regime_delta=pct_return("close"),
        )
        .with_columns(vol_regime_ratio=pl.col("vix_close") / pl.col("vix_median_60d"))
        .with_columns(
            vol_regime_ratio=pl.col("vol_regime_ratio").shift(1),
            vol_regime_delta=pl.col("vol_regime_delta").shift(1),
        )
        .select(["date", "vol_regime_ratio", "vol_regime_delta"])
    )


def calculate_daily_market_features(market_df: pl.DataFrame) -> pl.DataFrame:
    """
    Pre-open market regime features for session date T.

    - market_trend: prior close vs EMA20 (T−1), available pre-open
    - shock: today's open gap / prev_ATR14 — open is known by ~9:08
    """
    return (
        market_df.sort("date")
        .with_columns(
            ema20=ema("close", span=20),
            prev_atr14=atr(window=14).shift(1),
            gap_raw=gap("open", "close"),
        )
        .with_columns(
            market_trend=(pct_distance("close", "ema20") * 100).shift(1),
            shock=pl.col("gap_raw") / pl.col("prev_atr14"),
        )
        .select(["date", "market_trend", "shock"])
    )


def calculate_daily_market_breadth_features(nifty100_dfs: list[pl.DataFrame]) -> pl.DataFrame:
    """
    Pre-open breadth for session date T: prior-session % of Nifty 100 above 20DMA.
    """
    processed_dfs = []
    for df in nifty100_dfs:
        processed = (
            df.sort("date")
            .with_columns(dma20=pl.col("close").rolling_mean(20))
            .with_columns(above_20dma=(pl.col("close") > pl.col("dma20")).cast(pl.Float64))
            .select(["date", "above_20dma"])
        )
        processed_dfs.append(processed)

    if not processed_dfs:
        return pl.DataFrame({"date": [], "breadth_div": []})

    all_stocks = pl.concat(processed_dfs)

    breadth = (
        all_stocks.group_by("date")
        .agg(breadth_div=pl.col("above_20dma").mean())
        .sort("date")
        .with_columns(breadth_div=pl.col("breadth_div").shift(1))
    )

    return breadth


def calculate_daily_features(
    vix_df: pl.DataFrame, market_df: pl.DataFrame, nifty100_dfs: list[pl.DataFrame]
) -> pl.DataFrame:
    """
    Daily Regime features aligned to the pre-open gate on each session date.

    Row date=T is safe to use for gating day-T intraday bars (no same-day close leakage).
    """
    vix_features = calculate_daily_vix_features(vix_df)
    market_features = calculate_daily_market_features(market_df)
    market_breadth_features = calculate_daily_market_breadth_features(nifty100_dfs)

    return vix_features.join(market_features, on="date", how="left").join(
        market_breadth_features, on="date", how="left"
    )
