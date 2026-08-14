"""Short travel / ranking Step 0 diagnostic — Top−Rest + gated C1/C2 (no peek)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.eval import N_BOOT, annotate_hygiene_flags, format_report, k_for
from src.horizon.eval.short_travel import (
    attach_short_s1b_candidates,
    evaluate_short_travel,
    summarize_hard_gate,
)
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

FOLDS = {
    "A": {
        "train_period": "2015-2017",
        "test_period": "2018-2018",
        "regime_run_id": "e9dbc99428d748f0a78e12281531f27f",
    },
    "B": {
        "train_period": "2016-2018",
        "test_period": "2019-2019",
        "regime_run_id": "7fff95a9410144efb4ac69c10608ee53",
    },
}


def _run_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    directions: list[str],
    n_boot: int,
    seed: int,
) -> list:
    cfg = FOLDS[fold]
    train_period = cfg["train_period"]
    test_period = cfg["test_period"]
    train_start, train_end = parse_period_range(train_period)
    test_start, test_end = parse_period_range(test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    print(f"\n=== Fold {fold}  train={train_period}  test={test_period} ===")
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

    hmm_model, resolved_run_id = load_hmm_model(
        train_period=train_period,
        run_id=cfg["regime_run_id"],
    )
    print(f"   Regime run id: {resolved_run_id}")
    regime_preds = override_intraday_regime(
        predict_intraday_hmm(
            daily_regime, intraday_regime, hmm_model, apply_hysteresis=True
        )
    )
    regime_df = regime_preds.select(["date", "daily_regime", "intraday_regime"])

    print("Loading Horizon universe + building features/labels/TB+Short-travel...")
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
    # Pre-registered C1/C2 for gated ρ + non-duplication (not in SHORT_FEATURES).
    horizon_df = attach_short_s1b_candidates(horizon_df)

    train_df = filter_by_period(
        horizon_df, train_start, train_end, datetime_col="date"
    )
    test_df = filter_by_period(horizon_df, test_start, test_end, datetime_col="date")
    test_df = annotate_hygiene_flags(test_df)
    print(f"   Train rows={train_df.height}  Test rows={test_df.height}")
    if train_df.height == 0 or test_df.height == 0:
        print("Error: empty train or test after period filter.")
        sys.exit(1)

    print(
        "Fitting locked Horizon path-EV (Step 0 diagnostic -- not a peek) "
        f"K_long={k_for('long')} K_short={k_for('short')}..."
    )
    scored_parts: list[pl.DataFrame] = []
    for direction in directions:
        print(f"   Fitting {direction}...")
        model, fit_stats = fit_horizon_gbm(train_df, direction=direction)
        if model is None:
            print(f"   Warning: no {direction} model — skipping sleeve.")
            continue
        if fit_stats:
            print(
                f"   Trainer diagnostic IC val={fit_stats.get('mean_ic')} "
                f"test_cv={fit_stats.get('mean_test_ic')} (not a gate)"
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
    metrics = evaluate_short_travel(
        scored,
        train_df,
        directions=scored_dirs,
        n_boot=n_boot,
        seed=seed,
    )
    title = (
        f"Short-travel Step 0  fold={fold}  train={train_period}  "
        f"test={test_period}  dirs={','.join(scored_dirs)}  (REPORT ONLY -- no peek)"
    )
    print()
    report = format_report(metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    return metrics


def _print_decision(decision: dict) -> None:
    print("\n=== Step 0 hard-stop / implication (Short primary) ===")
    print(f"  folds={decision['folds']}")
    print(f"  SEP fail all={decision['sep_fail_all']}")
    print(f"  ANTI both={decision['anti_both']} gaps={decision['anti_gaps']}")
    print(
        f"  C1 clear={decision['c1_clear']} rho={decision['rho_c1']} | "
        f"C2 clear={decision['c2_clear']} rho={decision['rho_c2']}"
    )
    print(f"  S-K both={decision['sk_both']} gates={decision['sk_gates']}")
    print(f"  GEOM both={decision['geom_both']}")

    if decision["hard_stop"]:
        print("  HARD-STOP FIRED -> STOP @ 0/2")
        for reason in decision["hard_reasons"]:
            print(f"    - {reason}")
        print("  authorized=[]")
        return

    auth = decision["authorized"]
    if not auth:
        print("  hard-stop clear but no authorized lever pattern -> review")
        return

    # Spend order S1a → S1b → S-K; peek budget ≤2.
    peek1 = auth[0]
    peek2 = auth[1] if len(auth) > 1 else None
    print(f"  AUTHORIZED ladder={auth} (tie-break S1a→S1b→S-K; spend ≤2)")
    print(f"  Peek 1 = {peek1}" + (f"  Peek 2 contingent = {peek2}" if peek2 else ""))


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Short travel Step 0: Top-K vs Rest MFE / anti-selection / gated C1-C2 "
            "ρ on Fold A/B. Not a peek — hard-stop / lever authorization input."
        )
    )
    parser.add_argument("--config", type=str, default="config/market_sectoral_symbols.yml")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN")
    parser.add_argument(
        "--folds",
        type=str,
        default="A,B",
        help="Comma-separated folds (default A,B)",
    )
    parser.add_argument(
        "--direction",
        type=str,
        default="both",
        choices=["long", "short", "both"],
        help="Short primary; Long = companion path-density publish-only",
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

    folds = [f.strip().upper() for f in args.folds.split(",") if f.strip()]
    for fold in folds:
        if fold not in FOLDS:
            print(f"Error: unknown fold {fold}; expected one of {list(FOLDS)}")
            sys.exit(1)

    directions = ["long", "short"] if args.direction == "both" else [args.direction]
    print("Short-travel Step 0 -- REPORT ONLY (no peek)")
    print(f"Folds={folds}  directions={directions}  n_boot={args.n_boot}")

    fold_metrics: dict[str, list] = {}
    for fold in folds:
        fold_metrics[fold] = _run_fold(
            fold,
            data_dir,
            config_path,
            directions,
            args.n_boot,
            args.seed,
        )

    decision = summarize_hard_gate(fold_metrics)
    _print_decision(decision)


if __name__ == "__main__":
    main()
