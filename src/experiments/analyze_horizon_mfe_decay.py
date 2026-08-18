"""AUDIT-ONLY (fresh M0 quarantine). See docs/archive/horizon-fresh-quarantine-index.md. MFE-decay Step 0 diagnostic — peak bar + giveback + exit-clock (no peek)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.eval import N_BOOT, annotate_hygiene_flags, format_report, k_for
from src.horizon.eval.mfe_decay import (
    HARD_STOP_GIVEBACK_MAX,
    HARD_STOP_MFE_MAX,
    evaluate_mfe_decay,
    select_e1_h_eff,
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

    print("Loading Horizon universe + building features/labels/TB+MFE-decay...")
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
    metrics = evaluate_mfe_decay(scored, directions=scored_dirs)
    title = (
        f"MFE-decay Step 0  fold={fold}  train={train_period}  "
        f"test={test_period}  dirs={','.join(scored_dirs)}  (REPORT ONLY -- no peek)"
    )
    print()
    report = format_report(metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    return metrics


def _summarize(all_metrics: list, directions: list[str], folds: list[str]) -> None:
    """Cross-fold hard-stop + contingent lever implication (Long primary)."""
    print("\n=== Step 0 hard-stop / lever implication ===")
    print(
        f"Cuts: Top-K mean MFE < {HARD_STOP_MFE_MAX} AND "
        f"giveback < {HARD_STOP_GIVEBACK_MAX} on both folds -> STOP @ 0/2"
    )

    for direction in directions:
        hs = [m for m in all_metrics if m.name == "HARDSTOP" and m.side == direction]
        mfes = [m for m in all_metrics if m.name == "MFEabs" and m.side == direction]
        gbs = [m for m in all_metrics if m.name == "GIVEBACK" and m.side == direction]
        peaks = [m for m in all_metrics if m.name == "PEAKbar" and m.side == direction]
        earlys = [m for m in all_metrics if m.name == "EARLYpk" and m.side == direction]

        if not hs:
            print(f"  {direction}: no HARDSTOP metrics")
            continue

        both_hs = all(bool(m.gate_pass) for m in hs)
        mfe_vals = [m.value for m in mfes if m.value is not None]
        gb_vals = [m.value for m in gbs if m.value is not None]
        peak_vals = [m.value for m in peaks if m.value is not None]
        early_vals = [m.value for m in earlys if m.value is not None]

        print(
            f"  {direction}: folds={folds} "
            f"HARDSTOP={[bool(m.gate_pass) for m in hs]} "
            f"MFE={[f'{v:.3f}' for v in mfe_vals]} "
            f"GB={[f'{v:.3f}' for v in gb_vals]} "
            f"peak_med={[f'{v:.2f}' for v in peak_vals]}"
        )

        if direction != "long":
            print(f"  {direction}: companion only -- no Short peek authorization")
            continue

        if both_hs:
            print(
                "  long: DUAL-FOLD HARD-STOP FIRED -> STOP @ 0/2 "
                "(never approaches TP + null giveback)"
            )
            continue

        material_gb = any(v is not None and v >= HARD_STOP_GIVEBACK_MAX for v in gb_vals)
        near_tp = any(v is not None and v >= 0.85 for v in mfe_vals)
        early_pattern = (
            len(early_vals) >= 2
            and all(v is not None and v >= 0.5 for v in early_vals)
            and material_gb
        )
        late_pattern = (
            len(early_vals) >= 2
            and all(v is not None and v < 0.5 for v in early_vals)
        )

        h_eff = select_e1_h_eff(
            [float(v) for v in peak_vals],
            [float(v) for v in early_vals],
        )

        print(
            f"  long: near_tp={near_tp} material_gb={material_gb} "
            f"early_pattern={early_pattern} late_pattern={late_pattern} "
            f"E1_H_eff={h_eff}"
        )
        if h_eff is not None and material_gb:
            print(
                f"  long: contingent Peek 1 candidate = E1 (H_eff={h_eff}) "
                "[ladder order; lock before peek]"
            )
        elif material_gb:
            print(
                "  long: E1 not usable from peak-bar rule; "
                "E2 giveback hold candidate if pooled cut visible "
                "(pre-register threshold before peek; no A-tune/B-confirm)"
            )
        elif late_pattern:
            print(
                "  long: late-peak pattern — E3 TOD screen only if TOD buckets "
                "dominate; do not reopen H without dual-judge"
            )
        else:
            print(
                "  long: no clear E1/E2 implication from Step 0 "
                "-> STOP @ 0/2 if neither lever matches"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "MFE-decay Step 0: peak bar + giveback + exit-clock on Fold A/B. "
            "Not a peek — hard-stop / contingent lever input before any Long exit peek."
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
    )
    # Kept for CLI parity with path-density harness; Step 0 has no bootstrap gates.
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
    print("MFE-decay Step 0 -- REPORT ONLY (no peek)")
    print(f"Folds={folds}  directions={directions}")

    all_metrics = []
    for fold in folds:
        all_metrics.extend(
            _run_fold(
                fold,
                data_dir,
                config_path,
                directions,
            )
        )

    _summarize(all_metrics, directions, folds)


if __name__ == "__main__":
    main()
