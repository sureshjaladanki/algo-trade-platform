"""Successor S6 — multi-day fade on frozen prior_day_high_reject Short.

Charter: docs/next/horizon-successor-s6-multiday-fade-charter.md
In-repo daily bars. No SSF download. No new event rules.

    poetry run python -m src.experiments.eval_horizon_successor_s6_multiday
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.horizon.fresh.candidate_events import (
    build_candidate_event_panel,
    transition_candidate_events,
)
from src.horizon.fresh.folds import ROLLING_FOLDS
from src.horizon.fresh.friction import BPS
from src.horizon.fresh.gates import (
    declare_admit_power,
    k5_economics,
    k5_pooled,
    path_ev_net,
)
from src.horizon.successor.fade_bound import (
    DISASTER_SL,
    PRIMARY_RULE_ID,
    S6_AUTHORITY_HORIZON,
    S6_HAIRCUTS_BPS,
    S6_HORIZONS,
    S6_HURDLE_BPS,
    attach_multiday_close_drift,
)
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORITY_FOLDS: tuple[str, ...] = tuple(sorted(ROLLING_FOLDS))
N_AUTHORITY_FOLDS = len(AUTHORITY_FOLDS)
SIGN_MIN_POSITIVE = 5
EXPECTED_EVENTS = 6_000
EXPECTED_SESSIONS = 1_320
# Charter friction-ratio line: ~6 / 400 bps.
MULTIDAY_SIGMA = 0.04


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _fold_slice(panel: pl.DataFrame, fold_id: str) -> pl.DataFrame:
    spec = ROLLING_FOLDS[fold_id]
    lo, hi = parse_period_range(spec.test_period)
    return filter_by_period(panel, lo, hi, datetime_col="date")


def _arrays(sub: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    path = sub["side_drift"].to_numpy().astype(float)
    sess = sub["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    return path, sess


def _print_prereg() -> None:
    plan = declare_admit_power(
        EXPECTED_EVENTS, EXPECTED_SESSIONS, assumed_sigma=MULTIDAY_SIGMA
    )
    print("\n=== S6 PRE-REGISTRATION (before the peek) ===")
    print(f"  rule={PRIMARY_RULE_ID} side=short")
    print(f"  horizons={S6_HORIZONS} authority=T+{S6_AUTHORITY_HORIZON}")
    print(f"  disaster_sl={DISASTER_SL * BPS:.0f}bps clip (not drop)")
    print(f"  folds={','.join(AUTHORITY_FOLDS)} n_folds={N_AUTHORITY_FOLDS} sign>={SIGN_MIN_POSITIVE}")
    print(f"  costs_bps={S6_HAIRCUTS_BPS} authority={S6_HURDLE_BPS}")
    print(
        f"  AdmitPowerPlan n={plan.expected_admit_n} sess={plan.expected_sessions} "
        f"expected_mde={plan.expected_mde_bps:.1f}bps ({plan.note})"
    )
    if plan.expected_mde_bps >= S6_HURDLE_BPS:
        print(
            f"  declared_mde>={S6_HURDLE_BPS:.0f}bps sketch; "
            "realized session-block MDE is the authority after the peek."
        )


def _pooled_verdict(pooled, hurdle_bps: float) -> str:
    mde_bps = pooled.mde * BPS if pooled.mde is not None else float("nan")
    if pooled.passed:
        return "PASS"
    if np.isfinite(mde_bps) and mde_bps >= hurdle_bps:
        return "INCONCLUSIVE"
    return "FAIL"


def _horizon_table(
    events: pl.DataFrame,
    daily: pl.DataFrame,
    horizon: int,
    *,
    n_boot: int,
    seed: int,
    authority: bool,
) -> dict[float, str]:
    tag = "AUTHORITY" if authority else "companion"
    print(f"\n=== S6 {tag} T+{horizon} rule={PRIMARY_RULE_ID} ===")
    panel = attach_multiday_close_drift(
        events.filter(pl.col("rule_id") == PRIMARY_RULE_ID),
        daily,
        horizon_sessions=horizon,
    )
    n_clipped = int((panel["side_drift"] == -DISASTER_SL).sum()) if panel.height else 0
    n_raw_floor = (
        int((panel["side_drift_raw"] < -DISASTER_SL).sum()) if panel.height else 0
    )
    print(
        f"   rows={panel.height} disaster_clip rows_at_floor={n_clipped} "
        f"(raw_below_floor={n_raw_floor}; those are clipped, not dropped)"
    )
    fold_points: dict[float, dict[str, float]] = {bps: {} for bps in S6_HAIRCUTS_BPS}
    ev_parts: dict[float, list[np.ndarray]] = {bps: [] for bps in S6_HAIRCUTS_BPS}
    sess_parts: dict[float, list[np.ndarray]] = {bps: [] for bps in S6_HAIRCUTS_BPS}
    for fold_id in AUTHORITY_FOLDS:
        sub = _fold_slice(panel, fold_id)
        path, sess = _arrays(sub)
        m = np.isfinite(path)
        print(f"   {fold_id} n={int(m.sum())} sess={int(np.unique(sess[m]).size) if m.any() else 0}")
        for bps in S6_HAIRCUTS_BPS:
            ev = path_ev_net(path, bps / BPS)
            k5 = k5_economics(ev[m], sess[m], fold=fold_id, n_boot=n_boot, seed=seed)
            print(f"      c={bps:.0f}bps {k5.note}")
            if np.isfinite(k5.value):
                fold_points[bps][fold_id] = k5.value
                ev_parts[bps].append(ev[m])
                sess_parts[bps].append(sess[m])
    ladder: dict[float, str] = {}
    for bps in S6_HAIRCUTS_BPS:
        parts = ev_parts[bps]
        if len(parts) < N_AUTHORITY_FOLDS:
            print(f"   k5_pooled c={bps:.0f}bps thin - not enough folds with finite points")
            ladder[bps] = "INCONCLUSIVE"
            continue
        pooled = k5_pooled(
            fold_points[bps],
            np.concatenate(parts),
            np.concatenate(sess_parts[bps]),
            n_boot=n_boot,
            seed=seed,
            min_positive=SIGN_MIN_POSITIVE,
            min_folds=N_AUTHORITY_FOLDS,
        )
        verdict = _pooled_verdict(pooled, bps)
        ladder[bps] = verdict
        print(f"   k5_pooled c={bps:.0f}bps {pooled.note}")
        print(f"   S6 verdict T+{horizon} c={bps:.0f}bps={verdict}")
    return ladder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    print(
        "Successor S6 multi-day fade - close-to-close T+1..T+5. "
        "Charter: docs/next/horizon-successor-s6-multiday-fade-charter.md"
    )
    _print_prereg()

    stock, _nifty, _sector, daily_stock, _daily_nifty = load_horizon_data(
        data_dir=args.data_dir,
        config_path=args.config,
        start_period="2015",
        end_period="2023",
    )
    stock = _select_symbols(stock, args.max_symbols)
    daily_stock = _select_symbols(daily_stock, args.max_symbols)
    print(f"   stock rows={stock.height} symbols={stock['symbol'].n_unique()}")
    print(f"   daily rows={daily_stock.height}")

    events = transition_candidate_events(build_candidate_event_panel(stock))
    events = events.filter(pl.col("rule_id") == PRIMARY_RULE_ID)
    print(f"   transition events {PRIMARY_RULE_ID}={events.height}")

    ladders: dict[int, dict[float, str]] = {}
    for horizon in S6_HORIZONS:
        ladders[horizon] = _horizon_table(
            events,
            daily_stock,
            horizon,
            n_boot=args.n_boot,
            seed=args.seed,
            authority=horizon == S6_AUTHORITY_HORIZON,
        )

    c6 = ladders.get(S6_AUTHORITY_HORIZON, {}).get(S6_HURDLE_BPS, "INCONCLUSIVE")
    print(f"\nS6 authority T+{S6_AUTHORITY_HORIZON} c={S6_HURDLE_BPS:.0f}bps={c6}")
    if c6 == "PASS":
        print("S6 PASS - F&O eligibility / lot panel is earned, not started.")
        sys.exit(0)
    if c6 == "INCONCLUSIVE":
        print("S6 INCONCLUSIVE - MDE vs 6 bps. Repair power; do not buy SSF.")
        sys.exit(3)
    print("S6 FAIL - no friction-ratio escape for this signal. Do not download SSF.")
    sys.exit(2)


if __name__ == "__main__":
    main()
