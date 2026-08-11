import sys
from pathlib import Path

import polars as pl
import polars.selectors as cs

from src.features.daily_regime import calculate_daily_features
from src.features.intraday_regime import calculate_intraday_features
from src.utils.data import resample_15m, resample_daily
from src.utils.load_config import load_config
from src.utils.symbol_data import load_symbol_data


def load_regime_data(
    data_dir: Path,
    config_path: Path,
    start_period: str,
    end_period: str,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, list[pl.DataFrame]]:
    """
    Load VIX/market daily OHLCV, Nifty 15m bars, and Nifty-100 daily frames
    for Tier 1 regime feature calculation.

    Returns:
        vix_daily, market_daily, market_15m, nifty100_daily_dfs
    """
    print(f"Loading symbols configuration from {config_path}...")
    config = load_config(config_path)

    vix_symbol = config.get("vix_symbol", "^INDIAVIX")
    market_symbol = config.get("market_symbol", "^NSEI")
    nifty100_symbols = config.get("nifty100_symbols", [])

    print(f"1. Loading VIX features from {vix_symbol}...")
    vix_path = data_dir / f"{vix_symbol}.csv"
    if not vix_path.exists():
        print(f"Error: VIX data {vix_path} not found.")
        sys.exit(1)

    vix_df = load_symbol_data(vix_path, start_period=start_period, end_period=end_period)
    vix_daily = resample_daily(vix_df).with_columns(pl.col("date").cast(pl.Date))

    print(f"2. Loading Market features from {market_symbol}...")
    market_path = data_dir / f"{market_symbol}.csv"
    if not market_path.exists():
        print(f"Error: Market data {market_path} not found.")
        sys.exit(1)

    market_df = load_symbol_data(market_path, start_period=start_period, end_period=end_period)
    market_daily = resample_daily(market_df).with_columns(pl.col("date").cast(pl.Date))
    market_15m = resample_15m(market_df)

    print(f"3. Loading {len(nifty100_symbols)} stocks for breadth features...")
    nifty100_daily_dfs: list[pl.DataFrame] = []

    for sym in nifty100_symbols:
        sym_path = data_dir / f"{sym}.csv"
        if not sym_path.exists():
            print(f"Warning: Symbol data {sym_path} not found. Skipping.")
            continue

        stock_df = load_symbol_data(sym_path, start_period=start_period, end_period=end_period)
        stock_daily = resample_daily(stock_df).with_columns(pl.col("date").cast(pl.Date))
        nifty100_daily_dfs.append(stock_daily)

    if not nifty100_daily_dfs:
        print("Error: No data processed.")
        sys.exit(1)

    return vix_daily, market_daily, market_15m, nifty100_daily_dfs


def build_regime_features(
    vix_daily: pl.DataFrame,
    market_daily: pl.DataFrame,
    market_15m: pl.DataFrame,
    nifty100_daily_dfs: list[pl.DataFrame],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Compute market-level daily regime features and Nifty 15m intraday HMM
    emissions from loaded frames (no per-stock / sector columns).

    Returns:
        final_daily_df, final_intraday_df
    """
    print("4. Calculating daily market-level features...")
    final_daily_df = calculate_daily_features(vix_daily, market_daily, nifty100_daily_dfs)

    print("5. Calculating intraday features...")
    final_intraday_df = calculate_intraday_features(market_15m, market_daily)

    # Clean up NaNs / Infs
    final_daily_df = final_daily_df.with_columns(
        pl.when(cs.float().is_infinite()).then(None).otherwise(cs.float()).name.keep()
    )
    final_intraday_df = final_intraday_df.with_columns(
        pl.when(cs.float().is_infinite()).then(None).otherwise(cs.float()).name.keep()
    )

    return final_daily_df, final_intraday_df
