"""AUDIT-ONLY (fresh M0 quarantine). See docs/archive/horizon-fresh-quarantine-index.md. Path-quality veto Step 0 — reject-mass / H5 / veto separation (no peek)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.horizon.eval import N_BOOT, annotate_hygiene_flags, format_report, k_for
from src.horizon.eval.admission import fit_veto_last_fold
from src.horizon.eval.path_quality_veto import (
    DEFAULT_VETO_QUANTILE,
    MIN_REJECT_ROWS_FOR_POWER,
    NULL_LEVER_REJECT_MASS_MAX,
    evaluate_path_quality_step0,
    fit_veto_full_train,
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
        "Fitting locked Long path-EV (Step 0 -- not a peek) "
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

    print("Fitting multiclass veto head (purged val + full-train holdout)...")
    _vm, veto_val, veto_stats = fit_veto_last_fold(train_df)
    print(
        f"   Veto val bars={veto_stats.get('val_bars')} "
        f"splits={veto_stats.get('n_splits')} "
        f"reason={veto_stats.get('reason', 'ok')}"
    )
    veto_model, full_stats = fit_veto_full_train(train_df)
    if veto_model is None:
        print(f"Error: veto full-train fit failed: {full_stats}")
        sys.exit(1)
    veto_features = list(full_stats["features"])
    print(
        f"   Veto holdout model train_bars={full_stats.get('train_bars')} "
        f"features={len(veto_features)}"
    )

    metrics = evaluate_path_quality_step0(
        scored,
        n_boot=n_boot,
        seed=seed,
        veto_val=veto_val,
        veto_model=veto_model,
        veto_features=veto_features,
    )
    title = (
        f"Path-quality veto Step 0  fold={fold}  train={train_period}  "
        f"test={test_period}  (REPORT ONLY -- no peek)"
    )
    print()
    report = format_report(metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Path-quality veto Step 0: H5 reprint, P(SL) reject-mass probe, "
            "null-lever / min-power gates, A2 projection. Not a peek."
        )
    )
    parser.add_argument("--config", type=str, default="config/market_sectoral_symbols.yml")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN")
    parser.add_argument("--folds", type=str, default="A,B")
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

    print("Path-quality veto Step 0 -- REPORT ONLY (no peek); Long only")
    print(
        f"Folds={folds}  n_boot={args.n_boot}  "
        f"locked_q=P{int(DEFAULT_VETO_QUANTILE * 100)}  "
        f"null_max={NULL_LEVER_REJECT_MASS_MAX}  "
        f"min_reject_rows={MIN_REJECT_ROWS_FOR_POWER}"
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
        f"-> {'HOLD' if h5_ok else 'BROKEN — STOP at 0/2'}"
    )

    nulls = [m for m in all_metrics if m.name == "NULLlev" and m.side == "long"]
    null_both_fail = (
        len(nulls) >= 2 and all(not bool(m.gate_pass) for m in nulls)
    )
    print(
        f"  Null-lever (reject_mass<{NULL_LEVER_REJECT_MASS_MAX}): "
        f"values={[m.value for m in nulls]} "
        f"pass={[bool(m.gate_pass) for m in nulls]} "
        f"-> {'STOP at 0/2 (both null)' if null_both_fail else 'non-null OK'}"
    )

    powers = [m for m in all_metrics if m.name == "POWERrej" and m.side == "long"]
    power_ok = all(bool(m.gate_pass) for m in powers) if powers else False
    print(
        f"  Min-power reject rows>={MIN_REJECT_ROWS_FOR_POWER}: "
        f"{[m.value for m in powers]} "
        f"-> {'OK — Peek 1 authorized on power' if power_ok else 'STOP at 0/2 (underpowered)'}"
    )

    for tag in (70, 80, 90):
        ms = [m for m in all_metrics if m.name == f"REJp{tag}" and m.side == "long"]
        if ms:
            print(
                f"  Top-K reject-mass P{tag}: "
                + ", ".join(
                    f"{m.value:.4f}" if m.value is not None else "-" for m in ms
                )
            )

    a2_notes = []
    for m in all_metrics:
        if m.name == "A2sug" and m.side == "long":
            a2_notes.append(m.note)
    # A2sug already encodes per-fold suggestion; take min bars across folds.
    a2s = [m for m in all_metrics if m.name == "A2sug" and m.side == "long"]
    if a2s:
        min_bars = min(int(m.value) for m in a2s if m.value is not None)
        print(f"  A2sug notes: {a2_notes}")
        print(
            f"  A2 pre-register (dual-fold min bars from suggestions): "
            f"min_bars≈{min_bars} — lock sessions from Step 0 A2sug notes before Peek 1"
        )

    authorize = h5_ok and (not null_both_fail) and power_ok
    print(
        f"\n  Peek 1 authorize: "
        f"{'YES — lock A2 floors then spend P(SL) veto' if authorize else 'NO — STOP-MEMO at 0/2'}"
    )


if __name__ == "__main__":
    main()
