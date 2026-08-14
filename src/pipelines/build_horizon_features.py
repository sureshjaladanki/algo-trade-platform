import sys
from pathlib import Path

import polars as pl

from src.features.horizon import calculate_horizon_features
from src.features.regime_horizon import calculate_regime_horizon_features
from src.labels.horizon import calculate_horizon_labels
from src.labels.triple_barrier import calculate_triple_barrier_labels
from src.utils.data import resample_15m, resample_daily
from src.utils.eval_common import H_BARS
from src.utils.load_config import load_config
from src.utils.symbol_data import load_symbol_data


def load_horizon_data(
    data_dir: Path,
    config_path: Path,
    start_period: str,
    end_period: str,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """
    Load tradable-symbol 15m/daily OHLCV plus sector-index 15m closes for Tier 2.

    Tradable names come from ``sectoral_indices[*].trade_symbols`` (with sector
    tags). Broader ``nifty100_symbols`` stay in the Regime Tier 1 builder.

    Returns:
        stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty

    Intraday frames keep the bar timestamp column as `date` (Datetime), matching
    Regime Tier 1. Daily frames use `date` as Date. `sector_15m` is always a
    DataFrame (empty schema if no sector files loaded).
    """
    config = load_config(config_path)
    market_symbol = config.get("market_symbol", "^NSEI")
    sectoral_indices: dict = config.get("sectoral_indices", {}) or {}

    market_path = data_dir / f"{market_symbol}.csv"
    if not market_path.exists():
        print(f"Error: Market data {market_path} not found.")
        sys.exit(1)

    print(f"Loading market OHLCV from {market_symbol}...")
    market_raw = load_symbol_data(
        market_path, start_period=start_period, end_period=end_period
    )
    nifty_15m = resample_15m(market_raw).select(
        ["date", "open", "high", "low", "close", "volume"]
    )
    daily_nifty = resample_daily(market_raw).with_columns(pl.col("date").cast(pl.Date))

    print(f"Loading trade symbols from {len(sectoral_indices)} sectors...")
    stock_frames: list[pl.DataFrame] = []
    daily_frames: list[pl.DataFrame] = []
    sector_frames: list[pl.DataFrame] = []

    for sector_name, sector_data in sectoral_indices.items():
        for sym in sector_data.get("trade_symbols") or []:
            sym_path = data_dir / f"{sym}.csv"
            if not sym_path.exists():
                print(f"Warning: Symbol data {sym_path} not found. Skipping.")
                continue
            raw = load_symbol_data(
                sym_path, start_period=start_period, end_period=end_period
            )
            if raw.height == 0:
                continue
            stock_frames.append(
                resample_15m(raw)
                .with_columns(
                    pl.lit(sym).alias("symbol"),
                    pl.lit(sector_name).alias("sector"),
                )
                .select(
                    [
                        "symbol",
                        "sector",
                        "date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                    ]
                )
            )
            daily_frames.append(
                resample_daily(raw)
                .with_columns(
                    pl.col("date").cast(pl.Date),
                    pl.lit(sym).alias("symbol"),
                    pl.lit(sector_name).alias("sector"),
                )
                .select(
                    [
                        "symbol",
                        "sector",
                        "date",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                    ]
                )
            )

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
            .with_columns(pl.lit(sector_name).alias("sector"))
            .select(["date", "sector", "close"])
        )

    if not stock_frames:
        print("Error: No stock data loaded for Horizon universe.")
        sys.exit(1)

    stock_15m = pl.concat(stock_frames, how="vertical_relaxed").sort(
        ["symbol", "date"]
    )
    daily_stock = pl.concat(daily_frames, how="vertical_relaxed").sort(
        ["symbol", "date"]
    )

    sector_15m = (
        pl.concat(sector_frames, how="vertical_relaxed").sort(["sector", "date"])
        if sector_frames
        else pl.DataFrame(
            schema={
                "date": nifty_15m.schema["date"],
                "sector": pl.Utf8,
                "close": pl.Float64,
            }
        )
    )
    return stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty


def build_horizon_features(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    sector_df: pl.DataFrame,
    daily_stock_df: pl.DataFrame,
    daily_nifty_df: pl.DataFrame,
    daily_regime_df: pl.DataFrame,
    intraday_regime_df: pl.DataFrame,
    regime_df: pl.DataFrame,
) -> pl.DataFrame:
    """
    Compute Tier 2 Horizon features and labels from loaded universe frames.

    Auction-bleed / NO_TRADE bars stay in the frame; sleeve masks are applied
    by the pipeline.

    Args:
        nifty_df: 15m Nifty OHLCV (emissions attached from intraday_regime_df).
        daily_regime_df: Tier 1 daily features (must include vol_regime_ratio).
        intraday_regime_df: Tier 1 intraday emissions (r_15, vwap_dist).
        regime_df: Post-hysteresis daily_regime / intraday_regime predictions.

    Returns:
        Per-bar Horizon frame with features, H=6 labels/TB, cascade regimes,
        and regime-episode features.
    """
    # Attach Tier 1 emissions used as Horizon pass-throughs.
    emissions = intraday_regime_df.select(["date", "r_15", "vwap_dist"])
    nifty_with_emissions = nifty_df.join(emissions, on="date", how="left")

    features_df = calculate_horizon_features(
        stock_df,
        nifty_with_emissions,
        sector_df,
        daily_stock_df,
        daily_nifty_df,
        daily_regime_df,
    )
    labels_df = calculate_horizon_labels(
        stock_df, nifty_with_emissions, horizon_bars=H_BARS
    )

    horizon_df = features_df.join(labels_df, on=["symbol", "date"], how="inner")

    # Index-level Tier 1 regimes broadcast to all names.
    horizon_df = horizon_df.join(
        regime_df.select(["date", "daily_regime", "intraday_regime"]),
        on="date",
        how="inner",
    )
    horizon_df = calculate_regime_horizon_features(horizon_df)

    tb_df = calculate_triple_barrier_labels(
        stock_df, nifty_with_emissions, horizon_bars=H_BARS
    )
    horizon_df = horizon_df.join(tb_df, on=["symbol", "date"], how="left")
    return horizon_df
