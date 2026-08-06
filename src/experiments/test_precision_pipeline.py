"""Smoke / diagnostics harness for Tier 3 Precision (mirrors test_horizon_pipeline)."""

import argparse
from pathlib import Path

import polars as pl

from src.pipelines.build_horizon_features import (
    build_horizon_features,
    load_horizon_data,
)
from src.pipelines.build_precision_features import (
    build_precision_features,
    load_precision_data,
)
from src.pipelines.build_regime_features import (
    build_regime_features,
    load_regime_data,
)
from src.pipelines.horizon_pipeline import predict_horizon_gbm
from src.pipelines.precision_pipeline import run_precision_on_scored
from src.pipelines.regime_pipeline import predict_intraday_hmm
from src.regime.intraday import override_intraday_regime
from src.utils.date import filter_by_period, parse_period_range
from src.utils.mlflow_loader import load_hmm_model, load_horizon_models

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN = REPO_ROOT / "data" / "GOLDEN"


def main():
    parser = argparse.ArgumentParser(
        description="Test Precision Pipeline with cascade gates."
    )
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
        help="Train period for Horizon: yyyy-yyyy or mm/yyyy-mm/yyyy",
    )
    parser.add_argument(
        "--test-period",
        type=str,
        default="2018-2018",
        help="Test period for Precision rules: yyyy-yyyy or mm/yyyy-mm/yyyy",
    )
    parser.add_argument(
        "--direction",
        type=str,
        default="both",
        choices=["long", "short", "both"],
        help="Sleeve direction to run (long, short, or both)",
    )
    parser.add_argument(
        "--regime-run-id",
        type=str,
        default=None,
        help="Optional Regime_Pipeline MLflow run id",
    )
    parser.add_argument(
        "--horizon-run-id",
        type=str,
        default=None,
        help="Optional Horizon_Pipeline MLflow run id",
    )
    args = parser.parse_args()

    config_path = REPO_ROOT / args.config
    train_start, train_end = parse_period_range(args.train_period)
    test_start, test_end = parse_period_range(args.test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    print(f"1. Loading regime data from {load_start} to {load_end}...")
    vix_daily, market_daily, market_15m, nifty100_daily_dfs = load_regime_data(
        data_dir=GOLDEN,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    print("   Building regime features...")
    daily_regime, intraday_regime = build_regime_features(
        vix_daily, market_daily, market_15m, nifty100_daily_dfs
    )

    print("2. Pulling fitted HMM from Regime_Pipeline experiment...")
    hmm_model, resolved_run_id = load_hmm_model(
        train_period=args.train_period,
        run_id=args.regime_run_id,
    )
    print(f"   Using Regime Run ID: {resolved_run_id}")

    print("3. Predicting Tier 1 regimes...")
    regime_preds = predict_intraday_hmm(
        daily_regime,
        intraday_regime,
        hmm_model,
        apply_hysteresis=True,
    )
    regime_preds = override_intraday_regime(regime_preds)
    regime_df = regime_preds.select(["date", "daily_regime", "intraday_regime"])

    print("4. Loading Horizon universe...")
    stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty = load_horizon_data(
        data_dir=GOLDEN,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )

    print("5. Building Horizon features / TB geometry...")
    horizon_df = build_horizon_features(
        stock_15m,
        nifty_15m,
        sector_15m,
        daily_stock,
        daily_nifty,
        daily_regime_df=daily_regime,
        intraday_regime_df=intraday_regime,
        regime_df=regime_df,
    )

    print(f"6. Filtering Horizon test window ({args.test_period})...")
    test_df = filter_by_period(horizon_df, test_start, test_end, datetime_col="date")
    print(f"   Test shape: {test_df.shape}")

    if test_df.height == 0:
        print("Error: empty Horizon test — check periods.")
        return

    print("7. Loading Horizon models from Horizon_Pipeline + scoring test...")
    directions = ["long", "short"] if args.direction == "both" else [args.direction]
    try:
        models, resolved_horizon_run_id = load_horizon_models(
            directions=directions,
            train_period=args.train_period,
            run_id=args.horizon_run_id,
        )
    except FileNotFoundError as exc:
        print(f"Error: No Horizon models loaded. {exc}")
        return

    print(f"   Using Horizon Run ID: {resolved_horizon_run_id}")
    scored_dfs = [
        predict_horizon_gbm(test_df, model) for model in models.values()
    ]
    for sleeve, scored_sleeve in zip(models.keys(), scored_dfs):
        print(f"   Scored {sleeve} rows: {scored_sleeve.height}")

    scored = pl.concat(scored_dfs, how="diagonal")

    print("8. Loading 1m + building Precision features...")
    symbols = scored.select("symbol").unique().to_series().to_list()
    stock_1m, nifty_1m = load_precision_data(
        data_dir=GOLDEN,
        config_path=config_path,
        start_period=test_start,
        end_period=test_end,
        symbols=symbols,
    )
    features_1m = build_precision_features(stock_1m, nifty_1m)
    print(f"   1m feature rows: {features_1m.height}")

    print("9. Running Precision rules...")
    registry, trades, summary = run_precision_on_scored(scored, features_1m)
    print(f"   Registry: {registry.height}, Trades: {trades.height}")
    print("\nSummary:")
    for key, val in summary.items():
        if isinstance(val, float):
            print(f"   {key}: {val:.4f}")
        else:
            print(f"   {key}: {val}")

    fired = trades.filter(pl.col("precision_fire"))
    if fired.height > 0:
        print("\nExit reasons:")
        print(
            fired.group_by("exit_reason")
            .len()
            .sort("len", descending=True)
            .to_dict(as_series=False)
        )


if __name__ == "__main__":
    main()
