"""AUDIT-ONLY — EV-net rebuild Step 0 (M0 baseline reprint OK).

See docs/archive/horizon-fresh-quarantine-index.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.horizon.eval import format_report
from src.horizon.eval.ev_net_rebuild import (
    E0_CI_BLOCK,
    E0_CI_METHOD,
    E0_N_BOOT,
    candidate_dual_fold_feasible,
    e2_floors_for_geometry,
    evaluate_step0_geometries,
    hard_stop_fires,
    select_freeze_geometry,
)
from src.labels.ev_net_geometry import GEOMETRY_CANDIDATES
from src.labels.triple_barrier import BPS, ROUND_TRIP_COST
from src.pipelines.build_horizon_features import load_horizon_data
from src.pipelines.build_regime_features import (
    build_regime_features,
    load_regime_data,
)
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
) -> tuple[list, list]:
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

    print("Loading Horizon universe OHLCV (geometry labels only -- no GBM)...")
    stock_15m, _nifty, _sector, _daily_stock, _daily_nifty = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    # Holdout only — Step 0 unconditional EV_net is a test-fold feasibility probe.
    test_stock = filter_by_period(
        stock_15m, test_start, test_end, datetime_col="date"
    )
    test_regime = filter_by_period(
        regime_df, test_start, test_end, datetime_col="date"
    )
    print(f"   Test stock rows={test_stock.height}  regime rows={test_regime.height}")
    if test_stock.height == 0 or test_regime.height == 0:
        print("Error: empty holdout after period filter.")
        sys.exit(1)

    print(
        "Step 0a geometry probe (REPORT ONLY -- not a peek) "
        f"c*={ROUND_TRIP_COST:.4f} n_boot={n_boot}..."
    )
    stats, metrics = evaluate_step0_geometries(
        test_stock,
        test_regime,
        fold,
        n_boot=n_boot,
        seed=seed,
    )
    title = (
        f"EV-net Step 0a  fold={fold}  train={train_period}  "
        f"test={test_period}  (REPORT ONLY -- no peek)"
    )
    print()
    report = format_report(metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    return stats, metrics


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "EV-net rebuild Step 0: unconditional-eligible EV_net under ≤3 "
            "pre-registered Long geometries on Fold A/B. Not a peek — "
            "hard-stop / freeze input before Peek 1."
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
    parser.add_argument("--n-boot", type=int, default=E0_N_BOOT)
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

    print("EV-net rebuild Step 0 -- REPORT ONLY (no peek); Long only")
    print(f"Folds={folds}  n_boot={args.n_boot}  c*={ROUND_TRIP_COST:.4f}")
    print("Pre-registered geometries:")
    for g in GEOMETRY_CANDIDATES:
        print(
            f"  {g.name}: H={g.horizon_bars} "
            f"TP={g.tp_floor * BPS:.0f}bps SL={g.sl_floor * BPS:.0f}bps "
            f"vol_mult={g.tp_vol_mult}/{g.sl_vol_mult}"
        )

    all_stats = []
    for fold in folds:
        stats, _metrics = _run_fold(
            fold, data_dir, config_path, args.n_boot, args.seed
        )
        all_stats.extend(stats)

    print("\n=== Step 0 hard-stop + freeze summary (Long) ===")
    print(
        "Hard-stop cut: dual-fold CI UB <= -10 bps -> candidate infeasible; "
        "all infeasible -> STOP @ 0/3"
    )
    for g in GEOMETRY_CANDIDATES:
        fold_rows = [s for s in all_stats if s.geometry == g.name]
        feasible = candidate_dual_fold_feasible(all_stats, g.name)
        parts = []
        for s in fold_rows:
            parts.append(
                f"{s.fold}: ev={s.mean_ev_net * BPS:.1f}bps "
                f"CI=[{s.ci_lo * BPS:.1f},{s.ci_hi * BPS:.1f}] "
                f"n={s.n_eligible} TP/SL/TO="
                f"{s.p_tp:.2f}/{s.p_sl:.2f}/{s.p_to:.2f}"
            )
        print(
            f"  {g.name}: feasible={feasible} | " + " || ".join(parts)
        )

    stop = hard_stop_fires(all_stats)
    freeze = None if stop else select_freeze_geometry(all_stats)
    if stop:
        print(
            "\nHARD-STOP FIRED: all candidates dual-fold infeasible "
            "(CI UB <= -10 bps). Ledger STOP @ 0/3 -- no Peek 1; no geometry redraw."
        )
        sys.exit(0)

    assert freeze is not None
    floors = e2_floors_for_geometry(all_stats, freeze.name)
    print(f"\nSTEP 0b FREEZE: {freeze.name}")
    print(
        f"  geometry: H={freeze.horizon_bars} "
        f"TP_floor={freeze.tp_floor * BPS:.0f}bps "
        f"SL_floor={freeze.sl_floor * BPS:.0f}bps "
        f"vol_mult={freeze.tp_vol_mult}/{freeze.sl_vol_mult}"
    )
    print(
        f"  E0 CI scheme: method={E0_CI_METHOD} block={E0_CI_BLOCK} "
        f"n_boot={floors['n_boot']} (frozen -- no post-hoc method shopping)"
    )
    print(
        f"  E2 floors (dual-fold min of oracle EV_net>0 mass): "
        f"min_bars={floors['min_bars']} min_sessions={floors['min_sessions']} "
        f"(projected_adm bars/sess={floors['projected_adm_bars']}/"
        f"{floors['projected_adm_sess']})"
    )
    print("  Peek 1 authorized: absolute calibrated EV_net>0 admit under this freeze.")


if __name__ == "__main__":
    main()
