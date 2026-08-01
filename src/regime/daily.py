import polars as pl

from .types import DailyRegime


def classify_daily_regime(
    df: pl.DataFrame,
    market_trend_threshold: float = 0.0,
    vix_shock_threshold: float = 1.5,
    vix_delta_threshold: float = 0.2,
    gap_shock_threshold: float = 1.5,
    vix_elevated_threshold: float = 1.2,
    breadth_weak_threshold: float = 0.4
) -> pl.DataFrame:
    """
    Tier 1 Daily Regime Classifier based on deterministic rules.
    Runs pre-open to gate lower tiers.
    
    Vectorized classification for backtesting and live trading.
    Expects columns: market_trend, vol_regime_ratio, vol_regime_delta, shock, breadth_div
    """
    return df.with_columns(
        pl.when(
            (pl.col("shock").abs() > gap_shock_threshold) |
            ((pl.col("vol_regime_ratio") > vix_shock_threshold) & (pl.col("vol_regime_delta") > vix_delta_threshold))
        ).then(pl.lit(DailyRegime.NO_TRADE.value))
        .when(
            (pl.col("vol_regime_ratio") > vix_shock_threshold) |
            (pl.col("vol_regime_delta") > vix_delta_threshold) |
            ((pl.col("market_trend") < market_trend_threshold) & 
             ((pl.col("vol_regime_ratio") > vix_elevated_threshold) | (pl.col("breadth_div") < breadth_weak_threshold)))
        ).then(pl.lit(DailyRegime.HOSTILE.value))
        .when(
            (pl.col("market_trend") >= market_trend_threshold) & 
            (pl.col("vol_regime_ratio") <= vix_elevated_threshold) & 
            (pl.col("breadth_div") >= breadth_weak_threshold)
        ).then(pl.lit(DailyRegime.SUPPORTIVE.value))
        .otherwise(pl.lit(DailyRegime.AMBIGUOUS.value))
        .alias("daily_regime")
    )
