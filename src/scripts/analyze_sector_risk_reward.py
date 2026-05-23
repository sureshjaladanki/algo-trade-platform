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

def analyze_symbol_risk_reward(
    symbol: str,
    start_period: str,
    end_period: str,
    lookahead_minutes: int,
    sl_natr: float = 1.5,
    tp_natr: float = 2.0,
    sample_stride: int = 1
) -> dict[str, pl.Series]:
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
    df = df.drop_nulls(subset=["natr_5m", "close", "high", "low"])
    
    if df.is_empty():
        return {}

    # Uniform bar subsample for speed (apply BEFORE lookahead but need all data for lookahead)
    # Actually, we need to evaluate every T, but we can subsample the T's we evaluate.
    # Let's keep a row index to filter later.
    df = df.with_row_index("_idx")
    
    price_close = pl.col("close")
    natr = pl.col("natr_5m")
    tp_delta = natr * tp_natr
    sl_delta = natr * sl_natr
    
    tp_hits = []
    sl_hits = []
    
    for k in range(1, lookahead_minutes + 1):
        # future high and low relative to current close
        fut_high_ret = pl.col("high").shift(-k) / price_close - 1.0
        fut_low_ret = pl.col("low").shift(-k) / price_close - 1.0
        
        tp_hits.append(pl.when(fut_high_ret >= tp_delta).then(k))
        sl_hits.append(pl.when(fut_low_ret <= -sl_delta).then(k))
        
    inf = lookahead_minutes + 1
    first_tp = pl.min_horizontal(tp_hits).fill_null(inf)
    first_sl = pl.min_horizontal(sl_hits).fill_null(inf)
    
    df = df.with_columns(
        _tp_time=first_tp,
        _sl_time=first_sl
    )
    
    # We drop rows that do not have a full lookahead window
    df = df.filter(pl.col("close").shift(-lookahead_minutes).is_not_null())
    
    if sample_stride > 1:
        df = df.filter(pl.col("_idx") % sample_stride == 0)
        
    if df.is_empty():
        return {}

    total_evaluated = len(df)

    # Label outcomes
    # If both hit at the same time and it's <= lookahead_minutes, assume Risk (SL) is hit first conservatively
    df = df.with_columns(
        outcome=pl.when((pl.col("_sl_time") <= pl.col("_tp_time")) & (pl.col("_sl_time") <= lookahead_minutes)).then(pl.lit("Risk"))
        .when((pl.col("_tp_time") < pl.col("_sl_time")) & (pl.col("_tp_time") <= lookahead_minutes)).then(pl.lit("Reward"))
        .otherwise(pl.lit("None")),
        time_to_hit=pl.min_horizontal("_sl_time", "_tp_time")
    )
    
    df_resolved = df.filter(pl.col("outcome") != "None")
    
    return {
        "Total_Evaluated": total_evaluated,
        "Risk": df_resolved.filter(pl.col("outcome") == "Risk")["time_to_hit"] if not df_resolved.is_empty() else pl.Series(dtype=pl.Int32),
        "Reward": df_resolved.filter(pl.col("outcome") == "Reward")["time_to_hit"] if not df_resolved.is_empty() else pl.Series(dtype=pl.Int32)
    }

def main():
    parser = argparse.ArgumentParser(description="Analyze sector risk/reward times.")
    parser.add_argument("--config", type=str, default="config/trade_sectoral_symbols.yml", help="Path to the sectoral symbols config")
    parser.add_argument(
        "--test-period",
        type=str,
        required=True,
        help="Test period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy (e.g. 03/2020-03/2021)",
    )
    parser.add_argument("--lookahead", type=int, default=60, help="Max lookahead minutes for hit evaluation (default: 60)")
    parser.add_argument("--sl-natr", type=float, default=1.5, help="Stop loss normalized ATR multiplier (default: 1.5)")
    parser.add_argument("--tp-natr", type=float, default=2.0, help="Take profit normalized ATR multiplier (default: 2.0)")
    parser.add_argument("--sample-stride", type=int, default=1, help="Keep every Nth bar for speed (default: 1, exact)")
    args = parser.parse_args()
    
    config_path = REPO_ROOT / args.config
    start_period, end_period = parse_period_range(args.test_period)
    
    sectors = load_trade_sectors(config_path)
    
    # Store aggregated metrics: sector -> outcome -> list of times
    sector_data = defaultdict(lambda: {"Total_Evaluated": 0, "Risk": [], "Reward": []})
    
    print(f"Running risk/reward analysis for period: {start_period} to {end_period}")
    print(f"Risk: {args.sl_natr} NATR, Reward: {args.tp_natr} NATR, Lookahead: {args.lookahead} minutes")
    print(f"Sample stride: {args.sample_stride}")
    
    for sector_name, symbols in sectors.items():
        print(f"\nProcessing sector: {sector_name} ({len(symbols)} symbols)")
        for i, sym in enumerate(symbols, 1):
            res = analyze_symbol_risk_reward(
                sym, 
                start_period, 
                end_period, 
                args.lookahead, 
                args.sl_natr, 
                args.tp_natr, 
                args.sample_stride
            )
            print(f"  [{i:02d}/{len(symbols)}] {sym}", flush=True)
            if not res:
                continue
            sector_data[sector_name]["Total_Evaluated"] += res.get("Total_Evaluated", 0)
            if len(res.get("Risk", [])) > 0:
                sector_data[sector_name]["Risk"].append(res["Risk"].to_numpy())
            if len(res.get("Reward", [])) > 0:
                sector_data[sector_name]["Reward"].append(res["Reward"].to_numpy())
                
    # Generate report
    percentiles = list(range(10, 101, 10))
    
    header_cols = [f"P{p} (m/TP/SL)".center(18) for p in percentiles]
    
    print("\n" + "="*235)
    print(f"{'Sector':<22} | {'Total':<6} | " + " | ".join(header_cols))
    print("="*235)
    
    for sector_name, data in sectors.items():
        if sector_name not in sector_data:
            continue
            
        total_eval = sector_data[sector_name]["Total_Evaluated"]
        if total_eval == 0:
            continue
            
        risk_list = sector_data[sector_name]["Risk"]
        reward_list = sector_data[sector_name]["Reward"]
        
        risk_arr = np.concatenate(risk_list) if risk_list else np.array([])
        reward_arr = np.concatenate(reward_list) if reward_list else np.array([])
        
        all_hit_times = np.concatenate([risk_arr, reward_arr])
        all_hit_times = all_hit_times[np.isfinite(all_hit_times)]
        
        if len(all_hit_times) == 0:
            print(f"{sector_name:<22} | {total_eval:<6} | No resolved trades")
            continue
            
        cols = []
        for p in percentiles:
            t_p = np.percentile(all_hit_times, p)
            tp_pct = np.sum(reward_arr <= t_p) / total_eval * 100.0
            sl_pct = np.sum(risk_arr <= t_p) / total_eval * 100.0
            
            val = f"{t_p:4.1f}/{tp_pct:4.1f}%/{sl_pct:4.1f}%"
            cols.append(f"{val:>18}")
            
        print(f"{sector_name:<22} | {total_eval:<6} | " + " | ".join(cols))
            
    print("-" * 235)

if __name__ == "__main__":
    main()
