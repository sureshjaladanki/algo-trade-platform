"""Admission Peek 1 — Long conviction floor only (single-variable)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.horizon.eval import N_BOOT, annotate_hygiene_flags, format_report, k_for
from src.horizon.eval.admission import (
    DEFAULT_CONVICTION_QUANTILE,
    evaluate_conviction_peek,
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
    quantile: float,
    a2_min_bars: int,
    a2_min_sessions: int,
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
        f"Fitting locked Long path-EV; Peek 1 conviction floor P{int(quantile * 100)} "
        f"K={k_for('long')} A2={a2_min_bars}/{a2_min_sessions}..."
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

    metrics = evaluate_conviction_peek(
        scored,
        direction="long",
        quantile=quantile,
        n_boot=n_boot,
        seed=seed,
        a2_min_bars=a2_min_bars,
        a2_min_sessions=a2_min_sessions,
    )
    title = (
        f"Admission Peek 1 conviction  fold={fold}  "
        f"train={train_period}  test={test_period}  "
        f"q=P{int(quantile * 100)}  A2={a2_min_bars}/{a2_min_sessions}"
    )
    print()
    report = format_report(metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Admission Peek 1: inference-only Long conviction quantile floor. "
            "Requires Step 0 H5 hold + locked quantile + A2 floors."
        )
    )
    parser.add_argument("--config", type=str, default="config/market_sectoral_symbols.yml")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN")
    parser.add_argument("--folds", type=str, default="A,B")
    parser.add_argument(
        "--quantile",
        type=float,
        default=DEFAULT_CONVICTION_QUANTILE,
        help="Locked conviction floor (default P80 from charter)",
    )
    parser.add_argument(
        "--a2-min-bars",
        type=int,
        required=True,
        help="Pre-registered A2 min admitted bars (from Step 0)",
    )
    parser.add_argument(
        "--a2-min-sessions",
        type=int,
        required=True,
        help="Pre-registered A2 min admitted sessions (from Step 0)",
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
    if not (0.0 < args.quantile < 1.0):
        print("Error: --quantile must be in (0, 1).")
        sys.exit(1)

    folds = [f.strip().upper() for f in args.folds.split(",") if f.strip()]
    for fold in folds:
        if fold not in FOLDS:
            print(f"Error: unknown fold {fold}; expected one of {list(FOLDS)}")
            sys.exit(1)

    print(
        f"Admission Peek 1 -- conviction floor P{int(args.quantile * 100)} "
        f"(single variable; Long only)"
    )
    print(
        f"Folds={folds}  A2 min_bars={args.a2_min_bars} "
        f"min_sessions={args.a2_min_sessions}  n_boot={args.n_boot}"
    )

    all_metrics = []
    for fold in folds:
        all_metrics.extend(
            _run_fold(
                fold,
                data_dir,
                config_path,
                args.quantile,
                args.a2_min_bars,
                args.a2_min_sessions,
                args.n_boot,
                args.seed,
            )
        )

    print("\n=== Peek 1 gate summary (Long) ===")
    for name in ("H5", "H1", "H2", "H3", "A1", "A2"):
        ms = [m for m in all_metrics if m.name == name and m.side == "long"]
        if not ms:
            print(f"  {name}: missing")
            continue
        gates = [m.gate_pass for m in ms]
        vals = [
            f"{m.value:.4f}" if m.value is not None else "-"
            for m in ms
        ]
        print(f"  {name}: gates={gates} values={vals}")


if __name__ == "__main__":
    main()
