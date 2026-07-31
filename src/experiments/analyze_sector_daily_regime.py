import argparse
from collections import defaultdict
from pathlib import Path

import yaml

from src.features.daily import calculate_daily_features
from src.regime.daily import classify_daily_regime
from src.regime.types import DailyRegime
from src.utils.data import resample_daily
from src.utils.date import parse_period_range
from src.utils.symbol_data import load_symbol_data

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN = REPO_ROOT / "data" / "GOLDEN"

def load_trade_sectors(config_path: Path) -> tuple[str, dict[str, list[str]]]:
    cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    regime_symbol = cfg.get("regime_symbol", "^INDIAVIX")
    sectors = {}
    for sector_name, sector_data in cfg.get("sectoral_indices", {}).items():
        symbols = sector_data.get("trade_symbols", [])
        if symbols:
            sectors[sector_name] = symbols
    return regime_symbol, sectors

def main():
    parser = argparse.ArgumentParser(description="Analyze sector-wise symbol metrics for daily regime categorization.")
    parser.add_argument("--config", type=str, default="config/trade_sectoral_symbols.yml", help="Path to the sectoral symbols config")
    parser.add_argument(
        "--test-period",
        type=str,
        required=True,
        help="Test period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy (e.g. 03/2020-03/2021)",
    )
    args = parser.parse_args()
    
    config_path = REPO_ROOT / args.config
    start_period, end_period = parse_period_range(args.test_period)
    
    regime_symbol, sectors = load_trade_sectors(config_path)
    
    vix_path = GOLDEN / f"{regime_symbol}.csv"
    if not vix_path.exists():
        print(f"VIX data not found at {vix_path}")
        return
        
    vix_df = load_symbol_data(vix_path, start_period=start_period, end_period=end_period)
    vix_daily = resample_daily(vix_df)
    
    if vix_daily.is_empty():
        print("VIX data is empty for the given period.")
        return
        
    results = defaultdict(dict)
    
    for sector_name, symbols in sectors.items():
        index_path = GOLDEN / f"{sector_name}.csv"
        if not index_path.exists():
            print(f"Sector index data not found at {index_path}")
            continue
            
        index_df = load_symbol_data(index_path, start_period=start_period, end_period=end_period)
        index_daily = resample_daily(index_df)
        
        if index_daily.is_empty():
            print(f"Sector index data is empty for {sector_name}")
            continue
            
        for sym in symbols:
            sym_path = GOLDEN / f"{sym}.csv"
            if not sym_path.exists():
                continue
                
            sym_df = load_symbol_data(sym_path, start_period=start_period, end_period=end_period)
            sym_daily = resample_daily(sym_df)
            
            if sym_daily.is_empty():
                continue
                
            features = calculate_daily_features(sym_daily, index_daily, vix_daily)
            regime_df = classify_daily_regime(features)
            
            # Count regimes
            counts = regime_df.group_by("daily_regime").len().to_dict(as_series=False)
            regime_counts = {DailyRegime.NO_TRADE.value: 0, DailyRegime.HOSTILE.value: 0, DailyRegime.SUPPORTIVE.value: 0, DailyRegime.AMBIGUOUS.value: 0}
            
            for regime, count in zip(counts["daily_regime"], counts["len"]):
                if regime is not None:
                    regime_counts[regime] = count
                    
            results[sector_name][sym] = regime_counts
            
    # Print tabular output
    for sector_name, sym_data in results.items():
        print(f"\nSector: {sector_name}")
        print("=" * 70)
        print(f"{'Symbol':<20} | {'NO_TRADE':<10} | {'HOSTILE':<10} | {'SUPPORTIVE':<10} | {'AMBIGUOUS':<10}")
        print("-" * 70)
        for sym, counts in sym_data.items():
            print(f"{sym:<20} | {counts[DailyRegime.NO_TRADE.value]:<10} | {counts[DailyRegime.HOSTILE.value]:<10} | {counts[DailyRegime.SUPPORTIVE.value]:<10} | {counts[DailyRegime.AMBIGUOUS.value]:<10}")
        print("=" * 70)

if __name__ == "__main__":
    main()
