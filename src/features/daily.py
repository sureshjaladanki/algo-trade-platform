import polars as pl

from .core import atr, ema, gap, pct_distance, pct_return, rolling_median


def calculate_daily_vix_features(vix_df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates market-level Daily Regime features from India VIX.

    Inputs:
    - vix_df: EOD India VIX data (date, close)
    """
    return vix_df.sort("date").select(
        pl.col("date"),
        pl.col("close").alias("vix_close"),
        vix_median_60d=rolling_median("close", 60),
        vol_regime_delta=pct_return("close")
    ).with_columns(
        vol_regime_ratio=pl.col("vix_close") / pl.col("vix_median_60d")
    ).select([
        "date", "vol_regime_ratio", "vol_regime_delta"
    ])


def calculate_daily_market_features(market_df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates market-level Daily Regime features from the Nifty 50 index.

    Inputs:
    - market_df: EOD market index data (date, open, high, low, close)
    """
    return market_df.sort("date").with_columns(
        ema20=ema("close", span=20),
        atr14=atr(window=14),
        gap_raw=gap("open", "close")
    ).with_columns(
        market_trend=pct_distance("close", "ema20") * 100,
        shock=pl.col("gap_raw") / pl.col("atr14")
    ).select([
        "date", "market_trend", "shock"
    ])


def calculate_daily_market_breadth_features(nifty100_dfs: list[pl.DataFrame]) -> pl.DataFrame:
    """
    Calculates market breadth features (e.g. % of stocks above 20 DMA).

    Inputs:
    - nifty100_dfs: List of EOD stock DataFrames (date, close) for Nifty 100 constituents
    """
    processed_dfs = []
    for df in nifty100_dfs:
        processed = df.sort("date").with_columns(
            dma20=pl.col("close").rolling_mean(20)
        ).with_columns(
            above_20dma=(pl.col("close") > pl.col("dma20")).cast(pl.Float64)
        ).select(["date", "above_20dma"])
        processed_dfs.append(processed)
    
    if not processed_dfs:
        return pl.DataFrame({"date": [], "breadth_div": []})
        
    all_stocks = pl.concat(processed_dfs)
    
    breadth = all_stocks.group_by("date").agg(
        breadth_div=pl.col("above_20dma").mean()
    ).sort("date")
    
    return breadth


def calculate_daily_features(vix_df: pl.DataFrame, market_df: pl.DataFrame, nifty100_dfs: list[pl.DataFrame]) -> pl.DataFrame:
    """
    Calculates Daily Regime features by composing VIX, Nifty 50, and market breadth features.

    Inputs:
    - vix_df: EOD India VIX data (date, close)
    - market_df: EOD Nifty 50 index data (date, open, high, low, close)
    - nifty100_dfs: List of EOD stock DataFrames (date, close) for Nifty 100 constituents
    """
    vix_features = calculate_daily_vix_features(vix_df)
    market_features = calculate_daily_market_features(market_df)
    market_breadth_features = calculate_daily_market_breadth_features(nifty100_dfs)

    return vix_features.join(market_features, on="date", how="left").join(market_breadth_features, on="date", how="left")
