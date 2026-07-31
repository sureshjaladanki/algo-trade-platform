import argparse
from pathlib import Path
from collections import defaultdict
import numpy as np
import polars as pl
import yaml

from src.features.core import atr
from src.utils.data import load_csv_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN = REPO_ROOT / "data" / "GOLDEN"

def load_trade_sectors(config_path: Path) -> dict[str, list[str]]:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    sectors = {}
    for sector_name, sector_data in cfg.get("sectoral_indices", {}).items():
        symbols = sector_data.get("trade_symbols", [])
        if symbols:
            sectors[sector_name] = symbols
    return sectors

def analyze_symbol(
    symbol: str,
    start_period: str,
    end_period: str,
    horizons_mins: list[int],
    sample_stride: int
) -> dict[int, dict[str, pl.Series]]:
    path = GOLDEN / f"{symbol}.csv"
    if not path.exists():
        return {}

    df = load_csv_data(path, datetime_col="date")

    # Filter by test period
    df = filter_by_period(df, start_period, end_period, datetime_col="date")

    if df.is_empty():
        return {}

    # Resample to 15m candles
    df = df.group_by_dynamic("date", every="15m").agg([
        pl.col("open").first(),
        pl.col("high").max(),
        pl.col("low").min(),
        pl.col("close").last(),
        pl.col("volume").sum()
    ])
    
    # Calculate ATR14 on 15m candles
    df = df.with_columns(
        atr14=atr("high", "low", "close", 14)
    )
    df = df.drop_nulls(subset=["atr14", "close"])
    
    if df.is_empty():
        return {}

    results = {}
    price = pl.col("close")
    atr_col = pl.col("atr14")
    
    exprs = []
    # Horizons in minutes, 15m per bar
    for h_mins in horizons_mins:
        bars = h_mins // 15
        
        # absolute forward return as % change
        pct_change = (price.shift(-bars) / price - 1.0).abs() * 100.0
        
        # absolute forward return as a multiple of ATR
        atr_mult = (price.shift(-bars) - price).abs() / atr_col
        
        exprs.extend([
            pct_change.alias(f"pct_{h_mins}"),
            atr_mult.alias(f"atr_mult_{h_mins}")
        ])
        
    df = df.with_columns(exprs).drop_nulls(subset=[f"pct_{h_mins}" for h_mins in horizons_mins])
    
    if df.is_empty():
        return {}
        
    # Uniform bar subsample for speed
    if sample_stride > 1:
        df = df.with_row_index("_i").filter(pl.col("_i") % sample_stride == 0).drop("_i")
        
    for h_mins in horizons_mins:
        results[h_mins] = {
            "pct": df[f"pct_{h_mins}"],
            "atr_mult": df[f"atr_mult_{h_mins}"]
        }
        
    return results

def main():
    parser = argparse.ArgumentParser(description="Analyze sector volatility (ATR multiple and % change) over fixed minute horizons.")
    parser.add_argument("--config", type=str, default="config/trade_sectoral_symbols.yml", help="Path to the sectoral symbols config")
    parser.add_argument(
        "--test-period",
        type=str,
        required=True,
        help="Test period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy (e.g. 03/2020-03/2021)",
    )
    parser.add_argument("--sample-stride", type=int, default=1, help="Keep every Nth bar for speed (default: 1, exact)")
    args = parser.parse_args()
    
    config_path = REPO_ROOT / args.config
    start_period, end_period = parse_period_range(args.test_period)
    
    sectors = load_trade_sectors(config_path)
    horizons = [30, 60, 90, 120] # 0-2 hrs in 30 mins intervals
    
    # Store aggregated metrics: sector -> horizon -> metric -> list of arrays
    sector_data = defaultdict(lambda: defaultdict(lambda: {"pct": [], "atr_mult": []}))
    
    print(f"Running volatility analysis for period: {start_period} to {end_period}")
    print(f"Horizons evaluated: {horizons} minutes")
    print(f"Sample stride: {args.sample_stride}")
    
    for sector_name, symbols in sectors.items():
        print(f"\nProcessing sector: {sector_name} ({len(symbols)} symbols)")
        for i, sym in enumerate(symbols, 1):
            res = analyze_symbol(sym, start_period, end_period, horizons, args.sample_stride)
            print(f"  [{i:02d}/{len(symbols)}] {sym}", flush=True)
            if not res:
                continue
            for h in horizons:
                sector_data[sector_name][h]["pct"].append(res[h]["pct"].to_numpy())
                sector_data[sector_name][h]["atr_mult"].append(res[h]["atr_mult"].to_numpy())
    
    # Generate report
    print("\n" + "="*85)
    print(f"{'Sector':<22} | {'Mins':<5} | {'Metric':<9} | {'P50 (Median)':<15} | {'P75':<15}")
    print("="*85)
    
    for sector_name, symbols in sectors.items():
        if sector_name not in sector_data:
            continue
            
        for h in horizons:
            pct_list = sector_data[sector_name][h]["pct"]
            atr_mult_list = sector_data[sector_name][h]["atr_mult"]
            
            if not pct_list:
                continue
                
            pct_arr = np.concatenate(pct_list)
            atr_mult_arr = np.concatenate(atr_mult_list)
            
            # Clean arrays by removing any NaNs or Infs
            pct_arr = pct_arr[np.isfinite(pct_arr)]
            atr_mult_arr = atr_mult_arr[np.isfinite(atr_mult_arr)]
            
            if len(pct_arr) == 0 or len(atr_mult_arr) == 0:
                continue
                
            p50_pct, p75_pct = np.median(pct_arr), np.percentile(pct_arr, 75)
            p50_atr, p75_atr = np.median(atr_mult_arr), np.percentile(atr_mult_arr, 75)
            
            # Print ATR multiple and % change for the current horizon
            print(f"{sector_name:<22} | {h:>5} | {'ATR Mult':<9} | {p50_atr:>15.4f} | {p75_atr:>15.4f}")
            print(f"{'':<22} | {'':<5} | {'% Change':<9} | {p50_pct:>14.4f}% | {p75_pct:>14.4f}%")
        print("-" * 85)

if __name__ == "__main__":
    main()
