import sys
from pathlib import Path

import polars as pl

from src.utils.data import resample_15m, resample_daily
from src.utils.load_config import load_config
from src.utils.symbol_data import load_symbol_data


def load_horizon_universe(
    data_dir: Path,
    config_path: Path,
    start_period: str,
    end_period: str,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame | None, pl.DataFrame, pl.DataFrame]:
    """
    Load Nifty-100 15m/daily OHLCV plus sector-index 15m closes for Tier 2.

    Returns:
        stock_15m, nifty_15m, sector_15m | None, daily_stock, daily_nifty
    """
    config = load_config(config_path)
    market_symbol = config.get("market_symbol", "^NSEI")
    nifty100_symbols: list[str] = config.get("nifty100_symbols", [])
    sectoral_indices: dict = config.get("sectoral_indices", {}) or {}

    symbol_to_sector: dict[str, str] = {}
    for sector_name, sector_data in sectoral_indices.items():
        for sym in sector_data.get("trade_symbols", []) or []:
            symbol_to_sector.setdefault(sym, sector_name)

    market_path = data_dir / f"{market_symbol}.csv"
    if not market_path.exists():
        print(f"Error: Market data {market_path} not found.")
        sys.exit(1)

    print(f"Loading market OHLCV from {market_symbol}...")
    market_raw = load_symbol_data(
        market_path, start_period=start_period, end_period=end_period
    )
    nifty_15m = (
        resample_15m(market_raw)
        .rename({"date": "datetime"})
        .select(["datetime", "open", "high", "low", "close", "volume"])
    )
    daily_nifty = resample_daily(market_raw).with_columns(pl.col("date").cast(pl.Date))

    print(f"Loading {len(nifty100_symbols)} stock symbols for Horizon features...")
    stock_frames: list[pl.DataFrame] = []
    daily_frames: list[pl.DataFrame] = []
    for sym in nifty100_symbols:
        sym_path = data_dir / f"{sym}.csv"
        if not sym_path.exists():
            print(f"Warning: Symbol data {sym_path} not found. Skipping.")
            continue
        raw = load_symbol_data(
            sym_path, start_period=start_period, end_period=end_period
        )
        if raw.height == 0:
            continue
        sector = symbol_to_sector.get(sym)
        stock_15 = (
            resample_15m(raw)
            .rename({"date": "datetime"})
            .with_columns(
                pl.lit(sym).alias("symbol"),
                pl.lit(sector).alias("sector"),
            )
            .select(
                ["symbol", "sector", "datetime", "open", "high", "low", "close", "volume"]
            )
        )
        daily = (
            resample_daily(raw)
            .with_columns(
                pl.col("date").cast(pl.Date),
                pl.lit(sym).alias("symbol"),
            )
            .select(["symbol", "date", "open", "high", "low", "close", "volume"])
        )
        stock_frames.append(stock_15)
        daily_frames.append(daily)

    if not stock_frames:
        print("Error: No stock data loaded for Horizon universe.")
        sys.exit(1)

    stock_15m = pl.concat(stock_frames, how="vertical_relaxed").sort(
        ["symbol", "datetime"]
    )
    daily_stock = pl.concat(daily_frames, how="vertical_relaxed").sort(["symbol", "date"])

    sector_frames: list[pl.DataFrame] = []
    for sector_name in sectoral_indices:
        sector_path = data_dir / f"{sector_name}.csv"
        if not sector_path.exists():
            print(f"Warning: Sector index {sector_path} not found. Skipping.")
            continue
        sector_raw = load_symbol_data(
            sector_path, start_period=start_period, end_period=end_period
        )
        if sector_raw.height == 0:
            continue
        sector_frames.append(
            resample_15m(sector_raw)
            .rename({"date": "datetime"})
            .with_columns(pl.lit(sector_name).alias("sector"))
            .select(["datetime", "sector", "close"])
        )

    sector_15m = (
        pl.concat(sector_frames, how="vertical_relaxed").sort(["sector", "datetime"])
        if sector_frames
        else None
    )
    return stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty
