"""Successor S1 V2p-b - post-open residual on Nifty (clock repair).

Pre-registration: docs/archive/horizon-successor-s1-v2pb-preregistration.md
Does not re-peek V1n. Does not call eval_horizon_m9_v2_stub.

    poetry run python -m src.experiments.eval_horizon_successor_s1_v2pb --folds A B
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.experiments.eval_horizon_successor_s1_v1n import (
    INDEX_OPPORTUNITY_FEATURES,
    _nifty_15m,
)
from src.horizon.fresh.folds import FOLDS, apply_purge_date_filter, fold_spec
from src.horizon.fresh.gates import declare_admit_power
from src.horizon.fresh.opportunity import (
    OpportunityModel,
    attach_opportunity_features,
    remaining_session_range,
)
from src.horizon.m9.implied_range import (
    DEFAULT_RANGE_KAPPA,
    attach_vix_implied_range,
    daily_vix_from_1m,
)
from src.horizon.m9.v2p_range import (
    V2P_POST_OPEN_MIN_TIME,
    V2P_RESIDUAL_THRESHOLD,
    select_v2p_post_open_sessions,
    v2p_session_gate,
)
from src.utils.date import filter_by_period, parse_period_range
from src.utils.symbol_data import load_symbol_data

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_SESSIONS = 220
EXPECTED_SELECTED = 110


def _test_panel(
    fold: str,
    data_dir: Path,
    vix_path: Path,
) -> pl.DataFrame:
    spec = fold_spec(fold)
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(
        f"\n=== S1 V2p-b fold {fold} "
        f"train={cfg['train_period']} test={cfg['test_period']} ==="
    )
    nifty = _nifty_15m(
        data_dir, min(train_start, test_start), max(train_end, test_end)
    )
    vix_daily = daily_vix_from_1m(
        load_symbol_data(
            vix_path,
            start_period=min(train_start, test_start),
            end_period=max(train_end, test_end),
        )
    )
    panel = remaining_session_range(attach_opportunity_features(nifty))
    panel = panel.filter(pl.col("bars_to_mis") > 0)
    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
    train_end_year = int(str(spec.train_period).split("-")[1][:4])
    train = apply_purge_date_filter(train, train_end_year, spec.purge_calendar_days)
    test = filter_by_period(panel, test_start, test_end, datetime_col="date")
    feats = list(INDEX_OPPORTUNITY_FEATURES)
    keep = [*feats, "remaining_range"]
    finite = pl.all_horizontal([pl.col(c).is_finite() for c in keep])
    tr = train.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    te = test.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    model = OpportunityModel().fit(
        tr.select(feats).to_numpy(),
        tr["remaining_range"].to_numpy(),
    )
    q = model.predict_quantiles(te.select(feats).to_numpy())
    te = te.with_columns(range_q50=pl.Series(q["range_q50"]))
    return attach_vix_implied_range(te, vix_daily, kappa=DEFAULT_RANGE_KAPPA)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--vix-path",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN" / "^INDIAVIX.csv",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    args = parser.parse_args()

    print(
        "Successor S1 V2p-b - first bar at/after 09:45, residual > 0. "
        "Prereg: docs/archive/horizon-successor-s1-v2pb-preregistration.md"
    )
    plan = declare_admit_power(
        EXPECTED_SELECTED, EXPECTED_SESSIONS, assumed_sigma=0.004
    )
    print(
        f"   locked clock>={V2P_POST_OPEN_MIN_TIME} "
        f"threshold={V2P_RESIDUAL_THRESHOLD} "
        f"AdmitPowerPlan n={plan.expected_admit_n} sess={plan.expected_sessions} "
        f"expected_mde={plan.expected_mde_bps:.1f}bps ({plan.note})"
    )

    gates = []
    for fold in args.folds:
        te = _test_panel(fold, args.data_dir, args.vix_path)
        selected = select_v2p_post_open_sessions(te)
        n_sess = te["date_only"].n_unique()
        print(
            f"   test_sessions={n_sess} selected={selected.height} "
            f"share={selected.height / max(n_sess, 1):.1%}"
        )
        gate = v2p_session_gate(selected, fold=fold)
        print(
            f"   V2p-b {gate.verdict} mean={gate.value:+.5f} {gate.note}"
        )
        gates.append(gate)

    dual = all(g.verdict == "PASS" for g in gates) and len(gates) >= 2
    any_fail = any(g.verdict == "FAIL" for g in gates)
    any_thin = any("thin" in (g.note or "") for g in gates)
    print(
        f"\nV2p-b dual-fold="
        f"{'PASS' if dual else 'FAIL' if any_fail else 'INCONCLUSIVE'}"
    )
    if dual:
        print("P1 V2p PASS - index option marks (S4-P1) are earned, not automatic.")
        sys.exit(0)
    if any_fail:
        print("P1 STOP - signed range-space economics fail. Do not salvage with name V1.")
        sys.exit(2)
    if any_thin:
        print(
            "V2p-b still thin at 09:45 - do not scan other clocks. "
            "INCONCLUSIVE; residual>0 is not a session product on this charter."
        )
        sys.exit(3)
    print("V2p-b INCONCLUSIVE - CI includes 0. Repair power; do not record FAIL.")
    sys.exit(3)


if __name__ == "__main__":
    main()
