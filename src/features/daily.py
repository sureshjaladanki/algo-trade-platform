import polars as pl

from .core import atr, ema, gap, pct_distance, pct_return, rolling_median


def calculate_daily_market_features(vix_df: pl.DataFrame) -> pl.DataFrame:
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


def calculate_daily_sectoral_features(index_df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates sectoral Daily Regime features from the sectoral index.

    Inputs:
    - index_df: EOD sectoral index data (date, open, high, low, close)
    """
    return index_df.sort("date").with_columns(
        ema20=ema("close", span=20),
        atr14=atr(window=14),
        gap_raw=gap("open", "close")
    ).with_columns(
        nifty_trend=pct_distance("close", "ema20") * 100,
        shock=pl.col("gap_raw") / pl.col("atr14")
    ).select([
        "date", "nifty_trend", "shock"
    ])


def calculate_daily_features(df: pl.DataFrame, index_df: pl.DataFrame, vix_df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculates Daily Regime features by composing market, sectoral, and breadth features.

    Inputs:
    - df: EOD constituent data (date, close)
    - index_df: EOD sectoral index data (date, open, high, low, close)
    - vix_df: EOD India VIX data (date, close)
    """
    market = calculate_daily_market_features(vix_df)
    sectoral = calculate_daily_sectoral_features(index_df)

    breadth = (
        df.sort("date")
        .with_columns(
            dma20=pl.col("close").rolling_mean(20)
        )
        .with_columns(
            pct_above_20dma=pct_distance("close", "dma20") * 100
        )
        .select(
            pl.col("date"),
            pl.col("pct_above_20dma").alias("breadth_div")
        )
    )

    return market.join(sectoral, on="date", how="left").join(breadth, on="date", how="left").select([
        "date", "nifty_trend", "vol_regime_ratio", "vol_regime_delta", "shock", "breadth_div"
    ])
