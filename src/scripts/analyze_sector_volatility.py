import argparse
from pathlib import Path
from collections import defaultdict
import numpy as np
import polars as pl
import yaml

from src.symbol_features import build_symbol_features
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
    periods: list[int],
    sample_stride: int
) -> dict[int, dict[str, pl.Series]]:
    path = GOLDEN / f"{symbol}.csv"
    if not path.exists():
        return {}

    df = pl.read_csv(path)
    df = df.with_columns(pl.col("date").str.to_datetime().alias("timestamp"))
    
    # Filter by test period
    df = filter_by_period(df, start_period, end_period, datetime_col="timestamp")
    
    if df.is_empty():
        return {}

    # Build features to get natr_5m
    df = build_symbol_features(df, datetime_col="timestamp")
    df = df.drop_nulls(subset=["natr_5m", "close"])
    
    if df.is_empty():
        return {}

    results = {}
    price = pl.col("close")
    natr = pl.col("natr_5m")
    
    exprs = []
    for p in periods:
        # absolute return
        ret = (price.shift(-p) / price - 1.0).abs()
        pct_change = ret * 100.0
        natr_change = ret / natr
        
        exprs.extend([
            pct_change.alias(f"pct_{p}"),
            natr_change.alias(f"natr_{p}")
        ])
        
    df = df.with_columns(exprs).drop_nulls(subset=[f"pct_{p}" for p in periods])
    
    if df.is_empty():
        return {}
        
    # Uniform bar subsample for speed (apply AFTER shift so we don't mess up the bar count for future returns)
    if sample_stride > 1:
        df = df.with_row_index("_i").filter(pl.col("_i") % sample_stride == 0).drop("_i")
        
    for p in periods:
        results[p] = {
            "pct": df[f"pct_{p}"],
            "natr": df[f"natr_{p}"]
        }
        
    return results

def main():
    parser = argparse.ArgumentParser(description="Analyze sector volatility (NATR and % change) over fixed minute periods.")
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
    periods = [15, 22, 30, 37, 45, 52, 60]
    
    # Store aggregated metrics: sector -> period -> metric -> list of arrays
    sector_data = defaultdict(lambda: defaultdict(lambda: {"pct": [], "natr": []}))
    
    print(f"Running volatility analysis for period: {start_period} to {end_period}")
    print(f"Periods evaluated: {periods} minutes")
    print(f"Sample stride: {args.sample_stride}")
    
    for sector_name, symbols in sectors.items():
        print(f"\nProcessing sector: {sector_name} ({len(symbols)} symbols)")
        for i, sym in enumerate(symbols, 1):
            res = analyze_symbol(sym, start_period, end_period, periods, args.sample_stride)
            print(f"  [{i:02d}/{len(symbols)}] {sym}", flush=True)
            if not res:
                continue
            for p in periods:
                sector_data[sector_name][p]["pct"].append(res[p]["pct"].to_numpy())
                sector_data[sector_name][p]["natr"].append(res[p]["natr"].to_numpy())
    
    # Generate report
    print("\n" + "="*85)
    print(f"{'Sector':<22} | {'Mins':<5} | {'Metric':<7} | {'P50 (Median)':<15} | {'P75':<15}")
    print("="*85)
    
    for sector_name, symbols in sectors.items():
        if sector_name not in sector_data:
            continue
            
        for p in periods:
            pct_list = sector_data[sector_name][p]["pct"]
            natr_list = sector_data[sector_name][p]["natr"]
            
            if not pct_list:
                continue
                
            pct_arr = np.concatenate(pct_list)
            natr_arr = np.concatenate(natr_list)
            
            # Clean arrays by removing any NaNs or Infs
            pct_arr = pct_arr[np.isfinite(pct_arr)]
            natr_arr = natr_arr[np.isfinite(natr_arr)]
            
            if len(pct_arr) == 0 or len(natr_arr) == 0:
                continue
                
            p50_pct, p75_pct = np.median(pct_arr), np.percentile(pct_arr, 75)
            p50_natr, p75_natr = np.median(natr_arr), np.percentile(natr_arr, 75)
            
            # Print NATR and % change for the current period
            print(f"{sector_name:<22} | {p:>5} | {'NATR':<7} | {p50_natr:>15.4f} | {p75_natr:>15.4f}")
            print(f"{'':<22} | {'':<5} | {'% Change':<7} | {p50_pct:>14.4f}% | {p75_pct:>14.4f}%")
        print("-" * 85)

if __name__ == "__main__":
    main()
