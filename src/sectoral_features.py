from __future__ import annotations

from pathlib import Path
from typing import Dict

import polars as pl

from .features import add_advance_decline, add_roc
from .utils import load_config


# Resolve <repo_root>/config/sectoral_features.yml relative to this file
# (src/sectoral_features.py -> repo root is one parent up from src/).
_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "sectoral_features.yml"

_CFG = load_config(_CONFIG_PATH)


def compute_5m_sector_features(
    sector_df: pl.DataFrame,
    symbol_dfs: Dict[str, pl.DataFrame],
    datetime_col: str = "timestamp",
    *,
    roc_period: int = _CFG["roc"]["period"],
) -> pl.DataFrame:
    """
    Resamples 1m sector data and 1m symbol data to 5m, computes smoothed ROC
    (SMA of close pct-change) and Advance/Decline on 5m bars, and returns a 5m
    feature dataframe.

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

    # 2) Resample all symbol dfs to 5m (close only)
    symbol_5m_dfs: Dict[str, pl.DataFrame] = {}
    for sym, df in symbol_dfs.items():
        symbol_5m_dfs[sym] = df.group_by_dynamic(datetime_col, every="5m").agg(
            [pl.col("close").last().alias("close")]
        )

    # 3) Compute A/D across symbols (joins onto df_5m)
    df_5m = add_advance_decline(df_5m, symbol_5m_dfs, datetime_col=datetime_col)

    # 4) Compute ROC on 5m sector data
    df_5m = add_roc(df_5m, period=roc_period)

    # 5) Select only feature columns
    df_5m_features = df_5m.select(
        [
            pl.col(datetime_col),
            pl.col("roc").alias("sector_index_roc_5m"),
            pl.col("advance_decline").alias("sector_ad_5m"),
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
    df_5m_features = compute_5m_sector_features(sector_df, symbol_dfs, datetime_col)
    return sector_df.join_asof(df_5m_features, on=datetime_col, strategy="backward")

