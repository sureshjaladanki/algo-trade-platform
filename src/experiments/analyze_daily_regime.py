import argparse
from pathlib import Path

from src.pipelines.build_regime_features import (
    build_regime_features,
    load_regime_data,
)
from src.regime.daily import classify_daily_regime
from src.regime.types import DailyRegime
from src.utils.date import parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN = REPO_ROOT / "data" / "GOLDEN"


def main():
    parser = argparse.ArgumentParser(description="Analyze market-level daily regime categorization.")
    parser.add_argument(
        "--config",
        type=str,
        default="config/market_sectoral_symbols.yml",
        help="Path to the market / sectoral symbols config",
    )
    parser.add_argument(
        "--test-period",
        type=str,
        required=True,
        help="Test period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy (e.g. 03/2020-03/2021)",
    )
    args = parser.parse_args()

    config_path = REPO_ROOT / args.config
    start_period, end_period = parse_period_range(args.test_period)

    vix_daily, market_daily, market_15m, nifty100_daily_dfs = load_regime_data(
        data_dir=GOLDEN,
        config_path=config_path,
        start_period=start_period,
        end_period=end_period,
    )
    daily_features, _ = build_regime_features(
        vix_daily, market_daily, market_15m, nifty100_daily_dfs
    )

    if daily_features.is_empty():
        print("Daily features are empty for the given period.")
        return

    regime_df = classify_daily_regime(daily_features)

    counts = regime_df.group_by("daily_regime").len().to_dict(as_series=False)
    regime_counts = {
        DailyRegime.NO_TRADE.value: 0,
        DailyRegime.HOSTILE.value: 0,
        DailyRegime.SUPPORTIVE.value: 0,
        DailyRegime.AMBIGUOUS.value: 0,
    }
    for regime, count in zip(counts["daily_regime"], counts["len"]):
        if regime is not None:
            regime_counts[regime] = count

    total = sum(regime_counts.values())
    print(f"\nDaily regime counts ({args.test_period}, n={total})")
    print("=" * 50)
    for regime in (
        DailyRegime.NO_TRADE,
        DailyRegime.HOSTILE,
        DailyRegime.SUPPORTIVE,
        DailyRegime.AMBIGUOUS,
    ):
        n = regime_counts[regime.value]
        pct = (100.0 * n / total) if total else 0.0
        print(f"{regime.value:<12} {n:>6}  ({pct:5.1f}%)")


if __name__ == "__main__":
    main()
