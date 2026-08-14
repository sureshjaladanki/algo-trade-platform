"""Tier 3 Precision eval harness CLI — see docs/precision-tier3-eval-verdict.md."""

from __future__ import annotations

import argparse
import sys
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
from src.pipelines.regime_pipeline import predict_intraday_hmm
from src.precision.eval import N_BOOT, evaluate_precision, format_report, k_for
from src.precision.precision import NO_CHASE_RANK_MAX, classify_precision
from src.precision.session import LONG_TOP_K, SHORT_TOP_K
from src.regime.intraday import override_intraday_regime
from src.utils.date import filter_by_period, parse_period_range
from src.utils.mlflow_loader import load_hmm_model, load_horizon_models

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate Tier 3 Precision timing (P0 precondition; P1/P2 gated; "
            "P3 report-only until same-sleeve Horizon H5 CI LB > 0). "
            "Long and Short are scored separately. Phase-1 rules are the default."
        )
    )
    parser.add_argument("--config", type=str, default="config/market_sectoral_symbols.yml")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN")
    parser.add_argument("--train-period", type=str, required=True)
    parser.add_argument("--test-period", type=str, required=True)
    parser.add_argument(
        "--direction",
        type=str,
        default="both",
        choices=["long", "short", "both"],
    )
    parser.add_argument(
        "--regime-run-id",
        type=str,
        default=None,
        help="Optional Regime_Pipeline MLflow run id (default: match train_period / latest)",
    )
    parser.add_argument(
        "--horizon-run-id",
        type=str,
        default=None,
        help="Optional Horizon_Pipeline MLflow run id (default: match train_period / latest)",
    )
    parser.add_argument(
        "--no-chase",
        action="store_true",
        help="Ablation: skip fresh regime-flip fires (ranks ≤ --no-chase-rank-max)",
    )
    parser.add_argument(
        "--no-chase-rank-max",
        type=int,
        default=NO_CHASE_RANK_MAX,
        help=f"Max horizon_rank for --no-chase (default {NO_CHASE_RANK_MAX})",
    )
    parser.add_argument(
        "--skip-rank-1-2",
        action="store_true",
        help="Ablation: hard-skip horizon ranks 1–2",
    )
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = REPO_ROOT / data_dir
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path

    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist.")
        sys.exit(1)
    if not config_path.exists():
        print(f"Error: Config file {config_path} does not exist.")
        sys.exit(1)

    train_start, train_end = parse_period_range(args.train_period)
    test_start, test_end = parse_period_range(args.test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)
    directions = ["long", "short"] if args.direction == "both" else [args.direction]

    print(f"Loading regime data {load_start} -> {load_end}...")
    vix_daily, market_daily, market_15m, nifty100_daily = load_regime_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    daily_regime, intraday_regime = build_regime_features(
        vix_daily, market_daily, market_15m, nifty100_daily
    )

    print("Loading fitted HMM from Regime_Pipeline...")
    hmm_model, resolved_regime_run_id = load_hmm_model(
        train_period=args.train_period,
        run_id=args.regime_run_id,
    )
    print(f"   Regime run id: {resolved_regime_run_id}")

    print("Predicting Tier 1 regimes (post-hysteresis)...")
    regime_preds = override_intraday_regime(
        predict_intraday_hmm(
            daily_regime, intraday_regime, hmm_model, apply_hysteresis=True
        )
    )
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

    print("Loading Horizon universe + building features/labels/TB...")
    stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
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
    test_df = filter_by_period(horizon_df, test_start, test_end, datetime_col="date")
    print(f"   Horizon test rows={test_df.height}")
    if test_df.height == 0:
        print("Error: empty Horizon test after period filter.")
        sys.exit(1)

    print("Loading fitted Horizon models from Horizon_Pipeline...")
    try:
        models, resolved_horizon_run_id = load_horizon_models(
            directions=directions,
            train_period=args.train_period,
            run_id=args.horizon_run_id,
        )
    except FileNotFoundError as exc:
        print(f"Error: No Horizon models loaded. {exc}")
        sys.exit(1)
    print(f"   Horizon run id: {resolved_horizon_run_id}")

    scored_parts = [predict_horizon_gbm(test_df, model) for model in models.values()]
    scored = pl.concat(scored_parts, how="diagonal")
    scored_dirs = [
        d
        for d in directions
        if scored.filter(pl.col("horizon_direction") == d).height > 0
    ]
    if not scored_dirs:
        print("Error: scored frame has no requested directions.")
        sys.exit(1)

    print("Loading 1m + building Precision features...")
    stock_1m, nifty_1m = load_precision_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=test_start,
        end_period=test_end,
    )
    features_1m, registry = build_precision_features(stock_1m, nifty_1m, scored)
    print(f"   Registry episodes={registry.height}  1m rows={features_1m.height}")

    print(
        "Running Precision rules "
        f"(long_k={LONG_TOP_K}, short_k={SHORT_TOP_K}, "
        f"no_chase={args.no_chase}, skip_rank_1_2={args.skip_rank_1_2})..."
    )
    trades = classify_precision(
        registry,
        features_1m,
        no_chase=args.no_chase,
        no_chase_rank_max=args.no_chase_rank_max,
        skip_rank_1_2=args.skip_rank_1_2,
    )
    n_fire = trades.filter(pl.col("precision_fire")).height
    print(f"   Trades={trades.height}  fires={n_fire}")

    print(
        f"\nEvaluating holdout {args.test_period} "
        f"(n_boot={args.n_boot}; K_long={k_for('long')} K_short={k_for('short')})..."
    )
    metrics = evaluate_precision(
        trades,
        features_1m,
        directions=scored_dirs,
        n_boot=args.n_boot,
        seed=args.seed,
        scored=scored,
    )
    title = (
        f"Tier 3 Precision Eval  train={args.train_period}  "
        f"test={args.test_period}  dirs={','.join(scored_dirs)}"
    )
    print()
    print(format_report(metrics, title))


if __name__ == "__main__":
    main()
