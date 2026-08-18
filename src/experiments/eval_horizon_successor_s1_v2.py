"""Successor S1 V2 — remaining-session short Nifty straddle on V2p-c sessions.

Pre-registration: docs/archive/horizon-successor-s1-v2-preregistration.md
Hard-exits if S4-P1 snapshots are missing. Does not call eval_horizon_m9_v2_stub.

    poetry run python -m src.experiments.eval_horizon_successor_s1_v2 --folds A B
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.experiments.eval_horizon_successor_s1_v2pc import _clock_panels
from src.horizon.fresh.friction import BPS
from src.horizon.fresh.gates import declare_admit_power, mde_from_ci
from src.horizon.m9.index_option_store import (
    COVERAGE_GATE,
    DEFAULT_SNAPSHOT_PATH,
    IndexOptionStoreMissingError,
    coverage_selected,
    load_nifty_option_snapshots,
    session_entry_exit,
)
from src.horizon.m9.v2_index_straddle import (
    attach_short_straddle_pnl,
    v2_selected_pnl,
    v2_session_gate,
)
from src.horizon.m9.v2p_range import fit_v2pc_scale, select_v2pc_sessions
from src.horizon.m9.zenodo_ltp import is_zenodo_last_trade
from src.utils.eval_common import N_BOOT, session_block_mean_ci

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_SELECTED = 80
EXPECTED_SESSIONS = 245


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--vix-path",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN" / "^INDIAVIX.csv",
    )
    parser.add_argument(
        "--snapshots",
        type=Path,
        default=REPO_ROOT / DEFAULT_SNAPSHOT_PATH,
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Last-trade companion: do not earn V3 or invoke P1 STOP.",
    )
    args = parser.parse_args()

    print(
        "Successor S1 V2 - 09:45 to 15:15 short ATM straddle on V2p-c. "
        "Prereg: docs/archive/horizon-successor-s1-v2-preregistration.md"
    )
    plan = declare_admit_power(
        EXPECTED_SELECTED, EXPECTED_SESSIONS, assumed_sigma=0.004
    )
    print(
        f"   AdmitPowerPlan n={plan.expected_admit_n} sess={plan.expected_sessions} "
        f"expected_mde={plan.expected_mde_bps:.1f}bps ({plan.note})"
    )
    try:
        raw = load_nifty_option_snapshots(args.snapshots)
    except IndexOptionStoreMissingError as exc:
        print(f"V2 INCONCLUSIVE - marks missing. {exc}")
        sys.exit(3)

    report_only = args.report_only or is_zenodo_last_trade(raw)
    if report_only:
        print(
            "V2 REPORT-ONLY - Zenodo last-trade (bid=ask=close). "
            "Prereg: docs/archive/horizon-successor-s1-v2-zenodo-preregistration.md. "
            "Not quote V2."
        )

    marks = session_entry_exit(raw)
    fold_ys: list[np.ndarray] = []
    fold_sess: list[np.ndarray] = []
    fold_paired: list[np.ndarray] = []
    fold_paired_sess: list[np.ndarray] = []
    gates = []
    for fold in args.folds:
        train_clock, test_clock = _clock_panels(fold, args.data_dir, args.vix_path)
        selected = select_v2pc_sessions(test_clock, fit_v2pc_scale(train_clock))
        cov = coverage_selected(selected["date_only"], marks)
        print(
            f"   fold {fold} selected={cov['n']} marked={cov['n_marked']} "
            f"coverage={cov['coverage']:.1%}"
        )
        if cov["n"] == 0 or cov["coverage"] < COVERAGE_GATE:
            print(
                f"V2 INCONCLUSIVE - coverage {cov['coverage']:.1%} "
                f"< {COVERAGE_GATE:.0%}. Do not peek. Do not use bhavcopy."
            )
            sys.exit(3)
        pnl = v2_selected_pnl(selected, marks)
        gate = v2_session_gate(pnl, fold=fold, n_boot=args.n_boot, seed=args.seed)
        print(f"   V2 {fold} {gate.verdict} mean={gate.value:+.5f} {gate.note}")
        if report_only:
            universe = attach_short_straddle_pnl(
                marks.join(test_clock.select("date_only").unique(), on="date_only", how="inner")
            )
            mu_all = float(universe["pnl"].mean()) if universe.height else float("nan")
            paired = pnl["pnl"].to_numpy().astype(float) - mu_all
            print(
                f"   companion paired vs all-session last-trade "
                f"mean={(float(np.nanmean(paired)) * BPS):+.1f}bps"
            )
        gates.append(gate)
        if np.isfinite(gate.value):
            y = pnl["pnl"].to_numpy().astype(float)
            sess = pnl["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
            m = np.isfinite(y)
            fold_ys.append(y[m])
            fold_sess.append(sess[m])
            if report_only:
                fold_paired.append(paired[m])
                fold_paired_sess.append(sess[m])

    any_thin = any(g.verdict == "INCONCLUSIVE" for g in gates)
    if any_thin or not fold_ys:
        print("V2 INCONCLUSIVE - thin marked PnL. Do not record FAIL.")
        sys.exit(3)

    y = np.concatenate(fold_ys)
    sess = np.concatenate(fold_sess)
    rng = np.random.default_rng(args.seed)
    point, lo, hi = session_block_mean_ci(y, sess, args.n_boot, rng)
    mde = mde_from_ci(lo, hi)
    n_pos = sum(1 for g in gates if np.isfinite(g.value) and g.value > 0)
    pooled_pass = lo > 0.0
    label = "V2 REPORT-ONLY pooled" if report_only else "V2 pooled"
    print(
        f"\n{label} {'PASS' if pooled_pass else 'FAIL'} "
        f"CI=[{lo * BPS:+.1f},{hi * BPS:+.1f}]bps "
        f"mean={point * BPS:+.1f}bps mde={mde * BPS:.1f}bps "
        f"sign={n_pos}/{len(gates)} n={y.size}"
    )
    if report_only:
        if fold_paired:
            yp = np.concatenate(fold_paired)
            sp = np.concatenate(fold_paired_sess)
            p_point, p_lo, p_hi = session_block_mean_ci(yp, sp, args.n_boot, rng)
            print(
                f"   companion paired CI=[{p_lo * BPS:+.1f},{p_hi * BPS:+.1f}]bps "
                f"mean={p_point * BPS:+.1f}bps n={yp.size}"
            )
        print(
            "Not quote V2. Does not earn V3. Does not invoke P1 STOP. "
            "Quote S4-P1 remains not started."
        )
        sys.exit(0)
    if pooled_pass:
        print("P1 V2 PASS - V3 earned (quoted spread + 2026 STT). Not a ship.")
        sys.exit(0)
    print("P1 STOP - V2 LB <= 0 in premium space. Do not salvage with name V1.")
    sys.exit(2)


if __name__ == "__main__":
    main()
