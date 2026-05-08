import argparse
import sys
from pathlib import Path
from typing import Dict

import polars as pl

from .data import load_csv_data
from .market_features import build_market_features
from .sectoral_features import build_sectoral_features
from .symbol_features import build_symbol_features
from .features.long_target import generate_long_target
from .model import train_xgboost_model
from .utils import load_config


def parse_period(period_str: str) -> tuple[int, int]:
    if "-" in period_str:
        start, end = period_str.split("-")
        start_year = int(start)
        if len(end) == 2:
            end_year = int(start[:2] + end)
        else:
            end_year = int(end)
        return start_year, end_year
    else:
        return int(period_str), int(period_str)


def filter_by_period(df: pl.DataFrame, start_year: int, end_year: int, datetime_col: str = "date") -> pl.DataFrame:
    return df.filter(
        (pl.col(datetime_col).dt.year() >= start_year) &
        (pl.col(datetime_col).dt.year() <= end_year)
    )


def _load_symbol_data(
    csv_path: Path,
    *,
    start_year: int,
    end_year: int,
    datetime_col: str = "date",
) -> pl.DataFrame:
    df = load_csv_data(csv_path, datetime_col=datetime_col)
    return filter_by_period(df, start_year, end_year, datetime_col=datetime_col)


# Filtering the final final_df is correct logically, 
# but it’s slower because you compute features for years you’ll throw away.
def run_pipeline(
    data_dir: Path,
    symbols_config_path: Path,
    training_config_path: Path,
    train_period: str,
    test_period: str,
):
    train_start, train_end = parse_period(train_period)
    test_start, test_end = parse_period(test_period)

    # Filter raw inputs early for speed/memory, but keep a warmup window so
    # rolling features (EMA/BB/RSI/ADX/etc.) have enough history
    start_year = min(train_start, test_start)
    end_year = max(train_end, test_end)
    
    print(f"Loading symbols configuration from {symbols_config_path}...")
    config = load_config(symbols_config_path)

    print(f"Loading training configuration from {training_config_path}...")
    training_config = load_config(training_config_path)
    
    regime_symbol = config.get("regime_symbol", "^INDIAVIX")
    sectoral_indices = config.get("sectoral_indices", {})

    lookahead_minutes = int(training_config.get("lookahead_minutes", 15))
    stop_loss_pct = training_config.get("stop_loss_pct")
    take_profit_pct = training_config.get("take_profit_pct")

    # Single source of truth for the sector <-> integer-code mapping. Built from
    # the YAML config so train, test, and inference all share identical codes.
    sector_enum = pl.Enum(list(sectoral_indices.keys()))

    print(f"1. Building market features from {regime_symbol}...")
    vix_path = data_dir / f"{regime_symbol}.csv"
    if not vix_path.exists():
        print(f"Error: Market data {vix_path} not found.")
        sys.exit(1)
        
    vix_df = _load_symbol_data(vix_path, start_year=start_year, end_year=end_year)
    vix_df = build_market_features(vix_df, datetime_col="date")
    
    # We only need the market features to join later
    vix_features = vix_df.select(["date", "market_vix_5m", "market_vix_roc_5m"])
    
    all_symbols_df = []
    
    for sector_symbol, sector_info in sectoral_indices.items():
        print(f"2. Processing sector: {sector_symbol}")
        sector_path = data_dir / f"{sector_symbol}.csv"
        if not sector_path.exists():
            print(f"Warning: Sector data {sector_path} not found. Skipping.")
            continue
            
        sector_df = _load_symbol_data(sector_path, start_year=start_year, end_year=end_year)
        
        trade_symbols = sector_info.get("trade_symbols", [])
        symbol_dfs: Dict[str, pl.DataFrame] = {}
        
        for sym in trade_symbols:
            sym_path = data_dir / f"{sym}.csv"
            if sym_path.exists():
                symbol_dfs[sym] = _load_symbol_data(
                    sym_path,
                    start_year=start_year,
                    end_year=end_year
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
            sym_df = generate_long_target(
                sym_df,
                lookahead_minutes=lookahead_minutes,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
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
    
    print(f"4. Splitting data into train ({train_period}) and test ({test_period})...")
    df_train = filter_by_period(final_df, train_start, train_end)
    df_test = filter_by_period(final_df, test_start, test_end)
    
    print(f"   Train shape: {df_train.shape}, Test shape: {df_test.shape}")
    
    if len(df_train) == 0 or len(df_test) == 0:
        print("Error: Train or test dataframe is empty. Check your periods.")
        sys.exit(1)
    
    print("5. Training XGBoost model and logging to MLflow...")
    feature_cols = [
        # Symbol (1m)
        "close_vwap_zscore",
        "close_ema_14_pct",
        "minute_of_day",
        "bb_pct_b",
        "vol_z_score",
        "rvol",
        "gap_atr",
        # Symbol (5m joined to 1m)
        "rsi_5m",
        "adx_5m",
        "rsi_5m_roc",
        "adx_5m_roc",
        # Market (5m joined to 1m)
        "market_vix_5m",
        "market_vix_roc_5m",
        # Sector (5m joined to 1m)
        "sector",
        "sector_index_roc_5m",
        "sector_ad_5m",
    ]
    
    # Ensure all feature columns exist
    missing_cols = [col for col in feature_cols if col not in final_df.columns]
    if missing_cols:
        print(f"Warning: Missing feature columns: {missing_cols}")
        feature_cols = [col for col in feature_cols if col in final_df.columns]
    
    clf, acc = train_xgboost_model(df_train, df_test, feature_cols=feature_cols, target_col="long_target")
    print("====================================")
    print(f"Pipeline finished. Final test accuracy: {acc:.4f}")
    print("Run `mlflow ui` in your terminal to view the experiment tracking.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Algo Trading ML Platform pipeline")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN", help="Path to the GOLDEN data directory")
    parser.add_argument("--config", type=str, default="config/trade_sectoral_symbols.yml", help="Path to the sectoral symbols config")
    parser.add_argument("--training-config", type=str, default="config/model_training.yml", help="Path to the model training config")
    parser.add_argument("--train-period", type=str, required=True, help="Training period: yyyy or yyyy-yy (ex: 2015, 2015-18)")
    parser.add_argument("--test-period", type=str, required=True, help="Test period: yyyy or yyyy-yy (ex: 2015, 2015-18)")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    symbols_config_path = Path(args.config)
    training_config_path = Path(args.training_config)
    
    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist.")
        sys.exit(1)
        
    if not symbols_config_path.exists():
        print(f"Error: Config file {symbols_config_path} does not exist.")
        sys.exit(1)

    if not training_config_path.exists():
        print(f"Error: Training config file {training_config_path} does not exist.")
        sys.exit(1)
         
    run_pipeline(data_dir, symbols_config_path, training_config_path, args.train_period, args.test_period)
