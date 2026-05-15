from __future__ import annotations

from pathlib import Path
from typing import Dict

import polars as pl

from .utils import load_config


# Resolve <repo_root>/config/sectoral_features.yml relative to this file
# (src/sectoral_features.py -> repo root is one parent up from src/).
_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "sectoral_features.yml"

_CFG = load_config(_CONFIG_PATH)

def compute_1m_sector_features(
    sector_df: pl.DataFrame,
    datetime_col: str = "timestamp"
) -> pl.DataFrame:
    """
    Computes 1-minute sector features.

    """
    sector_df = sector_df.with_columns(
         pl.col("close").alias("sector_close"),
    )
    return sector_df

def compute_5m_sector_features(
    sector_df: pl.DataFrame,
    symbol_dfs: Dict[str, pl.DataFrame],
    datetime_col: str = "timestamp",
) -> pl.DataFrame:
    """
    Resamples 1m sector data to 5m and returns a 5m feature dataframe.

    The returned timestamps are shifted forward by 5 minutes so the features
    can be joined onto 1m data without lookahead bias.
    """
    # 1) Resample sector df to 5m
    df_5m = sector_df.group_by_dynamic(datetime_col, every="5m").agg(
        [
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").last().alias("close"),
        ]
    )

    # 2) Select only feature columns (currently none, but keeping structure for future)
    df_5m_features = df_5m.select(
        [
            pl.col(datetime_col)
        ]
    )

    # Shift 5m timestamp forward by 5 minutes to avoid lookahead bias
    df_5m_features = df_5m_features.with_columns(
        (pl.col(datetime_col) + pl.duration(minutes=5)).alias(datetime_col)
    )

    return df_5m_features.drop_nulls()


def build_sectoral_features(
    sector_df: pl.DataFrame,
    symbol_dfs: Dict[str, pl.DataFrame],
    datetime_col: str = "timestamp",
) -> pl.DataFrame:
    """
    Orchestrates building sectoral features then joins the 5m features onto
    the 1m sector dataframe via an as-of backward join.
    """
    sector_df = compute_1m_sector_features(sector_df, datetime_col)
    df_5m_features = compute_5m_sector_features(sector_df, symbol_dfs, datetime_col)
    return sector_df.join_asof(df_5m_features, on=datetime_col, strategy="backward")

