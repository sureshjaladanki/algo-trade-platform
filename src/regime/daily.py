import polars as pl

from .types import DailyRegime

# Fallback design prior when no train sample is available (ATR units over 5d EMA slope).
DEFAULT_TREND_STRENGTH_THRESHOLD = 0.5


def design_trend_strength_threshold(daily_features: pl.DataFrame) -> float:
    """
    Train-period design prior for SUPPORTIVE trend_strength floor.

    Median |trend_strength| on the design sample only — not searched against D2/I1/I5.
    """
    vals = daily_features.get_column("trend_strength").drop_nulls().abs()
    return float(vals.median())


def classify_daily_regime(
    df: pl.DataFrame,
    market_trend_threshold: float = 0.0,
    vix_shock_threshold: float = 1.5,
    vix_delta_threshold: float = 0.2,
    gap_shock_threshold: float = 1.5,
    vix_elevated_threshold: float = 1.2,
    breadth_weak_threshold: float = 0.4,
    trend_strength_threshold: float = DEFAULT_TREND_STRENGTH_THRESHOLD,
) -> pl.DataFrame:
    """
    Tier 1 Daily Regime Classifier based on deterministic rules.
    Runs pre-open to gate lower tiers.

    Vectorized classification for backtesting and live trading.
    Expects pre-open-aligned columns (see `calculate_daily_features`):
    market_trend, trend_strength, vol_regime_ratio, vol_regime_delta, shock, breadth_div
    — prior-close VIX/trend/breadth plus open-gap shock with prior ATR.

    v1.1 O1: SUPPORTIVE is capturable trend quality (|trend_strength| floor),
    not calm. Flat greens (weak strength) fall through to AMBIGUOUS. Calm/vol
    still shapes HOSTILE / NO_TRADE; breadth remains confirmatory on SUPPORTIVE.

    NO_TRADE hard vetoes:
    - large overnight gap shock
    - VIX spike: elevated vs 60d median AND large positive 1d ΔVIX
    - VIX collapse: elevated vs 60d median AND large negative 1d ΔVIX (event crush)
    """
    vix_spike = (pl.col("vol_regime_ratio") > vix_shock_threshold) & (
        pl.col("vol_regime_delta") > vix_delta_threshold
    )
    vix_collapse = (pl.col("vol_regime_ratio") > vix_elevated_threshold) & (
        pl.col("vol_regime_delta") < -vix_delta_threshold
    )

    return df.with_columns(
        pl.when(
            (pl.col("shock").abs() > gap_shock_threshold) | vix_spike | vix_collapse
        )
        .then(pl.lit(DailyRegime.NO_TRADE.value))
        .when(
            (pl.col("vol_regime_ratio") > vix_shock_threshold)
            | (pl.col("vol_regime_delta") > vix_delta_threshold)
            | (pl.col("vol_regime_delta") < -vix_delta_threshold)
            | (
                (pl.col("market_trend") < market_trend_threshold)
                & (
                    (pl.col("vol_regime_ratio") > vix_elevated_threshold)
                    | (pl.col("breadth_div") < breadth_weak_threshold)
                )
            )
        )
        .then(pl.lit(DailyRegime.HOSTILE.value))
        .when(
            (pl.col("market_trend") >= market_trend_threshold)
            & (pl.col("trend_strength").abs() >= trend_strength_threshold)
            & (pl.col("breadth_div") >= breadth_weak_threshold)
        )
        .then(pl.lit(DailyRegime.SUPPORTIVE.value))
        .otherwise(pl.lit(DailyRegime.AMBIGUOUS.value))
        .alias("daily_regime")
    )
