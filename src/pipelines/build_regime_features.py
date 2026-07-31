import sys
from pathlib import Path

import polars as pl
import polars.selectors as cs

from src.features.daily import calculate_daily_features
from src.features.intraday import calculate_intraday_features
from src.utils.data import resample_15m, resample_daily
from src.utils.load_config import load_config
from src.utils.symbol_data import load_symbol_data


def build_regime_features(
    data_dir: Path,
    symbols_config_path: Path,
    start_period: str,
    end_period: str,
) -> pl.DataFrame:
    """
    Reads the config, loops over all sectors and their symbols, calculates daily
    and intraday regime features, and returns a concatenated DataFrame.
    """
    print(f"Loading symbols configuration from {symbols_config_path}...")
    config = load_config(symbols_config_path)

    regime_symbol = config.get("regime_symbol", "^INDIAVIX")
    sectoral_indices = config.get("sectoral_indices", {})

    print(f"1. Loading market features from {regime_symbol}...")
    vix_path = data_dir / f"{regime_symbol}.csv"
    if not vix_path.exists():
        print(f"Error: Market data {vix_path} not found.")
        sys.exit(1)

    vix_df = load_symbol_data(vix_path, start_period=start_period, end_period=end_period)
    vix_daily = resample_daily(vix_df)
    vix_daily = vix_daily.with_columns(pl.col("date").cast(pl.Date))

    all_symbols_daily = []
    all_symbols_intraday = []

    for sector_symbol, sector_info in sectoral_indices.items():
        print(f"2. Processing sector: {sector_symbol}")
        sector_path = data_dir / f"{sector_symbol}.csv"
        if not sector_path.exists():
            print(f"Warning: Sector data {sector_path} not found. Skipping.")
            continue

        index_df = load_symbol_data(sector_path, start_period=start_period, end_period=end_period)
        index_daily = resample_daily(index_df)
        index_daily = index_daily.with_columns(pl.col("date").cast(pl.Date))

        trade_symbols = sector_info.get("trade_symbols", [])

        for sym in trade_symbols:
            sym_path = data_dir / f"{sym}.csv"
            if not sym_path.exists():
                print(f"Warning: Symbol data {sym_path} not found. Skipping.")
                continue
                
            sym_df = load_symbol_data(sym_path, start_period=start_period, end_period=end_period)
            
            # Resample to daily and 15m
            sym_daily = resample_daily(sym_df)
            sym_daily = sym_daily.with_columns(pl.col("date").cast(pl.Date))
            
            sym_15m = resample_15m(sym_df)
            
            # 1. Calculate Daily Features
            daily_features = calculate_daily_features(sym_daily, index_daily, vix_daily)
            daily_features = daily_features.with_columns([
                pl.lit(sector_symbol).alias("sector"),
                pl.lit(sym).alias("symbol")
            ])
            all_symbols_daily.append(daily_features)
            
            # 2. Calculate Intraday Features
            intraday_features = calculate_intraday_features(sym_15m, sym_daily)
            intraday_features = intraday_features.with_columns([
                pl.lit(sector_symbol).alias("sector"),
                pl.lit(sym).alias("symbol")
            ])
            all_symbols_intraday.append(intraday_features)

    if not all_symbols_daily or not all_symbols_intraday:
        print("Error: No data processed.")
        sys.exit(1)

    print("3. Combining all symbol data...")
    final_daily_df = pl.concat(all_symbols_daily, how="vertical_relaxed")
    final_intraday_df = pl.concat(all_symbols_intraday, how="vertical_relaxed")

    # Clean up NaNs / Infs for daily
    final_daily_df = final_daily_df.with_columns(
        pl.when(cs.float().is_infinite()).then(None).otherwise(cs.float()).name.keep()
    )
    final_intraday_df = final_intraday_df.with_columns(
        pl.when(cs.float().is_infinite()).then(None).otherwise(cs.float()).name.keep()
    )

    return final_daily_df, final_intraday_df
