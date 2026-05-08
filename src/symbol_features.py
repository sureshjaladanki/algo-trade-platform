from pathlib import Path

import polars as pl

from .features import (
    add_trading_day,
    add_minute_of_day,
    add_vwap,
    add_ema,
    add_bollinger,
    add_volume_zscore,
    add_relative_volume,
    add_atr_gap,
    add_rsi,
    add_adx,
)
from .utils import load_config


# Resolve <repo_root>/config/symbol_features.yml relative to this file
# (src/symbol_features.py -> repo root is one parent up from src/).
_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "symbol_features.yml"

_CFG = load_config(_CONFIG_PATH)


def compute_1m_features(
    df: pl.DataFrame,
    datetime_col: str = "timestamp",
    *,
    ema_period: int = _CFG["ema"]["period"],
    bb_period: int = _CFG["bollinger"]["period"],
    vol_zscore_period: int = _CFG["volume_zscore"]["period"],
    rel_vol_period: int = _CFG["relative_volume"]["period"],
    atr_period: int = _CFG["atr_gap"]["period"],
) -> pl.DataFrame:
    """
    Computes 1-minute features: VWAP, EMA, minute_of_the_day, Bollinger %B, Volume Z-Score,
    Relative Volume and Daily ATR / gap.

    Each per-feature `*_period` kwarg defaults to the value defined in
    config/symbol_features.yml.
    """
    # Create a date column to group by trading day for VWAP / ATR-gap
    df = add_trading_day(df, datetime_col)

    # Minute of day (used by relative volume)
    df = add_minute_of_day(df, datetime_col)

    # 1. VWAP (Grouped by trading day)
    df = add_vwap(df)

    # 2. EMA
    df = add_ema(df, period=ema_period)

    # 3. Bollinger %B
    df = add_bollinger(df, period=bb_period)

    # 4. Volume Z-Score
    df = add_volume_zscore(df, period=vol_zscore_period)

    # 5. Relative Volume (vol / rvol)
    df = add_relative_volume(df, datetime_col, period=rel_vol_period)

    # 6. Daily ATR and Gap (close - prev_day_close) / ATR
    df = add_atr_gap(df, period=atr_period)

    df = df.drop("trading_day")

    return df


def compute_5m_features(
    df_1m: pl.DataFrame,
    datetime_col: str = "timestamp",
    *,
    rsi_period: int = _CFG["rsi"]["period"],
    rsi_roc_period: int = _CFG["rsi"]["roc_period"],
    adx_period: int = _CFG["adx"]["period"],
    adx_roc_period: int = _CFG["adx"]["roc_period"],
) -> pl.DataFrame:
    """
    Resamples 1m data to 5m and computes RSI and ADX features (with ROCs)
    on the 5m bars using the pure indicator functions.

    The returned dataframe contains only the datetime column and the 5m
    feature columns; its timestamps are shifted forward by 5 minutes so the
    features can be joined onto 1m data without lookahead bias.

    Period defaults are loaded from config/symbol_features.yml.
    """
    # Resample to 5m
    df_5m = df_1m.group_by_dynamic(datetime_col, every="5m").agg([
        pl.col("high").max().alias("high"),
        pl.col("low").min().alias("low"),
        pl.col("close").last().alias("close")
    ])

    # Compute RSI and ADX (and their ROCs) on 5m data. The indicator
    # functions are timeperiod-agnostic; we rename them here to make their 5m provenance explicit.
    df_5m = add_rsi(df_5m, period=rsi_period, roc_period=rsi_roc_period)
    df_5m = add_adx(df_5m, period=adx_period, roc_period=adx_roc_period)

    df_5m_features = df_5m.select([
        pl.col(datetime_col),
        pl.col("rsi").alias("rsi_5m"),
        pl.col("adx").alias("adx_5m"),
        pl.col("rsi_roc").alias("rsi_5m_roc"),
        pl.col("adx_roc").alias("adx_5m_roc"),
    ])

    # Shift 5m timestamp forward by 5 minutes to avoid lookahead bias
    # The 5m bar at 09:00 ends at 09:04:59, so the features are available at 09:05:00
    df_5m_features = df_5m_features.with_columns(
        (pl.col(datetime_col) + pl.duration(minutes=5)).alias(datetime_col)
    )

    # Drop rows with nulls in features (from rolling windows/indicators)
    df_5m_features = df_5m_features.drop_nulls()

    return df_5m_features


def build_symbol_features(df: pl.DataFrame, datetime_col: str = "timestamp") -> pl.DataFrame:
    """
    Orchestrates building both 1m and 5m features for a single symbol's bar data,
    then joins the 5m features onto the 1m frame via an as-of backward join.
    """
    df_1m = compute_1m_features(df, datetime_col)
    df_5m_features = compute_5m_features(df_1m, datetime_col)

    # Join asof backward
    # For each 1m row, find the most recent 5m feature row where 5m_timestamp <= 1m_timestamp
    df_joined = df_1m.join_asof(df_5m_features, on=datetime_col, strategy="backward")

    return df_joined
