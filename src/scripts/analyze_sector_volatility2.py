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
    targets: list[float],
    sample_stride: int
) -> dict[float, dict[str, pl.Series]]:
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
        
    close = df["close"].to_numpy()
    timestamps = df["timestamp"].to_numpy()
    natr = df["natr_5m"].to_numpy()
    
    N = len(close)
    
    # Subsample start points for speed
    if sample_stride > 1:
        start_indices = np.arange(0, N, sample_stride)
    else:
        start_indices = np.arange(N)
        
    # Filter out start points where natr is 0 or invalid to avoid divide by zero
    valid_starts = (natr[start_indices] > 0) & np.isfinite(natr[start_indices])
    start_indices = start_indices[valid_starts]
        
    start_close = close[start_indices]
    start_natr = natr[start_indices]
    start_time = timestamps[start_indices]
    
    N_sub = len(start_indices)
    
    first_hit_mins = {t: np.full(N_sub, np.nan) for t in targets}
    first_hit_pct = {t: np.full(N_sub, np.nan) for t in targets}
    hit_mask = {t: np.zeros(N_sub, dtype=bool) for t in targets}
    
    # Max lookforward to search for the target hit (e.g. ~40 trading days of 1-min bars)
    max_lookforward = 15000 
    
    for k in range(1, max_lookforward + 1):
        valid_mask = (start_indices + k) < N
        if not np.any(valid_mask):
            break
            
        v_idx = np.where(valid_mask)[0]
        
        # Early stopping check:
        # If all valid indices have hit all targets, we can break early
        all_hit = True
        for t in targets:
            if not np.all(hit_mask[t][v_idx]):
                all_hit = False
                break
        if all_hit:
            break
            
        f_idx = start_indices[v_idx] + k
        
        # Absolute return
        ret = np.abs(close[f_idx] / start_close[v_idx] - 1.0)
        
        # NATR change
        natr_change = ret / start_natr[v_idx]
        
        # Calculate time difference in minutes
        time_diff = (timestamps[f_idx] - start_time[v_idx]).astype('timedelta64[m]').astype(float)
        
        for t in targets:
            new_hits = (natr_change >= t) & (~hit_mask[t][v_idx])
            
            if np.any(new_hits):
                hit_sub_idx = v_idx[new_hits]
                hit_mask[t][hit_sub_idx] = True
                first_hit_mins[t][hit_sub_idx] = time_diff[new_hits]
                first_hit_pct[t][hit_sub_idx] = ret[new_hits] * 100.0
                
    results = {}
    for t in targets:
        # filter out NaN (targets not hit within max_lookforward)
        hit = hit_mask[t]
        results[t] = {
            "mins": pl.Series(first_hit_mins[t][hit]),
            "pct": pl.Series(first_hit_pct[t][hit]),
        }
        
    return results


def main():
    parser = argparse.ArgumentParser(description="Analyze time to reach NATR targets.")
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
    
    # NATR from 0.5 to 3.0 in increments of +0.5
    targets = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    
    # Store aggregated metrics: sector -> target -> metric -> list of arrays
    sector_data = defaultdict(lambda: defaultdict(lambda: {"mins": [], "pct": []}))
    
    print(f"Running NATR target analysis for period: {start_period} to {end_period}")
    print(f"NATR Targets evaluated: {targets}")
    print(f"Sample stride: {args.sample_stride}")
    
    for sector_name, symbols in sectors.items():
        print(f"\nProcessing sector: {sector_name} ({len(symbols)} symbols)")
        for i, sym in enumerate(symbols, 1):
            res = analyze_symbol(sym, start_period, end_period, targets, args.sample_stride)
            print(f"  [{i:02d}/{len(symbols)}] {sym}", flush=True)
            if not res:
                continue
            for t in targets:
                if len(res[t]["mins"]) > 0:
                    sector_data[sector_name][t]["mins"].append(res[t]["mins"].to_numpy())
                    sector_data[sector_name][t]["pct"].append(res[t]["pct"].to_numpy())
    
    # Generate report
    print("\n" + "="*90)
    print(f"{'Sector':<22} | {'Target':<6} | {'P25 (mins)':<12} | {'P50 (mins)':<12} | {'P50 (% chg)':<12}")
    print("="*90)
    
    for sector_name, symbols in sectors.items():
        if sector_name not in sector_data:
            continue
            
        for t in targets:
            time_list = sector_data[sector_name][t]["mins"]
            pct_list = sector_data[sector_name][t]["pct"]
            
            if not time_list:
                continue
                
            time_arr = np.concatenate(time_list)
            pct_arr = np.concatenate(pct_list)
            
            # Clean arrays by removing any NaNs or Infs
            time_arr = time_arr[np.isfinite(time_arr)]
            pct_arr = pct_arr[np.isfinite(pct_arr)]
            
            if len(time_arr) == 0 or len(pct_arr) == 0:
                continue
                
            p25 = np.percentile(time_arr, 25)
            p50 = np.median(time_arr)
            p25_pct = np.percentile(pct_arr, 25)
            p50_pct = np.median(pct_arr)
            
            print(f"{sector_name:<22} | {t:>6.1f} | {p25:>12.1f} | {p50:>12.1f} | {p25_pct:>11.4f}% | {p50_pct:>11.4f}%")
        print("-" * 90)


if __name__ == "__main__":
    main()
