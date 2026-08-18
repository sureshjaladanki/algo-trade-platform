"""Successor S1 V2p-c — short residual, incremental to unconditional short vol.

Pre-registration: docs/archive/horizon-successor-s1-v2pc-preregistration.md
New selection definition. Does not retune residual>0. Does not scan 10:00.

    poetry run python -m src.experiments.eval_horizon_successor_s1_v2pc --folds A B
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.experiments.eval_horizon_successor_s1_v1n import (
    INDEX_OPPORTUNITY_FEATURES,
    _nifty_15m,
)
from src.horizon.fresh.folds import FOLDS, apply_purge_date_filter, fold_spec
from src.horizon.fresh.friction import BPS
from src.horizon.fresh.gates import declare_admit_power, mde_from_ci
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
    V2PC_ABORT_MDE_BPS,
    V2PC_TERCILE,
    first_post_open_clock,
    fit_v2pc_scale,
    select_v2pc_sessions,
    v2pc_paired_values,
    v2pc_session_gate,
)
from src.utils.date import filter_by_period, parse_period_range
from src.utils.eval_common import N_BOOT, session_block_mean_ci
from src.utils.symbol_data import load_symbol_data

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_SESSIONS = 245
EXPECTED_SELECTED = 80
EXPECTED_POOLED = 160


def _clock_panels(
    fold: str,
    data_dir: Path,
    vix_path: Path,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    spec = fold_spec(fold)
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(
        f"\n=== S1 V2p-c fold {fold} "
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
    q_tr = model.predict_quantiles(tr.select(feats).to_numpy())
    q_te = model.predict_quantiles(te.select(feats).to_numpy())
    tr = tr.with_columns(range_q50=pl.Series(q_tr["range_q50"]))
    te = te.with_columns(range_q50=pl.Series(q_te["range_q50"]))
    tr = attach_vix_implied_range(tr, vix_daily, kappa=DEFAULT_RANGE_KAPPA)
    te = attach_vix_implied_range(te, vix_daily, kappa=DEFAULT_RANGE_KAPPA)
    return first_post_open_clock(tr), first_post_open_clock(te)


def _pooled_gate(
    fold_ys: list[np.ndarray],
    fold_sess: list[np.ndarray],
    *,
    n_boot: int,
    seed: int,
):
    y = np.concatenate(fold_ys)
    sess = np.concatenate(fold_sess)
    m = np.isfinite(y)
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(y[m], sess[m], n_boot, rng)
    mde = mde_from_ci(lo, hi)
    return point, lo, hi, mde, int(m.sum()), int(np.unique(sess[m]).size)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--vix-path",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN" / "^INDIAVIX.csv",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    print(
        "Successor S1 V2p-c - 09:45 bottom tercile, paired (R_imp-R). "
        "Prereg: docs/archive/horizon-successor-s1-v2pc-preregistration.md"
    )
    plan = declare_admit_power(
        EXPECTED_SELECTED, EXPECTED_SESSIONS, assumed_sigma=0.004
    )
    plan_p = declare_admit_power(
        EXPECTED_POOLED, EXPECTED_POOLED, assumed_sigma=0.004
    )
    print(
        f"   locked clock>={V2P_POST_OPEN_MIN_TIME} tercile={V2PC_TERCILE:.2f} "
        f"kappa={DEFAULT_RANGE_KAPPA} abort_mde={V2PC_ABORT_MDE_BPS:.0f}bps"
    )
    print(
        f"   AdmitPowerPlan per-fold n={plan.expected_admit_n} "
        f"sess={plan.expected_sessions} expected_mde={plan.expected_mde_bps:.1f}bps "
        f"({plan.note})"
    )
    print(
        f"   AdmitPowerPlan pooled n={plan_p.expected_admit_n} "
        f"expected_mde={plan_p.expected_mde_bps:.1f}bps ({plan_p.note})"
    )
    if plan.expected_mde_bps > V2PC_ABORT_MDE_BPS:
        print(
            f"V2p-c INCONCLUSIVE - declared MDE {plan.expected_mde_bps:.1f}bps "
            f"> {V2PC_ABORT_MDE_BPS:.0f}bps. Abort before selection."
        )
        sys.exit(3)

    gates = []
    fold_ys: list[np.ndarray] = []
    fold_sess: list[np.ndarray] = []
    for fold in args.folds:
        train_clock, test_clock = _clock_panels(fold, args.data_dir, args.vix_path)
        scale = fit_v2pc_scale(train_clock)
        selected = select_v2pc_sessions(test_clock, scale)
        n_sess = test_clock.height
        print(
            f"   scale a={scale.intercept:+.4f} b={scale.slope:+.3f} "
            f"resid_mu={scale.resid_mean:+.5f} resid_sd={scale.resid_std:.5f} "
            f"z_terc={scale.tercile_threshold:+.3f}"
        )
        print(
            f"   test_sessions={n_sess} selected={selected.height} "
            f"share={selected.height / max(n_sess, 1):.1%}"
        )
        gate = v2pc_session_gate(
            selected, test_clock, fold=fold, n_boot=args.n_boot, seed=args.seed
        )
        sign = "n/a"
        if np.isfinite(gate.value):
            sign = "pos" if gate.value > 0 else "nonpos"
            y = v2pc_paired_values(selected, test_clock)
            sess = selected["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
            m = np.isfinite(y)
            fold_ys.append(y[m])
            fold_sess.append(sess[m])
        print(
            f"   V2p-c {fold} {gate.verdict} mean={gate.value:+.5f} "
            f"sign={sign} {gate.note}"
        )
        gates.append(gate)

    any_thin = any(g.verdict == "INCONCLUSIVE" for g in gates)
    if any_thin:
        print(
            "\nV2p-c INCONCLUSIVE - thin selected set. "
            "Do not retune residual>0. Do not acquire marks."
        )
        sys.exit(3)

    point, lo, hi, mde, n, n_sess = _pooled_gate(
        fold_ys, fold_sess, n_boot=args.n_boot, seed=args.seed
    )
    n_pos = sum(1 for g in gates if np.isfinite(g.value) and g.value > 0)
    pooled_pass = lo > 0.0
    print(
        f"\nV2p-c pooled {'PASS' if pooled_pass else 'FAIL'} "
        f"CI=[{lo * BPS:+.1f},{hi * BPS:+.1f}]bps "
        f"mean={point * BPS:+.1f}bps mde={mde * BPS:.1f}bps "
        f"sign={n_pos}/{len(gates)} n={n} sess={n_sess}"
    )
    if pooled_pass:
        print("P1 V2p-c PASS - index option marks (S4-P1) are earned, not automatic.")
        sys.exit(0)
    print("P1 STOP - V2p-c LB <= 0 on a passable harness. Do not salvage with name V1.")
    sys.exit(2)


if __name__ == "__main__":
    main()
