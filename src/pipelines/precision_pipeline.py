"""Tier 3 Precision pipeline: Horizon registry → 1m features → rules fills / exits."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import mlflow
import polars as pl

from src.labels.triple_barrier import ROUND_TRIP_COST
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
from src.pipelines.regime_pipeline import predict_intraday_hmm
from src.precision.precision import classify_precision
from src.precision.scores import check_rank_edge_polarity
from src.precision.session import LONG_TOP_K, SHORT_TOP_K
from src.regime.intraday import override_intraday_regime
from src.utils.date import filter_by_period, parse_period_range
from src.utils.mlflow_loader import load_hmm_model, load_horizon_models

PRECISION_EXPERIMENT = "Precision_Pipeline"


def run_pipeline(
    data_dir: Path,
    config_path: Path,
    train_period: str,
    test_period: str,
    direction: str = "both",
    regime_run_id: str | None = None,
    horizon_run_id: str | None = None,
):
    mlflow.set_experiment(PRECISION_EXPERIMENT)
    with mlflow.start_run(run_name=f"Precision_{train_period}_{test_period}"):
        mlflow.log_param("train_period", train_period)
        mlflow.log_param("test_period", test_period)
        mlflow.log_param("data_dir", str(data_dir))
        mlflow.log_param("config_path", str(config_path))
        mlflow.log_param("direction", direction)
        mlflow.log_param("long_top_k", LONG_TOP_K)
        mlflow.log_param("short_top_k", SHORT_TOP_K)

        train_start, train_end = parse_period_range(train_period)
        test_start, test_end = parse_period_range(test_period)
        # Include train window so rolling Regime / Horizon features (and HMM
        # hysteresis) have history before test. Tier 3 does not train — only
        # the test window is scored / traded after warm-up.
        load_start = min(train_start, test_start)
        load_end = max(train_end, test_end)

        print(f"1. Loading regime data from {load_start} to {load_end}...")
        vix_daily, market_daily, market_15m, nifty100_daily_dfs = load_regime_data(
            data_dir=data_dir,
            config_path=config_path,
            start_period=load_start,
            end_period=load_end,
        )
        print("   Building regime features...")
        daily_regime, intraday_regime = build_regime_features(
            vix_daily, market_daily, market_15m, nifty100_daily_dfs
        )

        print("2. Pulling fitted HMM from Regime_Pipeline experiment...")
        hmm_model, resolved_regime_run_id = load_hmm_model(
            train_period=train_period,
            run_id=regime_run_id,
        )
        mlflow.log_param("regime_run_id", resolved_regime_run_id)

        print("3. Predicting Tier 1 regimes (daily cascade + HMM)...")
        regime_preds = predict_intraday_hmm(
            daily_regime,
            intraday_regime,
            hmm_model,
            apply_hysteresis=True,
        )
        regime_preds = override_intraday_regime(regime_preds)

        print(f"4. Filtering Regime test window ({test_period})...")
        daily_regime = filter_by_period(
            daily_regime, test_start, test_end, datetime_col="date"
        )
        intraday_regime = filter_by_period(
            intraday_regime, test_start, test_end, datetime_col="date"
        )
        regime_df = filter_by_period(
            regime_preds.select(["date", "daily_regime", "intraday_regime"]),
            test_start,
            test_end,
            datetime_col="date",
        )
        print(f"   Regime test bars: {regime_df.height}")
        mlflow.log_metric("regime_test_rows", regime_df.height)

        print("5. Loading Horizon universe (15m stocks + sectors + Nifty)...")
        stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty = load_horizon_data(
            data_dir=data_dir,
            config_path=config_path,
            start_period=load_start,
            end_period=load_end,
        )

        print("6. Building Horizon features / labels / TB geometry...")
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

        print(f"7. Filtering Horizon test window ({test_period})...")
        test_df = filter_by_period(
            horizon_df, test_start, test_end, datetime_col="date"
        )
        print(f"   Test shape: {test_df.shape}")
        mlflow.log_metric("horizon_test_rows", test_df.height)

        if test_df.height == 0:
            print("Error: Test Horizon dataframe is empty. Check your periods.")
            sys.exit(1)

        print("8. Loading fitted Horizon models from Horizon_Pipeline experiment...")
        # TODO: support per-sleeve Horizon run ids (--horizon-long-run-id /
        # --horizon-short-run-id) so long and short trained in separate
        # Horizon_Pipeline runs can be selected independently; fall back to
        # auto-resolve latest matching train_period (+ direction param) per sleeve.
        directions = ["long", "short"] if direction == "both" else [direction]
        try:
            models, resolved_horizon_run_id = load_horizon_models(
                directions=directions,
                train_period=train_period,
                run_id=horizon_run_id,
            )
        except FileNotFoundError as exc:
            print(f"Error: No Horizon models loaded/scored. {exc}")
            sys.exit(1)

        mlflow.log_param("horizon_run_id", resolved_horizon_run_id)

        scored_dfs: list[pl.DataFrame] = []
        for sleeve, model in models.items():
            scored = predict_horizon_gbm(test_df, model)
            print(f"   Scored {sleeve} rows: {scored.height}")
            scored_dfs.append(scored)

        scored = pl.concat(scored_dfs, how="diagonal")

        print("9. Loading 1m data for Precision trade symbols...")
        # 1m only needed on the test window (entry timing / exits).
        # Symbols come from config sectoral_indices[*].trade_symbols.
        stock_1m, nifty_1m = load_precision_data(
            data_dir=data_dir,
            config_path=config_path,
            start_period=test_start,
            end_period=test_end,
        )

        print("10. Building Precision 1m features...")
        features_1m, registry = build_precision_features(
            stock_1m,
            nifty_1m,
            scored,
        )
        print(f"   1m feature rows: {features_1m.height}")
        mlflow.log_metric("precision_1m_rows", features_1m.height)

        polarity = check_rank_edge_polarity(registry)
        mlflow.log_metric("rank_polarity_ok", float(polarity["rank_polarity_ok"]))
        mlflow.log_metric(
            "rank_polarity_violations", float(polarity["rank_polarity_violations"])
        )
        if not polarity["rank_polarity_ok"]:
            print(
                "   WARNING: registry rank/edge polarity violations — "
                "check Horizon sleeve rank_descending vs edge_score."
            )

        print(
            "11. Running Precision rules "
            f"(long_k={LONG_TOP_K}, short_k={SHORT_TOP_K})..."
        )
        trades = classify_precision(registry, features_1m)
        _log_run_stats(trades)
        _print_run_stats(registry.height, trades)

        print("\nRun `mlflow ui` in your terminal to view the experiment tracking.")
        print(
            "Gated P0–P3 eval: python -m src.experiments.eval_precision "
            f"--train-period {train_period} --test-period {test_period}"
        )
        return trades


def _print_run_stats(n_registry: int, trades: pl.DataFrame) -> None:
    fired = trades.filter(pl.col("precision_fire"))
    print(f"   Registry episodes: {n_registry}")
    print(f"   Trades frame: {trades.height}")
    print(f"   Fires: {fired.height}")
    if fired.height == 0:
        return
    print("\nFires by direction / exit:")
    print(
        fired.group_by(["horizon_direction", "exit_reason"])
        .len()
        .sort(["horizon_direction", "len"], descending=[False, True])
    )


def _log_run_stats(trades: pl.DataFrame) -> None:
    fired = trades.filter(pl.col("precision_fire"))
    n, n_fire = trades.height, fired.height
    mlflow.log_metric("episodes", n)
    mlflow.log_metric("fires", n_fire)
    mlflow.log_metric("fire_rate", n_fire / n if n else 0.0)
    if n_fire == 0:
        return
    mean_gross = float(fired["gross_ret"].mean())
    mlflow.log_metric("mean_gross_ret", mean_gross)
    mlflow.log_metric("mean_net_ret", mean_gross - ROUND_TRIP_COST)
    for direction in ("long", "short"):
        sleeve = fired.filter(pl.col("horizon_direction") == direction)
        mlflow.log_metric(f"{direction}_fires", sleeve.height)


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
    # TODO: add --horizon-long-run-id / --horizon-short-run-id for split sleeve runs.
    parser.add_argument(
        "--horizon-run-id",
        type=str,
        default=None,
        help="Optional Horizon_Pipeline MLflow run id (default: match train_period / latest)",
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
        horizon_run_id=args.horizon_run_id,
    )
