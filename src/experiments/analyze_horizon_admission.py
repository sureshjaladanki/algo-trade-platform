"""Admission Step 0 diagnostic — rank-tier / score floors / veto-head (no peek)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.horizon.eval import N_BOOT, annotate_hygiene_flags, format_report, k_for
from src.horizon.eval.admission import (
    DEFAULT_CONVICTION_QUANTILE,
    evaluate_admission_step0,
    fit_veto_last_fold,
    suggest_a2_floors,
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
    test_df = annotate_hygiene_flags(test_df)
    print(f"   Train rows={train_df.height}  Test rows={test_df.height}")
    if train_df.height == 0 or test_df.height == 0:
        print("Error: empty train or test after period filter.")
        sys.exit(1)

    print(
        "Fitting locked Long path-EV (Step 0 diagnostic -- not a peek) "
        f"K_long={k_for('long')}..."
    )
    model, fit_stats = fit_horizon_gbm(train_df, direction="long")
    if model is None:
        print("Error: no long model.")
        sys.exit(1)
    if fit_stats:
        print(
            f"   Trainer diagnostic IC val={fit_stats.get('mean_ic')} "
            f"test_cv={fit_stats.get('mean_test_ic')} (not a gate)"
        )
    scored = predict_horizon_gbm(test_df, model)
    print(f"   Scored long rows: {scored.height}")

    print("Fitting multiclass veto head on last purged val (report-only)...")
    _veto_model, veto_val, veto_stats = fit_veto_last_fold(train_df)
    print(
        f"   Veto val bars={veto_stats.get('val_bars')} "
        f"splits={veto_stats.get('n_splits')} "
        f"reason={veto_stats.get('reason', 'ok')}"
    )

    metrics = evaluate_admission_step0(
        scored,
        directions=["long"],
        n_boot=n_boot,
        seed=seed,
        veto_val_by_direction={"long": veto_val} if veto_val is not None else None,
    )
    title = (
        f"Admission Step 0  fold={fold}  train={train_period}  "
        f"test={test_period}  dirs=long  (REPORT ONLY -- no peek)"
    )
    print()
    report = format_report(metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Admission Step 0: rank-tier refresh, score floors, veto-head val "
            "separation, coverage, and baseline H5 hard-gate reprint on Long A/B. "
            "Not a peek."
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

    print("Admission Step 0 -- REPORT ONLY (no peek); Long only")
    print(
        f"Folds={folds}  n_boot={args.n_boot}  "
        f"default_conviction_q={DEFAULT_CONVICTION_QUANTILE}"
    )

    all_metrics = []
    for fold in folds:
        all_metrics.extend(
            _run_fold(fold, data_dir, config_path, args.n_boot, args.seed)
        )

    print("\n=== Step 0 hard-gate + lock summary (Long) ===")
    h5s = [m for m in all_metrics if m.name == "H5" and m.side == "long"]
    h5_ok = all(bool(m.gate_pass) for m in h5s) if h5s else False
    print(
        f"  H5 dual-fold: {[bool(m.gate_pass) for m in h5s]} "
        f"-> {'HOLD — proceed to lock conviction quantile' if h5_ok else 'BROKEN — STOP at 0/2'}"
    )

    k_flags = [m for m in all_metrics if m.name == "Kimplic" and m.side == "long"]
    k_any = any(bool(m.gate_pass) for m in k_flags)
    k_both = all(bool(m.gate_pass) for m in k_flags) if k_flags else False
    print(
        f"  K-implicated: {[bool(m.gate_pass) for m in k_flags]} "
        f"any={k_any} both={k_both} "
        f"-> {'K may enter peek ladder' if k_both else 'K stays OUT of peek ladder'}"
    )

    floors = {
        tag: [m for m in all_metrics if m.name == f"FLOORp{tag}" and m.side == "long"]
        for tag in (70, 80, 90)
    }
    for tag, ms in floors.items():
        vals = [m.value for m in ms if m.value is not None]
        if vals:
            print(
                f"  Top-K frac below P{tag}: "
                + ", ".join(f"{v:.3f}" for v in vals)
                + " (report-only)"
            )

    print(
        f"  Conviction lock (charter default): P{int(DEFAULT_CONVICTION_QUANTILE * 100)} "
        f"— lock after this table; do not grid on A+B"
    )

    a2s = [m for m in all_metrics if m.name == "A2sug" and m.side == "long"]
    cov_bars = [m for m in all_metrics if m.name == "COVtopk" and m.side == "long"]
    cov_sess = [m for m in all_metrics if m.name == "COVsess" and m.side == "long"]
    if cov_bars and cov_sess and len(cov_bars) == len(cov_sess):
        # Dual-fold lock = min across folds so both clear the same floor.
        suggested = [
            suggest_a2_floors(b.value, s.value)
            for b, s in zip(cov_bars, cov_sess)
            if b.value is not None and s.value is not None
        ]
        if suggested:
            min_bars = min(t[0] for t in suggested)
            min_sess = min(t[1] for t in suggested)
            print(
                f"  A2 pre-register (dual-fold min): "
                f"min_bars={min_bars} min_sessions={min_sess}"
            )
    elif a2s:
        print(f"  A2 suggestions: {[m.note for m in a2s]}")


if __name__ == "__main__":
    main()
