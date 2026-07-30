import polars as pl
from typing import Dict
from .types import DailyRegime

class DailyRegimeClassifier:
    """
    Tier 1 Daily Regime Classifier based on deterministic rules.
    Runs pre-open to gate lower tiers.
    """
    
    def __init__(
        self, 
        nifty_trend_threshold: float = 0.0,
        vix_shock_threshold: float = 1.5,
        vix_delta_threshold: float = 0.2,
        gap_shock_threshold: float = 1.5,
        vix_elevated_threshold: float = 1.2,
        breadth_weak_threshold: float = 0.4
    ):
        self.nifty_trend_threshold = nifty_trend_threshold
        self.vix_shock_threshold = vix_shock_threshold
        self.vix_delta_threshold = vix_delta_threshold
        self.gap_shock_threshold = gap_shock_threshold
        self.vix_elevated_threshold = vix_elevated_threshold
        self.breadth_weak_threshold = breadth_weak_threshold

    def classify(self, features: Dict[str, float]) -> DailyRegime:
        """
        Classifies the daily regime based on the latest EOD / pre-open features.
        
        Expected features:
        - nifty_trend: Continuous % distance of Nifty close to EMA20
        - vol_regime_ratio: India VIX vs 60d median
        - vol_regime_delta: 1d change in VIX
        - shock: Overnight gap / ATR14
        - breadth_div: % of Nifty 100 stocks above 20DMA (or 5DMA / AD ratio)
        """
        nifty_trend = features.get("nifty_trend", 0.0)
        vol_regime_ratio = features.get("vol_regime_ratio", 1.0)
        vol_regime_delta = features.get("vol_regime_delta", 0.0)
        shock = features.get("shock", 0.0)
        breadth = features.get("breadth_div", 0.5)

        # 1. Hard Veto (NO_TRADE) - Capital preservation kill switch
        if (abs(shock) > self.gap_shock_threshold or 
            vol_regime_ratio > self.vix_shock_threshold or 
            vol_regime_delta > self.vix_delta_threshold):
            return DailyRegime.NO_TRADE
            
        # 2. Hostile Market (HOSTILE)
        if nifty_trend < self.nifty_trend_threshold and (vol_regime_ratio > self.vix_elevated_threshold or breadth < self.breadth_weak_threshold):
            return DailyRegime.HOSTILE
            
        # 3. Supportive Trend (SUPPORTIVE)
        if nifty_trend >= self.nifty_trend_threshold and vol_regime_ratio <= self.vix_elevated_threshold and breadth >= self.breadth_weak_threshold:
            return DailyRegime.SUPPORTIVE
            
        # 4. Ambiguous
        return DailyRegime.AMBIGUOUS

    def classify_history(self, df: pl.DataFrame) -> pl.DataFrame:
        """
        Vectorized classification for backtesting.
        Expects columns: nifty_trend, vol_regime_ratio, vol_regime_delta, shock, breadth_div
        """
        return df.with_columns(
            pl.when(
                (pl.col("shock").abs() > self.gap_shock_threshold) |
                (pl.col("vol_regime_ratio") > self.vix_shock_threshold) |
                (pl.col("vol_regime_delta") > self.vix_delta_threshold)
            ).then(pl.lit(DailyRegime.NO_TRADE.value))
            .when(
                (pl.col("nifty_trend") < self.nifty_trend_threshold) & 
                ((pl.col("vol_regime_ratio") > self.vix_elevated_threshold) | (pl.col("breadth_div") < self.breadth_weak_threshold))
            ).then(pl.lit(DailyRegime.HOSTILE.value))
            .when(
                (pl.col("nifty_trend") >= self.nifty_trend_threshold) & 
                (pl.col("vol_regime_ratio") <= self.vix_elevated_threshold) & 
                (pl.col("breadth_div") >= self.breadth_weak_threshold)
            ).then(pl.lit(DailyRegime.SUPPORTIVE.value))
            .otherwise(pl.lit(DailyRegime.AMBIGUOUS.value))
            .alias("daily_regime")
        )
