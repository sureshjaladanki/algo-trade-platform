"""Tier 2 Horizon eval harness CLI — see docs/horizon-tier2-eval-verdict.md."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.eval import N_BOOT, evaluate_horizon, format_report, k_for
from src.horizon.eval.common import annotate_hygiene_flags
from src.pipelines.build_horizon_features import (
    build_horizon_features,
    load_horizon_data,
)
from src.pipelines.build_regime_features import (
    build_regime_features,
    load_regime_data,
)
from src.pipelines.horizon_pipeline import fit_horizon_gbm, predict_horizon_gbm
from src.pipelines.regime_pipeline import predict_intraday_hmm
from src.regime.intraday import override_intraday_regime
from src.utils.date import filter_by_period, parse_period_range
from src.utils.mlflow_loader import load_hmm_model

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate Tier 2 Horizon ranking (H1/H2/H3/H5 gated; H10 precondition) "
            "on a holdout fold. Long and Short are scored separately."
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
    hmm_model, resolved_run_id = load_hmm_model(
        train_period=args.train_period,
        run_id=args.regime_run_id,
    )
    print(f"   Regime run id: {resolved_run_id}")

    print("Predicting Tier 1 regimes (post-hysteresis)...")
    regime_preds = override_intraday_regime(
        predict_intraday_hmm(
            daily_regime, intraday_regime, hmm_model, apply_hysteresis=True
        )
    )
    regime_df = regime_preds.select(["date", "daily_regime", "intraday_regime"])

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

    train_df = filter_by_period(
        horizon_df, train_start, train_end, datetime_col="date"
    )
    test_df = filter_by_period(horizon_df, test_start, test_end, datetime_col="date")
    # Full-panel hygiene so H7 fwd-circuit windows see non-sleeve bars too.
    test_df = annotate_hygiene_flags(test_df)
    print(f"   Train rows={train_df.height}  Test rows={test_df.height}")
    if train_df.height == 0 or test_df.height == 0:
        print("Error: empty train or test after period filter.")
        sys.exit(1)

    print(
        "Fitting Horizon models on train "
        f"(K_long={k_for('long')} K_short={k_for('short')}; "
        "gates use holdout only — trainer CV IC is not a ship gate)..."
    )
    scored_parts: list[pl.DataFrame] = []
    for direction in directions:
        print(f"\n   Fitting {direction}...")
        model, fit_stats = fit_horizon_gbm(train_df, direction=direction)
        if model is None:
            print(f"   Warning: no {direction} model — skipping sleeve.")
            continue
        if fit_stats:
            print(
                f"   Trainer diagnostic IC val={fit_stats.get('mean_ic')} "
                f"test_cv={fit_stats.get('mean_test_ic')} "
                f"(not a gate)"
            )
        scored = predict_horizon_gbm(test_df, model)
        print(f"   Scored {direction} rows: {scored.height}")
        scored_parts.append(scored)

    if not scored_parts:
        print("Error: no sleeves scored.")
        sys.exit(1)

    scored = pl.concat(scored_parts, how="diagonal")
    scored_dirs = [
        d
        for d in directions
        if scored.filter(pl.col("horizon_direction") == d).height > 0
    ]
    if not scored_dirs:
        print("Error: scored frame has no requested directions.")
        sys.exit(1)

    print(f"\nEvaluating holdout {args.test_period} (n_boot={args.n_boot})...")
    metrics = evaluate_horizon(
        scored,
        directions=scored_dirs,
        n_boot=args.n_boot,
        seed=args.seed,
    )

    title = (
        f"Tier 2 Horizon Eval  train={args.train_period}  "
        f"test={args.test_period}  dirs={','.join(scored_dirs)}"
    )
    print()
    print(format_report(metrics, title))


if __name__ == "__main__":
    main()
