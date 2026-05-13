from __future__ import annotations

from pathlib import Path

import polars as pl

from .features import add_minute_of_day, add_trading_session
from .utils import load_config


# Resolve <repo_root>/config/market_features.yml relative to this file
# (src/market_features.py -> repo root is one parent up from src/).
_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "market_features.yml"

_CFG = load_config(_CONFIG_PATH)


def compute_1m_market_features(
    market_df: pl.DataFrame,
    datetime_col: str = "timestamp"
) -> pl.DataFrame:
    """
    Computes 1-minute market features.

    """
    
    return market_df


def compute_5m_market_features(
    market_df: pl.DataFrame,
    datetime_col: str = "timestamp",
) -> pl.DataFrame:
    """
    Resamples 1m market data to 5m and returns a 5m feature dataframe.

    The returned timestamps are shifted forward by 5 minutes so the features
    can be joined onto 1m data without lookahead bias.
    """
    # 1) Resample market df to 5m
    df_5m = market_df.group_by_dynamic(datetime_col, every="5m").agg(
        [
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").last().alias("close"),
        ]
    )

    # 2) Select only feature columns
    df_5m_features = df_5m.select(
        [
            pl.col(datetime_col),
            pl.col("close").alias("market_vix_5m"),
        ]
    )

    # Shift 5m timestamp forward by 5 minutes to avoid lookahead bias
    df_5m_features = df_5m_features.with_columns(
        (pl.col(datetime_col) + pl.duration(minutes=5)).alias(datetime_col)
    )

    return df_5m_features.drop_nulls()


def build_market_features(
    market_df: pl.DataFrame,
    datetime_col: str = "timestamp",
) -> pl.DataFrame:
    """
    Orchestrates building market features then joins the 5m features onto the
    1m market dataframe via an as-of backward join.
    """
    market_df = compute_1m_market_features(market_df, datetime_col)
    df_5m_features = compute_5m_market_features(market_df, datetime_col)
    return market_df.join_asof(df_5m_features, on=datetime_col, strategy="backward")
