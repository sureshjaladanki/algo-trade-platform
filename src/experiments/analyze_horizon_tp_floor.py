"""AUDIT-ONLY (fresh M0 quarantine). See docs/archive/horizon-fresh-quarantine-index.md. TP-floor Step 0 diagnostic — absolute MFE crossing @ 50 vs 60 bps (no peek)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.eval import annotate_hygiene_flags, format_report, k_for
from src.horizon.eval.tp_floor import (
    HARD_STOP_MEAN_MFE_MIN,
    HARD_STOP_NEAR_MISS_MIN,
    HARD_STOP_SL_CONTAM_MAX,
    evaluate_tp_floor,
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

    print("Loading Horizon universe + building features/labels/TB+TP-floor...")
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
        f"K_long={k_for('long')}..."
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
    metrics = evaluate_tp_floor(scored, directions=scored_dirs)
    title = (
        f"TP-floor Step 0  fold={fold}  train={train_period}  "
        f"test={test_period}  dirs={','.join(scored_dirs)}  (REPORT ONLY -- no peek)"
    )
    print()
    report = format_report(metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    return metrics


def _summarize(all_metrics: list, directions: list[str], folds: list[str]) -> None:
    """Cross-fold hard-stop + T1 implication (Long only)."""
    print("\n=== Step 0 hard-stop / T1 implication ===")
    print(
        f"Cuts (OR; either fold): near-miss < {HARD_STOP_NEAR_MISS_MIN} OR "
        f"SLcontam > {HARD_STOP_SL_CONTAM_MAX} OR "
        f"mean Abs MFE < {HARD_STOP_MEAN_MFE_MIN} bps -> STOP @ 0/1"
    )

    for direction in directions:
        hs = [m for m in all_metrics if m.name == "HARDSTOP" and m.side == direction]
        nears = [m for m in all_metrics if m.name == "NEARMISS" and m.side == direction]
        contams = [
            m for m in all_metrics if m.name == "SLcontam" and m.side == direction
        ]
        mfes = [m for m in all_metrics if m.name == "MFEbps" and m.side == direction]
        deltas = [m for m in all_metrics if m.name == "DELTA" and m.side == direction]

        if not hs:
            print(f"  {direction}: no HARDSTOP metrics")
            continue

        any_hs = any(bool(m.gate_pass) for m in hs)
        near_vals = [m.value for m in nears if m.value is not None]
        contam_vals = [m.value for m in contams if m.value is not None]
        mfe_vals = [m.value for m in mfes if m.value is not None]
        delta_vals = [m.value for m in deltas if m.value is not None]

        print(
            f"  {direction}: folds={folds} "
            f"HARDSTOP={[bool(m.gate_pass) for m in hs]} "
            f"near={[f'{v:.3f}' for v in near_vals]} "
            f"SLcontam={[f'{v:.3f}' for v in contam_vals]} "
            f"MFEbps={[f'{v:.2f}' for v in mfe_vals]} "
            f"delta={[f'{v:.3f}' for v in delta_vals]}"
        )

        if direction != "long":
            print(f"  {direction}: omitted this charter — no Short peek")
            continue

        if any_hs:
            print(
                "  long: EITHER-FOLD HARD-STOP FIRED -> STOP @ 0/1 "
                "(T1 not authorized)"
            )
            continue

        both_near_ok = (
            len(near_vals) >= 2
            and all(v is not None and v >= HARD_STOP_NEAR_MISS_MIN for v in near_vals)
        )
        if both_near_ok:
            print(
                "  long: hard-stop clear; near-miss >=5% both folds "
                "-> T1 AUTHORIZED (Long TP floor 60->50; retrain+relabel)"
            )
        else:
            print(
                "  long: hard-stop clear but near-miss pattern incomplete "
                "-> review before T1"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "TP-floor Step 0: absolute MFE crossing @ 50 vs 60 bps on Fold A/B. "
            "Long only. Not a peek — hard-stop / T1 gate before any floor peek."
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
        default="long",
        choices=["long", "short", "both"],
        help="Charter default: long only",
    )
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
    print("TP-floor Step 0 -- REPORT ONLY (no peek)")
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
