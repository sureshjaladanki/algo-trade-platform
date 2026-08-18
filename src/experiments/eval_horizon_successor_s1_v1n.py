"""Successor S1 — P1 V1n nested HAR, V1κ, V2p (only if V1n PASS).

Pre-registration: docs/archive/horizon-successor-s1-preregistration.md
Do not call eval_horizon_m9_v2_stub. Index-only; no volume_z.

    poetry run python -m src.experiments.eval_horizon_successor_s1_v1n --folds A B
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.horizon.fresh.folds import FOLDS, apply_purge_date_filter, fold_spec
from src.horizon.fresh.gates import declare_admit_power
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    remaining_session_range,
)
from src.horizon.m9.har_range import attach_causal_har_remaining_range
from src.horizon.m9.implied_range import (
    DEFAULT_RANGE_KAPPA,
    attach_vix_implied_range,
    daily_vix_from_1m,
)
from src.horizon.m9.v1_incremental import demean_within_clock, incremental_range_ols
from src.horizon.m9.v2p_range import select_v2p_sessions, v2p_session_gate
from src.utils.data import resample_15m
from src.utils.date import filter_by_period, parse_period_range
from src.utils.symbol_data import load_symbol_data

REPO_ROOT = Path(__file__).resolve().parents[2]

INDEX_OPPORTUNITY_FEATURES: tuple[str, ...] = tuple(
    f for f in OPPORTUNITY_FEATURES if f != "volume_z"
)
KAPPA_SENSITIVITY: tuple[float, ...] = (1.4, 1.6, 1.8)


def _nifty_15m(data_dir: Path, start: str, end: str) -> pl.DataFrame:
    raw = load_symbol_data(
        data_dir / "^NSEI.csv", start_period=start, end_period=end
    )
    return (
        resample_15m(raw)
        .with_columns(pl.lit("^NSEI").alias("symbol"))
        .select(["symbol", "date", "open", "high", "low", "close", "volume"])
    )


def _print_ols(tag: str, res) -> None:
    extra = ""
    if res.coef_controls:
        extra = " ctrl=" + ",".join(f"{c:+.3f}" for c in res.coef_controls)
    status = "PASS" if res.passed else "FAIL"
    print(
        f"   {tag} {status} n={res.n} R2={res.r2:.3f} "
        f"b_imp={res.coef_implied:+.3f} b_q50={res.coef_q50:+.3f} "
        f"t_q50={res.t_q50:+.2f} p={res.p_q50:.4g}{extra} ({res.note})"
    )


def _run_fold(
    fold: str,
    data_dir: Path,
    vix_path: Path,
) -> dict:
    spec = fold_spec(fold)
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(
        f"\n=== S1 V1n fold {fold} "
        f"train={cfg['train_period']} test={cfg['test_period']} "
        f"purge={spec.purge_calendar_days}d ==="
    )

    nifty = _nifty_15m(
        data_dir, min(train_start, test_start), max(train_end, test_end)
    )
    vix_1m = load_symbol_data(
        vix_path,
        start_period=min(train_start, test_start),
        end_period=max(train_end, test_end),
    )
    vix_daily = daily_vix_from_1m(vix_1m)

    panel = remaining_session_range(attach_opportunity_features(nifty))
    panel = panel.filter(pl.col("bars_to_mis") > 0)
    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
    train_end_year = int(str(spec.train_period).split("-")[1][:4])
    train = apply_purge_date_filter(
        train, train_end_year, spec.purge_calendar_days
    )
    test = filter_by_period(panel, test_start, test_end, datetime_col="date")

    feats = list(INDEX_OPPORTUNITY_FEATURES)
    keep = [*feats, "remaining_range"]
    finite = pl.all_horizontal([pl.col(c).is_finite() for c in keep])
    tr = train.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    te = test.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    print(f"   train={tr.height} test={te.height} feats={feats}")

    model = OpportunityModel().fit(
        tr.select(feats).to_numpy(),
        tr["remaining_range"].to_numpy(),
    )
    q = model.predict_quantiles(te.select(feats).to_numpy())
    te = te.with_columns(range_q50=pl.Series(q["range_q50"]))
    te = attach_causal_har_remaining_range(te, kappa=DEFAULT_RANGE_KAPPA)
    te = attach_vix_implied_range(te, vix_daily, kappa=DEFAULT_RANGE_KAPPA)

    # V1κ report-only (two-regressor V1, no HAR). Implied is linear in κ.
    kappa_flags: dict[float, bool] = {}
    imp = te["range_imp_vix"].to_numpy()
    for kappa in KAPPA_SENSITIVITY:
        res_k = incremental_range_ols(
            te["remaining_range"].to_numpy(),
            imp * (kappa / DEFAULT_RANGE_KAPPA),
            te["range_q50"].to_numpy(),
        )
        _print_ols(f"V1k kappa={kappa:.1f}", res_k)
        kappa_flags[kappa] = res_k.passed
    extras = np.column_stack(
        [te["range_har_1d"].to_numpy(), te["range_har_5d"].to_numpy()]
    )
    res_n = incremental_range_ols(
        te["remaining_range"].to_numpy(),
        te["range_imp_vix"].to_numpy(),
        te["range_q50"].to_numpy(),
        extra_controls=extras,
    )
    _print_ols("V1n", res_n)

    clock = te["bars_to_mis"].to_numpy()
    res_clk = incremental_range_ols(
        demean_within_clock(te["remaining_range"].to_numpy(), clock),
        demean_within_clock(te["range_imp_vix"].to_numpy(), clock),
        demean_within_clock(te["range_q50"].to_numpy(), clock),
        extra_controls=np.column_stack(
            [
                demean_within_clock(te["range_har_1d"].to_numpy(), clock),
                demean_within_clock(te["range_har_5d"].to_numpy(), clock),
            ]
        ),
        require_positive=False,
    )
    _print_ols("V1n within-clock", res_clk)

    return {
        "fold": fold,
        "v1n": res_n,
        "v1n_clock": res_clk,
        "kappa": kappa_flags,
        "panel": te,
    }


def _run_v2p(fold_rows: list[dict]) -> list:
    print("\n=== S1 V2p (pre-registered residual > 0, first bar) ===")
    expected_sess = 220
    plan = declare_admit_power(expected_sess // 2, expected_sess, assumed_sigma=0.004)
    print(
        f"   AdmitPowerPlan (per fold, ~half selected) n={plan.expected_admit_n} "
        f"sess={plan.expected_sessions} expected_mde={plan.expected_mde_bps:.1f}bps "
        f"({plan.note})"
    )
    gates = []
    for row in fold_rows:
        selected = select_v2p_sessions(row["panel"])
        gate = v2p_session_gate(selected, fold=row["fold"])
        print(
            f"   fold {row['fold']} selected={selected.height} "
            f"{gate.verdict} mean={gate.value:+.5f} {gate.note}"
        )
        gates.append(gate)
    return gates


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
        "Successor S1 V1n - nested HAR on Nifty. "
        "Prereg: docs/archive/horizon-successor-s1-preregistration.md"
    )
    rows = [
        _run_fold(fold, args.data_dir, args.vix_path) for fold in args.folds
    ]
    v1n_dual = all(r["v1n"].passed for r in rows) and len(rows) >= 2
    print(f"\nV1n dual-fold={'PASS' if v1n_dual else 'FAIL'}")
    if not v1n_dual:
        print("P1 STOP - do not salvage with name V1. Do not run V2p.")
        sys.exit(2)

    gates = _run_v2p(rows)
    dual_v2p = all(g.verdict == "PASS" for g in gates) and len(gates) >= 2
    any_fail = any(g.verdict == "FAIL" for g in gates)
    print(f"V2p dual-fold={'PASS' if dual_v2p else 'FAIL' if any_fail else 'INCONCLUSIVE'}")
    if dual_v2p:
        sys.exit(0)
    if any_fail:
        print("P1 STOP - incremental information without signed range-space economics.")
        sys.exit(2)
    print("V2p INCONCLUSIVE - repair / do not record FAIL.")
    sys.exit(3)


if __name__ == "__main__":
    main()
