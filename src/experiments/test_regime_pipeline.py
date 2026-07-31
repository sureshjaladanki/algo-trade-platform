import argparse
from pathlib import Path

import polars as pl

from src.features.daily import calculate_daily_features
from src.features.intraday import calculate_intraday_features
from src.pipelines.regime_pipeline import fit_intraday_hmm, predict_intraday_hmm
from src.utils.data import resample_15m, resample_daily
from src.utils.date import filter_by_period, parse_period_range
from src.utils.symbol_data import load_symbol_data

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN = REPO_ROOT / "data" / "GOLDEN"

def main():
    parser = argparse.ArgumentParser(description="Test Regime Pipeline with cascade gates.")
    parser.add_argument(
        "--train-period",
        type=str,
        default="2015-2016",
        help="Train period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy",
    )
    parser.add_argument(
        "--test-period",
        type=str,
        default="2017-2017",
        help="Test period: yyyy-yyyy (e.g. 2017-2018) or mm/yyyy-mm/yyyy",
    )
    args = parser.parse_args()

    train_start, train_end = parse_period_range(args.train_period)
    test_start, test_end = parse_period_range(args.test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    # Use TCS as proxy for symbol, CNXIT as proxy for index, INDIAVIX as VIX
    sym_path = GOLDEN / "TCS.NS.csv"
    index_path = GOLDEN / "^CNXIT.csv"
    vix_path = GOLDEN / "^INDIAVIX.csv"

    if not all(p.exists() for p in [sym_path, index_path, vix_path]):
        print("Required data files not found.")
        return

    print(f"Loading data ({load_start} to {load_end})...")
    sym_df = load_symbol_data(sym_path, start_period=load_start, end_period=load_end)
    index_df = load_symbol_data(index_path, start_period=load_start, end_period=load_end)
    vix_df = load_symbol_data(vix_path, start_period=load_start, end_period=load_end)

    print("Resampling daily data...")
    sym_daily = resample_daily(sym_df)
    index_daily = resample_daily(index_df)
    vix_daily = resample_daily(vix_df)

    print("Resampling 15m data...")
    sym_15m = resample_15m(sym_df)

    print("Calculating features...")

    # Ensure date is Date type for daily features
    sym_daily = sym_daily.with_columns(pl.col("date").cast(pl.Date))
    index_daily = index_daily.with_columns(pl.col("date").cast(pl.Date))
    vix_daily = vix_daily.with_columns(pl.col("date").cast(pl.Date))

    daily_features = calculate_daily_features(sym_daily, index_daily, vix_daily).with_columns([
        pl.lit("^CNXIT").alias("sector"),
        pl.lit("TCS.NS").alias("symbol"),
    ])
    intraday_features = calculate_intraday_features(sym_15m, sym_daily).with_columns([
        pl.lit("^CNXIT").alias("sector"),
        pl.lit("TCS.NS").alias("symbol"),
    ])

    print(f"Splitting into train ({args.train_period}) and test ({args.test_period})...")
    daily_train = filter_by_period(daily_features, train_start, train_end, datetime_col="date")
    daily_test = filter_by_period(daily_features, test_start, test_end, datetime_col="date")
    intraday_train = filter_by_period(intraday_features, train_start, train_end, datetime_col="datetime")
    intraday_test = filter_by_period(intraday_features, test_start, test_end, datetime_col="datetime")

    print(f"   Train daily: {daily_train.shape}, Test daily: {daily_test.shape}")
    print(f"   Train intraday: {intraday_train.shape}, Test intraday: {intraday_test.shape}")

    if daily_train.height == 0 or daily_test.height == 0:
        print("Error: Train or test daily dataframe is empty. Check your periods.")
        return

    print("Fitting Intraday HMM on train data (only on data passing daily filter)...")
    hmm_model = fit_intraday_hmm(daily_train, intraday_train, random_state=42, n_iter=100)

    print("Predicting Regimes on test data...")
    results = predict_intraday_hmm(daily_test, intraday_test, hmm_model)

    # Print some stats
    print("\nDaily Regime Counts:")
    daily_counts = results.group_by("daily_regime").len().sort("len", descending=True)
    print(daily_counts.to_dict(as_series=False))

    print("\nIntraday Regime Counts:")
    intraday_counts = results.group_by("intraday_regime").len().sort("len", descending=True)
    print(intraday_counts.to_dict(as_series=False))

    print("\nCross-tabulation (Daily vs Intraday):")
    # Group by both to see the cascade effect
    cross_tab = results.group_by(["daily_regime", "intraday_regime"]).len().sort(["daily_regime", "len"], descending=[False, True])
    print(cross_tab.to_dict(as_series=False))

if __name__ == "__main__":
    main()
