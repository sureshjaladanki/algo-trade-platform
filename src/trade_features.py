import sys
from pathlib import Path
from typing import Dict

import polars as pl

from .market_features import build_market_features
from .sectoral_features import build_sectoral_features
from .symbol_features import build_symbol_features
from .features.long_target import add_long_target
from .utils import load_config
from .utils.symbol_data import load_symbol_data


def build_all_features(
    data_dir: Path,
    symbols_config_path: Path,
    training_config_path: Path,
    start_year: int,
    end_year: int,
) -> pl.DataFrame:
    print(f"Loading symbols configuration from {symbols_config_path}...")
    config = load_config(symbols_config_path)

    print(f"Loading training configuration from {training_config_path}...")
    training_config = load_config(training_config_path)

    regime_symbol = config.get("regime_symbol", "^INDIAVIX")
    sectoral_indices = config.get("sectoral_indices", {})

    lookahead_minutes = int(training_config.get("lookahead_minutes", 15))
    stop_loss_pct = training_config.get("stop_loss_pct")
    take_profit_pct = training_config.get("take_profit_pct")

    target = training_config.get("target", {})
    target_classes = target.get("classes", {})

    # Single source of truth for the sector <-> integer-code mapping. Built from
    # the YAML config so train, test, and inference all share identical codes.
    sector_enum = pl.Enum(list(sectoral_indices.keys()))

    print(f"1. Building market features from {regime_symbol}...")
    vix_path = data_dir / f"{regime_symbol}.csv"
    if not vix_path.exists():
        print(f"Error: Market data {vix_path} not found.")
        sys.exit(1)

    vix_df = load_symbol_data(vix_path, start_year=start_year, end_year=end_year)
    vix_df = build_market_features(vix_df, datetime_col="date")

    # We only need the market features to join later
    vix_features = vix_df.select(["date", "market_vix_5m", "market_vix_roc_5m", "trading_session"])

    all_symbols_df = []

    for sector_symbol, sector_info in sectoral_indices.items():
        print(f"2. Processing sector: {sector_symbol}")
        sector_path = data_dir / f"{sector_symbol}.csv"
        if not sector_path.exists():
            print(f"Warning: Sector data {sector_path} not found. Skipping.")
            continue

        sector_df = load_symbol_data(sector_path, start_year=start_year, end_year=end_year)

        trade_symbols = sector_info.get("trade_symbols", [])
        symbol_dfs: Dict[str, pl.DataFrame] = {}

        for sym in trade_symbols:
            sym_path = data_dir / f"{sym}.csv"
            if sym_path.exists():
                symbol_dfs[sym] = load_symbol_data(
                    sym_path,
                    start_year=start_year,
                    end_year=end_year,
                )
            else:
                print(f"Warning: Symbol data {sym_path} not found. Skipping.")

        if not symbol_dfs:
            print(f"No trade symbols loaded for sector {sector_symbol}. Skipping.")
            continue

        print(f"   Building sectoral features for {sector_symbol}...")
        sector_df = build_sectoral_features(sector_df, symbol_dfs, datetime_col="date")
        # Add sector identifier as an Enum so it survives concat/joins and surfaces
        # in pandas as `category` for XGBoost's native categorical splits.
        sector_df = sector_df.with_columns(
            pl.lit(sector_symbol).cast(sector_enum).alias("sector")
        )

        sector_features = sector_df.select(["date", "sector", "sector_index_roc_5m", "sector_ad_5m"])

        for sym, sym_df in symbol_dfs.items():
            print(f"   Building features for symbol: {sym}")
            sym_df = build_symbol_features(sym_df, datetime_col="date")

            # Join sector features
            sym_df = sym_df.join_asof(sector_features, on="date", strategy="backward")

            # Join market features
            sym_df = sym_df.join_asof(vix_features, on="date", strategy="backward")

            # Generate long target
            sym_df = add_long_target(
                sym_df,
                lookahead_minutes=lookahead_minutes,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
                target_classes=target_classes,
            )

            # Add symbol identifier
            sym_df = sym_df.with_columns(pl.lit(sym).alias("symbol"))

            all_symbols_df.append(sym_df)

    if not all_symbols_df:
        print("Error: No data processed.")
        sys.exit(1)

    print("3. Combining all symbol data...")
    final_df = pl.concat(all_symbols_df, how="vertical_relaxed")

    print(f"   Combined data shape: {final_df.shape}")
    return final_df
