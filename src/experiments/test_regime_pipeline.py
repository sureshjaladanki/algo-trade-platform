import argparse
from pathlib import Path

from src.pipelines.build_regime_features import build_regime_features
from src.pipelines.regime_pipeline import fit_intraday_hmm, predict_intraday_hmm
from src.regime.intraday import override_intraday_regime
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN = REPO_ROOT / "data" / "GOLDEN"


def main():
    parser = argparse.ArgumentParser(description="Test Regime Pipeline with cascade gates.")
    parser.add_argument(
        "--config",
        type=str,
        default="config/market_sectoral_symbols.yml",
        help="Path to the market / sectoral symbols config",
    )
    parser.add_argument(
        "--train-period",
        type=str,
        default="2015-2017",
        help="Train period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy",
    )
    parser.add_argument(
        "--test-period",
        type=str,
        default="2018-2018",
        help="Test period: yyyy-yyyy (e.g. 2017-2018) or mm/yyyy-mm/yyyy",
    )
    args = parser.parse_args()

    config_path = REPO_ROOT / args.config
    train_start, train_end = parse_period_range(args.train_period)
    test_start, test_end = parse_period_range(args.test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    print(f"Loading data and building features from {load_start} to {load_end}...")
    daily_features, intraday_features = build_regime_features(
        data_dir=GOLDEN,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )

    print(f"Splitting into train ({args.train_period}) and test ({args.test_period})...")
    daily_train = filter_by_period(daily_features, train_start, train_end, datetime_col="date")
    daily_test = filter_by_period(daily_features, test_start, test_end, datetime_col="date")
    intraday_train = filter_by_period(
        intraday_features, train_start, train_end, datetime_col="date"
    )
    intraday_test = filter_by_period(
        intraday_features, test_start, test_end, datetime_col="date"
    )

    print(f"   Train daily: {daily_train.shape}, Test daily: {daily_test.shape}")
    print(f"   Train intraday: {intraday_train.shape}, Test intraday: {intraday_test.shape}")

    if daily_train.height == 0 or daily_test.height == 0:
        print("Error: Train or test daily dataframe is empty. Check your periods.")
        return

    print("Fitting Intraday HMM on train data (only on data passing daily filter)...")
    hmm_model = fit_intraday_hmm(daily_train, intraday_train, random_state=42, n_iter=100)

    print("Predicting Regimes on test data...")
    results = predict_intraday_hmm(daily_test, intraday_test, hmm_model)
    # Intraday hard rules (not inside the HMM).
    results = override_intraday_regime(results)

    print("\nDaily Regime Counts:")
    daily_counts = results.group_by("daily_regime").len().sort("len", descending=True)
    print(daily_counts.to_dict(as_series=False))

    print("\nIntraday Regime Counts:")
    intraday_counts = results.group_by("intraday_regime").len().sort("len", descending=True)
    print(intraday_counts.to_dict(as_series=False))

    print("\nCross-tabulation (Daily vs Intraday):")
    cross_tab = (
        results.group_by(["daily_regime", "intraday_regime"])
        .len()
        .sort(["daily_regime", "len"], descending=[False, True])
    )
    print(cross_tab.to_dict(as_series=False))


if __name__ == "__main__":
    main()
