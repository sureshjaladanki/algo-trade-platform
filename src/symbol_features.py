from pathlib import Path

import polars as pl

from .features import (
    add_trading_day,
    add_minute_of_day,
    add_vwap,
    add_ema,
    add_bollinger,
    add_relative_volume,
    add_atr_gap,
    add_atr,
    add_rsi,
    add_adx,
    add_roc,
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
    ema_fast_period: int = _CFG["ema"]["fast_period"],
    ema_slow_period: int = _CFG["ema"]["slow_period"],
    bb_period: int = _CFG["bollinger"]["period"],
    rel_vol_period: int = _CFG["relative_volume"]["period"],
    atr_period: int = _CFG["atr_gap"]["period"],
) -> pl.DataFrame:
    """
    Computes 1-minute features: VWAP, EMA (slow), minute_of_the_day, Bollinger %B, EMA slope (fast),
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

    # 2. EMA slope (fast) and close vs EMA % (slow)
    df = add_ema(df, fast_period=ema_fast_period, slow_period=ema_slow_period)

    # Add lags for EMA features (1m timeline). No `.over("symbol")` here: this
    # dataframe is one symbol per call; `symbol` is added later in `trade_features`.
    # for period in [ema_slow_period]:
    #     pct_col = f"close_ema_{period}_pct"
    #     df = df.with_columns([
    #         pl.col(pct_col).shift(1).alias(f"{pct_col}_lag1"),
    #         pl.col(pct_col).shift(2).alias(f"{pct_col}_lag2"),
    #     ])

    # 3. Bollinger %B
    df = add_bollinger(df, period=bb_period)

    # 4. Relative Volume (vol / rvol)
    df = add_relative_volume(df, datetime_col, period=rel_vol_period)

    # 5. Daily ATR and Gap (close - prev_day_close) / ATR
    df = add_atr_gap(df, period=atr_period)

    df = df.drop("trading_day")

    return df


def compute_5m_features(
    df_1m: pl.DataFrame,
    datetime_col: str = "timestamp",
    *,
    rsi_period: int = _CFG["rsi"]["period"],
    adx_period: int = _CFG["adx"]["period"],
    atr_period: int = _CFG["atr"]["period"],
    roc_period: int = _CFG["roc"]["period"],
) -> pl.DataFrame:
    """
    Resamples 1m data to 5m and computes ATR, RSI, and ADX (+DI / -DI)
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
        pl.col("close").last().alias("close"),
        pl.col("ema_8").last().alias("ema_8"),
    ])

    # Raw ATR on 5m (gap-free first bar of day), then RSI and ADX (+DI/-DI).
    # NATR is derived on the 1m frame after join_asof (see `build_symbol_features`).
    df_5m = add_atr(df_5m, datetime_col=datetime_col, period=atr_period)
    df_5m = add_roc(df_5m, roc_col="atr", period=roc_period)
    df_5m = add_rsi(df_5m, period=rsi_period)
    df_5m = add_roc(df_5m, roc_col="rsi", period=roc_period)
    df_5m = add_adx(df_5m, period=adx_period)
    df_5m = add_roc(df_5m, roc_col="adx", period=roc_period)
    df_5m = add_roc(df_5m, roc_col="ema_8", period=roc_period)

    # Add lags for RSI (5m timeline)
    # df_5m = df_5m.with_columns([
    #     pl.col("rsi").shift(1).alias("rsi_5m_lag1"),
    #     pl.col("rsi").shift(2).alias("rsi_5m_lag2"),
    # ])

    df_5m_features = df_5m.select([
        pl.col(datetime_col),
        pl.col("rsi").alias("rsi_5m"),
        pl.col("rsi_roc").alias("rsi_5m_roc"),
        pl.col("adx").alias("adx_5m"),
        pl.col("adx_roc").alias("adx_5m_roc"),
        pl.col("di_diff").alias("di_diff_5m"),
        pl.col("atr").alias("atr_5m"),
        pl.col("atr_roc").alias("atr_5m_roc"),
        pl.col("ema_8_roc").alias("fast_ema_5m_roc"),
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

    5m bars carry raw ATR (`atr_5m`); after the join, `natr_5m = atr_5m / close` on the
    1m grid. Raw `atr_5m` columns is dropped so downstream code uses `natr_5m` instead.
    """
    df = compute_1m_features(df, datetime_col)
    df_5m_features = compute_5m_features(df, datetime_col)

    # Join asof backward
    # For each 1m row, find the most recent 5m feature row where 5m_timestamp <= 1m_timestamp
    df_joined = df.join_asof(df_5m_features, on=datetime_col, strategy="backward")

    # Normalize joined 5m ATR by the current 1m close; z-score NATR on the 1m timeline.
    df_joined = df_joined.with_columns((pl.col("atr_5m") / pl.col("close")).alias("natr_5m"))
    # Drop raw ATR, EMA (fast), and EMA (slow)
    df_joined = df_joined.drop("atr_5m", "ema_8", "ema_21")

    return df_joined
