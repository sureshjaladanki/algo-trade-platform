"""Load 1m universe data and build Tier 3 Precision features."""

import sys
from pathlib import Path

import polars as pl

from src.features.precision import calculate_precision_features
from src.utils.load_config import load_config
from src.utils.symbol_data import load_symbol_data


def load_precision_data(
    data_dir: Path,
    config_path: Path,
    start_period: str,
    end_period: str,
    symbols: list[str] | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Load 1m OHLCV for Precision timing (no 15m resample).

    If `symbols` is provided, only those names are loaded (typically the
    Horizon registry universe for the eval window). Otherwise all
    ``sectoral_indices[*].trade_symbols`` are loaded.

    Returns:
        stock_1m, nifty_1m
    """
    config = load_config(config_path)
    market_symbol = config.get("market_symbol", "^NSEI")
    sectoral_indices: dict = config.get("sectoral_indices", {}) or {}

    market_path = data_dir / f"{market_symbol}.csv"
    if not market_path.exists():
        print(f"Error: Market data {market_path} not found.")
        sys.exit(1)

    print(f"Loading 1m market OHLCV from {market_symbol}...")
    nifty_1m = load_symbol_data(
        market_path, start_period=start_period, end_period=end_period
    ).select(["date", "open", "high", "low", "close", "volume"])

    if symbols is None:
        symbols = []
        for sector_data in sectoral_indices.values():
            symbols.extend(sector_data.get("trade_symbols") or [])
        symbols = sorted(set(symbols))

    print(f"Loading 1m stock OHLCV for {len(symbols)} symbols...")
    frames: list[pl.DataFrame] = []
    for sym in symbols:
        sym_path = data_dir / f"{sym}.csv"
        if not sym_path.exists():
            print(f"Warning: Symbol data {sym_path} not found. Skipping.")
            continue
        raw = load_symbol_data(
            sym_path, start_period=start_period, end_period=end_period
        )
        if raw.height == 0:
            continue
        frames.append(
            raw.with_columns(pl.lit(sym).alias("symbol")).select(
                ["symbol", "date", "open", "high", "low", "close", "volume"]
            )
        )

    if not frames:
        print("Error: No 1m stock data loaded for Precision universe.")
        sys.exit(1)

    stock_1m = pl.concat(frames, how="vertical_relaxed").sort(["symbol", "date"])
    return stock_1m, nifty_1m


def build_precision_features(
    stock_1m: pl.DataFrame,
    nifty_1m: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """Compute Tier 3 1m timing features (causal)."""
    return calculate_precision_features(stock_1m, nifty_1m)
