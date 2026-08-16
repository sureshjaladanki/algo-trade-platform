"""Short capacity / regularization Phase 1 + authorized peeks (U1/U2/R1)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.horizon.eval import N_BOOT, evaluate_horizon, format_report
from src.horizon.eval.capacity import (
    MIN_VAL_BARS,
    MIN_VAL_SESS,
    PARAM_SLICES,
    R1_GAP_MIN,
    R1_H5_DELTA_MIN,
    U1_GAP_MAX,
    U1_H5_DELTA_MIN,
    U1_RATIO_MAX,
    U1_REL_MULT,
    U2_H5_DELTA_MIN,
    U2_RATIO_MAX,
    authorize_capacity_levers,
    fit_short_walkforward_slice,
    metric_map,
    peek_h5_clear,
    peek_no_h123_regression,
    reprint_holdout_h5_fail,
    run_phase1_fold_diagnostics,
)
from src.horizon.eval.diagnostics import adv_tercile_topk_diagnostics
from src.horizon.eval.panel import annotate_hygiene_flags, prepare_eval_panel
from src.horizon.horizon_model import SHORT_PARAMS
from src.pipelines.build_horizon_features import (
    build_horizon_features,
    load_horizon_data,
)
from src.pipelines.build_regime_features import (
    build_regime_features,
    load_regime_data,
)
from src.pipelines.horizon_pipeline import predict_horizon_gbm
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


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _load_fold_frames(
    fold: str, data_dir: Path, config_path: Path
) -> tuple[pl.DataFrame, pl.DataFrame, str, str]:
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
    test_df = filter_by_period(
        horizon_df, test_start, test_end, datetime_col="date"
    )
    test_df = annotate_hygiene_flags(test_df)
    print(f"   Train rows={train_df.height}  Test rows={test_df.height}")
    if train_df.height == 0 or test_df.height == 0:
        print("Error: empty train or test after period filter.")
        sys.exit(1)
    return train_df, test_df, train_period, test_period


def _run_phase1_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    n_boot: int,
    seed: int,
) -> dict:
    train_df, test_df, train_period, test_period = _load_fold_frames(
        fold, data_dir, config_path
    )
    print("Phase 1 capacity diagnosis (last-fold train/val; 0 peeks)...")
    _fold_train, _fold_val, diag = run_phase1_fold_diagnostics(train_df)
    print(
        f"   mass n_S={diag['n_train_short']} n_L={diag['n_train_long']} "
        f"ratio={_fmt(diag['ratio'], 3)}  "
        f"rel400={_fmt(diag['rel400'], 5)} rel300_L={_fmt(diag['rel300_l'], 5)} "
        f"rel_vs_L={_fmt(diag['rel_vs_long'], 2)}"
    )
    print(
        f"   val bars/sess={diag['val_bars']}/{diag['val_sess']} "
        f"min-N>={MIN_VAL_BARS}/{MIN_VAL_SESS} clear={diag['val_min_n_clear']}  "
        f"gap(train-val IC)={_fmt(diag['gap'], 4)}"
    )
    print(
        f"   H5v0={_fmt(diag['h5v0'], 4)} H2v0={_fmt(diag['h2v0'], 4)}  "
        f"dU1={_fmt(diag['delta_U1'], 4)} "
        f"ci=[{_fmt(diag['delta_U1_lo'], 4)}, {_fmt(diag['delta_U1_hi'], 4)}]  "
        f"dU2={_fmt(diag['delta_U2'], 4)} "
        f"ci=[{_fmt(diag['delta_U2_lo'], 4)}, {_fmt(diag['delta_U2_hi'], 4)}]  "
        f"dR1={_fmt(diag['delta_R1'], 4)} "
        f"ci=[{_fmt(diag['delta_R1_lo'], 4)}, {_fmt(diag['delta_R1_hi'], 4)}]"
    )
    for name in ("U1", "U2", "R1"):
        print(
            f"   {name}: H5={_fmt(diag[f'h5v_{name}'], 4)} "
            f"H2={_fmt(diag[f'h2v_{name}'], 4)} "
            f"gap={_fmt(diag[f'gap_{name}'], 4)} "
            f"seed7_d={_fmt(diag.get(f'seed7_delta_{name}'), 4)}"
        )
    leaf = diag.get("leaf") or {}
    if leaf.get("skipped"):
        print(f"   leaf occupancy: skipped ({leaf.get('note')})")
    else:
        print(
            f"   leaf occupancy: n_used={leaf.get('n_leaves_used')} "
            f"mean={_fmt(leaf.get('mean_samples'), 1)} "
            f"p10={_fmt(leaf.get('p10_samples'), 1)}"
        )

    # Holdout reprint under baseline last-fold model (frozen; not authorize).
    base_model = diag["_models"]["base"]
    print("Scoring holdout path-EV baseline (frozen reprint; not a peek)...")
    holdout_scored = predict_horizon_gbm(test_df, base_model)
    holdout_metrics = evaluate_horizon(
        holdout_scored, directions=["short"], n_boot=n_boot, seed=seed
    )
    title = (
        f"Capacity Phase 1 holdout reprint  fold={fold}  "
        f"train={train_period}  test={test_period}  (FROZEN -- not authorize)"
    )
    report = format_report(holdout_metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    holdout_panel = prepare_eval_panel(holdout_scored, "short")
    advt = adv_tercile_topk_diagnostics(holdout_panel, "short")
    if advt:
        print(f"   Holdout ADVt lo={_fmt(advt[0].value)}  {advt[0].note}")

    # Drop heavy objects before cross-fold authorize.
    clean = {k: v for k, v in diag.items() if not k.startswith("_")}
    clean["holdout_h5_fail"] = reprint_holdout_h5_fail(holdout_metrics)
    clean["holdout_metrics"] = holdout_metrics
    return clean


def _print_decision(fold_rows: dict[str, dict], decision: dict) -> None:
    print("\n=== Phase 1 numeric gate (Short capacity; MUST_FIX robustness on) ===")
    print(
        f"  cuts: U1 ratio<={U1_RATIO_MAX} & "
        f"rel400>={U1_REL_MULT}*rel300_L & gap<={U1_GAP_MAX} & "
        f"dH5>=+{U1_H5_DELTA_MIN} & H2>0 + robust | "
        f"U2 ratio<={U2_RATIO_MAX} & dH5>=+{U2_H5_DELTA_MIN} & H2>0 + robust | "
        f"R1 gap>={R1_GAP_MIN} OR (dH5>=+{R1_H5_DELTA_MIN} & H2>0 + robust) | "
        f"val min-N>={MIN_VAL_BARS}/{MIN_VAL_SESS}"
    )
    for fold, row in fold_rows.items():
        print(f"  Fold {fold}:")
        print(
            f"    ratio={_fmt(row['ratio'], 3)}  rel_vs_L={_fmt(row['rel_vs_long'], 2)}  "
            f"gap={_fmt(row['gap'], 4)}  val_min_n={row['val_min_n_clear']}  "
            f"holdout H5 FAIL reprint={row['holdout_h5_fail']}"
        )
        print(
            f"    H5v0={_fmt(row['h5v0'], 4)}  "
            f"dU1={_fmt(row['delta_U1'], 4)} lo={_fmt(row['delta_U1_lo'], 4)}  "
            f"dU2={_fmt(row['delta_U2'], 4)} lo={_fmt(row['delta_U2_lo'], 4)}  "
            f"dR1={_fmt(row['delta_R1'], 4)} lo={_fmt(row['delta_R1_lo'], 4)}"
        )

    print(
        f"  U1={decision['u1']} (mass={decision['u1_mass']} "
        f"point={decision['u1_point']} robust={decision['u1_robust']})  "
        f"U2={decision['u2']} (alt={decision['u2_alt']} robust={decision['u2_robust']} "
        f"u1_fail_only_delta={decision['u1_fail_only_delta']})  "
        f"R1={decision['r1']} (gap_lane={decision['r1_gap_lane']} "
        f"delta_lane={decision['r1_delta_lane']} robust={decision['r1_robust']})  "
        f"val_n={decision['val_n_ok']}"
    )
    if decision["hard_stop"]:
        print("  HARD-STOP FIRED -> STOP @ 0/2")
        print("  authorized=[]")
        print("  next = Long-only cascade economics; Short sleeve disabled")
        return
    print(
        f"  AUTHORIZED ladder={decision['authorized']} "
        f"(tie-break U1->U2->R1; spend <=2)"
    )
    print(
        f"  Peek 1 = {decision['peek1']}"
        + (f"  Peek 2 contingent = {decision['peek2']}" if decision["peek2"] else "")
    )


def _run_peek_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    slice_id: str,
    n_boot: int,
    seed: int,
) -> tuple[list, list]:
    train_df, test_df, train_period, test_period = _load_fold_frames(
        fold, data_dir, config_path
    )
    overrides = PARAM_SLICES[slice_id]
    print("Fitting baseline SHORT_PARAMS (companion regression baseline)...")
    base_model, base_stats = fit_short_walkforward_slice(train_df, overrides=None, seed=seed)
    if base_model is None:
        print("Error: baseline walk-forward fit failed.")
        sys.exit(1)
    print(
        f"   baseline n_splits={base_stats.get('n_splits')} "
        f"mean val IC={_fmt(base_stats.get('mean_ic'), 4)}"
    )
    base_scored = predict_horizon_gbm(test_df, base_model)
    base_metrics = evaluate_horizon(
        base_scored, directions=["short"], n_boot=n_boot, seed=seed
    )

    print(f"Fitting peek slice {slice_id} overrides={overrides}...")
    peek_model, peek_stats = fit_short_walkforward_slice(
        train_df, overrides=overrides, seed=seed
    )
    if peek_model is None:
        print(f"Error: {slice_id} walk-forward fit failed.")
        sys.exit(1)
    print(
        f"   peek n_splits={peek_stats.get('n_splits')} "
        f"mean val IC={_fmt(peek_stats.get('mean_ic'), 4)}"
    )
    peek_scored = predict_horizon_gbm(test_df, peek_model)
    peek_metrics = evaluate_horizon(
        peek_scored, directions=["short"], n_boot=n_boot, seed=seed
    )
    title = (
        f"Capacity Peek {slice_id}  fold={fold}  train={train_period}  "
        f"test={test_period}  short-only  overrides={overrides}"
    )
    report = format_report(peek_metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    return peek_metrics, base_metrics


def _print_peek_verdict(
    slice_id: str, peek_metrics: dict[str, list], base_metrics: dict[str, list]
) -> bool:
    print(
        f"\n=== Peek {slice_id} vs baseline Short "
        f"(H5 primary; no H1/H2/H3 regression) ==="
    )
    h5_both = True
    h123_both = True
    for fold, peek in peek_metrics.items():
        base = base_metrics[fold]
        mm = metric_map(peek)
        h5 = mm.get("H5")
        h5_ok = peek_h5_clear(peek)
        h123_ok, note = peek_no_h123_regression(peek, base)
        h5_both = h5_both and h5_ok
        h123_both = h123_both and h123_ok
        h5_val = _fmt(h5.value, 4) if h5 else "nan"
        h5_lo = _fmt(h5.ci_low, 4) if h5 else "nan"
        h5_hi = _fmt(h5.ci_high, 4) if h5 else "nan"
        print(
            f"  Fold {fold}: H5={h5_val} ci=[{h5_lo}, {h5_hi}] "
            f"{'PASS' if h5_ok else 'FAIL'}  H1/H2/H3={note}"
        )
    if h5_both and h123_both:
        print(f"  VERDICT: Short H5 dual-fold CLEAR on {slice_id} -- STOP (PASS path)")
        return True
    print(f"  VERDICT: Peek {slice_id} FAIL H5 and/or H1-H3 regression")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Short capacity Phase 1 diagnosis, or Phase-1-authorized peek "
            "(U1/U2/R1). One param slice; Short-only."
        )
    )
    parser.add_argument("--config", type=str, default="config/market_sectoral_symbols.yml")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN")
    parser.add_argument("--folds", type=str, default="A,B")
    parser.add_argument(
        "--peek",
        type=str,
        default=None,
        choices=["U1", "U2", "R1"],
        help="Authorized peek only (Phase 1 must have authorized the slice).",
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

    if args.peek:
        slice_id = args.peek
        print(
            f"Capacity Peek -- {slice_id} overrides={PARAM_SLICES[slice_id]} "
            f"(baseline SHORT_PARAMS={ {k: SHORT_PARAMS[k] for k in ('min_child_samples', 'reg_lambda', 'max_depth')} })"
        )
        print(f"Folds={folds}  n_boot={args.n_boot}")
        peek_metrics: dict[str, list] = {}
        base_metrics: dict[str, list] = {}
        for fold in folds:
            peek_metrics[fold], base_metrics[fold] = _run_peek_fold(
                fold, data_dir, config_path, slice_id, args.n_boot, args.seed
            )
        _print_peek_verdict(slice_id, peek_metrics, base_metrics)
        return

    print("Capacity Phase 1 -- REPORT ONLY (0 peeks)")
    print(f"Folds={folds}  n_boot={args.n_boot}")
    print(f"Baseline SHORT_PARAMS min_child_samples={SHORT_PARAMS['min_child_samples']} "
          f"max_depth={SHORT_PARAMS['max_depth']} reg_lambda={SHORT_PARAMS['reg_lambda']}")

    fold_rows: dict[str, dict] = {}
    for fold in folds:
        fold_rows[fold] = _run_phase1_fold(
            fold, data_dir, config_path, args.n_boot, args.seed
        )

    decision = authorize_capacity_levers(fold_rows)
    _print_decision(fold_rows, decision)


if __name__ == "__main__":
    main()
