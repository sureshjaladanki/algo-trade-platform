import sys
from pathlib import Path
from typing import Dict

import polars as pl
import polars.selectors as cs
    

from .market_features import build_market_features
from .sectoral_features import build_sectoral_features
from .symbol_features import build_symbol_features
from .features.long_target import add_long_target
from .features.relative_strength import add_relative_strength
from .features.roc import add_roc
from .utils import load_config
from .utils.symbol_data import load_symbol_data

_TRADE_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "trade_features.yml"
_TRADE_CFG = load_config(_TRADE_CONFIG_PATH)


def compute_1m_trade_features(
    trade_df: pl.DataFrame,
    training_config: Dict,
    datetime_col: str = "timestamp",
) -> pl.DataFrame:
    """
    Computes 1-minute trade features, including the long-only triple-barrier target.

    `datetime_col` names the time column on `trade_df` for callers that resample or
    join on time; barrier labeling uses `close` and `natr_col` from the config.
    """
    lookahead_minutes = int(training_config.get("lookahead_minutes", 30))
    take_profit_natr = float(training_config.get("take_profit_natr", 2.0))
    stop_loss_natr = float(training_config.get("stop_loss_natr", 1.5))
    natr_col = str(training_config.get("natr_col", "natr_5m"))
    target = training_config.get("target", {})
    target_classes = target.get("classes", {})

    trade_df = add_long_target(
        trade_df,
        lookahead_minutes=lookahead_minutes,
        natr_col=natr_col,
        take_profit_natr=take_profit_natr,
        stop_loss_natr=stop_loss_natr,
        target_classes=target_classes,
    )

    return trade_df


def compute_5m_trade_features(
    trade_df: pl.DataFrame,
    datetime_col: str = "timestamp",
    *,
    roc_period: int = _TRADE_CFG["relative_strength"]["roc"]
) -> pl.DataFrame:
    """
    Resamples 1m trade data to 5m and returns a 5m feature dataframe.

    The returned timestamps are shifted forward by 5 minutes so the features
    can be joined onto 1m data without lookahead bias.
    """
    # 1) Resample trade df to 5m
    df_5m = trade_df.group_by_dynamic(datetime_col, every="5m").agg(
        [
            pl.col("high").max().alias("high"),
            pl.col("low").min().alias("low"),
            pl.col("close").last().alias("close"),
            pl.col("sector_close").last().alias("sector_close"),
        ]
    )

    df_5m = add_relative_strength(
        df_5m,
        close_col="close",
        sector_close_col="sector_close",
    )
    df_5m = add_roc(df_5m, roc_col="rs_ratio", period=roc_period)

    # 2) Select only feature columns
    df_5m_features = df_5m.select(
        [
            pl.col(datetime_col),
            pl.col("rs_ratio").alias("rs_5m_ratio"),
            pl.col("rs_ratio_roc").alias("rs_5m_roc"),
        ]
    )

    # Shift 5m timestamp forward by 5 minutes to avoid lookahead bias
    df_5m_features = df_5m_features.with_columns(
        (pl.col(datetime_col) + pl.duration(minutes=5)).alias(datetime_col)
    )
    df_5m_features = df_5m_features.drop_nulls()

    return df_5m_features

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
    vix_features = vix_df.select(["date", "market_vix_5m"])

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

        sector_features = sector_df.select(["date", "sector", "sector_close"])

        for sym, sym_df in symbol_dfs.items():
            print(f"   Building features for symbol: {sym}")
            sym_df = build_symbol_features(sym_df, datetime_col="date")
            
            # Add symbol identifier
            sym_df = sym_df.with_columns(pl.lit(sym).alias("symbol"))

            # Join sector features
            sym_df = sym_df.join_asof(sector_features, on="date", strategy="backward")

            # Join market features
            sym_df = sym_df.join_asof(vix_features, on="date", strategy="backward")

            sym_df = compute_1m_trade_features(
                sym_df, training_config=training_config, datetime_col="date"
            )
            df_5m_features = compute_5m_trade_features(sym_df, datetime_col="date")

            sym_df = sym_df.join_asof(df_5m_features, on="date", strategy="backward")

            all_symbols_df.append(sym_df)

    if not all_symbols_df:
        print("Error: No data processed.")
        sys.exit(1)

    print("3. Combining all symbol data...")
    final_df = pl.concat(all_symbols_df, how="vertical_relaxed")

    # Clean up any infinite values generated during feature engineering (e.g. division by zero)
    # Replace with NaN (null in Polars) so XGBoost can route it through its missing-value branch.
    final_df = final_df.with_columns(
        pl.when(cs.float().is_infinite()).then(None).otherwise(cs.float()).name.keep()
    )

    # Cast float64 to float32 to match XGBoost internal types and handle out-of-bounds values
    final_df = final_df.with_columns(
        cs.float().cast(pl.Float32)
    )
    
    # Replace any new infs (which might have been created by float32 cast of large values) with null
    final_df = final_df.with_columns(
        pl.when(cs.float().is_infinite()).then(None).otherwise(cs.float()).name.keep()
    )

    print(f"   Combined data shape: {final_df.shape}")
    return final_df
