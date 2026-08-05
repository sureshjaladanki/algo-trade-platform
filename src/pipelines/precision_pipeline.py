"""Tier 3 Precision pipeline: Horizon registry → 1m features → rules fills / exits."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import mlflow
import numpy as np
import polars as pl

from src.pipelines.build_horizon_features import (
    build_horizon_features,
    load_horizon_data,
)
from src.pipelines.build_precision_features import (
    build_precision_features,
    load_precision_data,
)
from src.pipelines.build_regime_features import build_regime_features
from src.pipelines.horizon_pipeline import fit_horizon_gbm, predict_horizon_gbm
from src.pipelines.regime_pipeline import predict_intraday_hmm
from src.precision.rules import (
    build_decision_registry,
    run_precision_rules,
    summarize_precision_trades,
)
from src.regime.intraday import override_intraday_regime
from src.utils.date import filter_by_period, parse_period_range
from src.utils.mlflow_loader import load_hmm_model

PRECISION_EXPERIMENT = "Precision_Pipeline"


def run_precision_on_scored(
    horizon_scored: pl.DataFrame,
    stock_1m_features: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """
    Apply Precision rules to a Horizon-scored frame + 1m features.

    Returns (registry, trades, summary).
    """
    registry = build_decision_registry(horizon_scored)
    trades = run_precision_rules(registry, stock_1m_features)
    summary = summarize_precision_trades(trades)
    return registry, trades, summary


def run_pipeline(
    data_dir: Path,
    config_path: Path,
    train_period: str,
    test_period: str,
    direction: str = "both",
    regime_run_id: str | None = None,
):
    mlflow.set_experiment(PRECISION_EXPERIMENT)
    with mlflow.start_run(run_name=f"Precision_{train_period}_{test_period}"):
        mlflow.log_param("train_period", train_period)
        mlflow.log_param("test_period", test_period)
        mlflow.log_param("data_dir", str(data_dir))
        mlflow.log_param("config_path", str(config_path))
        mlflow.log_param("direction", direction)

        train_start, train_end = parse_period_range(train_period)
        test_start, test_end = parse_period_range(test_period)
        load_start = min(train_start, test_start)
        load_end = max(train_end, test_end)

        print(f"1. Building regime features from {load_start} to {load_end}...")
        daily_regime, intraday_regime = build_regime_features(
            data_dir=data_dir,
            config_path=config_path,
            start_period=load_start,
            end_period=load_end,
        )

        print("2. Pulling fitted HMM from Regime_Pipeline experiment...")
        hmm_model, resolved_run_id = load_hmm_model(
            train_period=train_period,
            run_id=regime_run_id,
        )
        mlflow.log_param("regime_run_id", resolved_run_id)

        print("3. Predicting Tier 1 regimes (daily cascade + HMM)...")
        regime_preds = predict_intraday_hmm(
            daily_regime,
            intraday_regime,
            hmm_model,
            apply_hysteresis=True,
        )
        regime_preds = override_intraday_regime(regime_preds)
        regime_df = regime_preds.select(
            ["date", "daily_regime", "intraday_regime"]
        )

        print("4. Loading Horizon universe (15m stocks + sectors + Nifty)...")
        stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty = load_horizon_data(
            data_dir=data_dir,
            config_path=config_path,
            start_period=load_start,
            end_period=load_end,
        )

        print("5. Building Horizon features / labels / TB geometry...")
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

        print(f"6. Splitting Horizon into train ({train_period}) / test ({test_period})...")
        train_df = filter_by_period(
            horizon_df, train_start, train_end, datetime_col="date"
        )
        test_df = filter_by_period(
            horizon_df, test_start, test_end, datetime_col="date"
        )
        print(f"   Train shape: {train_df.shape}, Test shape: {test_df.shape}")
        mlflow.log_metric("horizon_train_rows", train_df.height)
        mlflow.log_metric("horizon_test_rows", test_df.height)

        if train_df.height == 0 or test_df.height == 0:
            print("Error: Train or test Horizon dataframe is empty. Check your periods.")
            sys.exit(1)

        print("7. Fitting Horizon models (cascade-valid sleeves) for Precision registry...")
        directions = ["long", "short"] if direction == "both" else [direction]
        scored_dfs: list[pl.DataFrame] = []

        for sleeve in directions:
            print(f"\n   Fitting Horizon {sleeve.capitalize()} model...")
            model, fit_stats = fit_horizon_gbm(train_df, direction=sleeve)
            if model is None:
                print(f"   Warning: No Horizon {sleeve.capitalize()} model trained.")
                continue
            if fit_stats:
                mlflow.log_metric(
                    f"horizon_{sleeve}_mean_ic", float(fit_stats.get("mean_ic", 0.0))
                )
            scored = predict_horizon_gbm(test_df, model)
            print(f"   Scored {sleeve} rows: {scored.height}")
            scored_dfs.append(scored)

        if not scored_dfs:
            print("Error: No Horizon models trained/scored. Cannot build Precision registry.")
            sys.exit(1)

        scored = pl.concat(scored_dfs, how="diagonal")

        print("8. Loading 1m data for Precision registry symbols...")
        registry_symbols = (
            scored.select("symbol").unique().to_series().to_list()
        )
        # 1m only needed on the test window (entry timing / exits).
        stock_1m, nifty_1m = load_precision_data(
            data_dir=data_dir,
            config_path=config_path,
            start_period=test_start,
            end_period=test_end,
            symbols=registry_symbols,
        )

        print("9. Building Precision 1m features...")
        features_1m = build_precision_features(stock_1m, nifty_1m)
        print(f"   1m feature rows: {features_1m.height}")
        mlflow.log_metric("precision_1m_rows", features_1m.height)

        print("10. Running Precision rules (bounded-wait entry + frozen TB exits)...")
        registry, trades, summary = run_precision_on_scored(scored, features_1m)
        print(f"   Registry episodes: {registry.height}")
        print(f"   Trades frame: {trades.height}")
        _print_summary(summary)
        _log_summary_mlflow(summary)

        print("\nExit reason counts (fired only):")
        fired = trades.filter(pl.col("precision_fire"))
        if fired.height > 0:
            counts = (
                fired.group_by("exit_reason").len().sort("len", descending=True)
            )
            print(counts.to_dict(as_series=False))

        print("\nRun `mlflow ui` in your terminal to view the experiment tracking.")
        return trades


def _print_summary(summary: dict[str, Any]) -> None:
    print("\nPrecision summary:")
    for key, val in summary.items():
        if isinstance(val, float):
            print(f"   {key}: {val:.4f}")
        else:
            print(f"   {key}: {val}")


def _log_summary_mlflow(summary: dict[str, Any]) -> None:
    for key, val in summary.items():
        if isinstance(val, (int, float)) and np.isfinite(val):
            mlflow.log_metric(key, float(val))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the Algo Trading Precision Pipeline workflow"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/GOLDEN",
        help="Path to the GOLDEN data directory",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/market_sectoral_symbols.yml",
        help="Path to the symbols config",
    )
    parser.add_argument(
        "--train-period",
        type=str,
        required=True,
        help="Training period for Horizon: yyyy-yyyy or mm/yyyy-mm/yyyy",
    )
    parser.add_argument(
        "--test-period",
        type=str,
        required=True,
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
        help="Optional Regime_Pipeline MLflow run id (default: match train_period / latest)",
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    config_path = Path(args.config)

    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist.")
        sys.exit(1)

    if not config_path.exists():
        print(f"Error: Config file {config_path} does not exist.")
        sys.exit(1)

    run_pipeline(
        data_dir=data_dir,
        config_path=config_path,
        train_period=args.train_period,
        test_period=args.test_period,
        direction=args.direction,
        regime_run_id=args.regime_run_id,
    )
