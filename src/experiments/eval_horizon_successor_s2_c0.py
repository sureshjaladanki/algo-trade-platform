"""Successor S2 — P2 C0 8-fold fade cost-bound at 3/5/8 bps.

Pre-registration: docs/archive/horizon-successor-s2-c0-preregistration.md
First live caller of k5_pooled. No Stage C. No N-bar exhaustion.

    poetry run python -m src.experiments.eval_horizon_successor_s2_c0
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
from src.horizon.fresh.microstructure import corwin_schultz_spread_bps
from src.horizon.fresh.tradability import attach_tradability_mask
from src.horizon.successor.fade_bound import (
    C0_HAIRCUTS_BPS,
    COMPANION_RULE_IDS,
    DISASTER_SL,
    PRIMARY_RULE_ID,
    attach_clipped_side_drift,
)
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]

AUTHORITY_FOLDS: tuple[str, ...] = tuple(sorted(ROLLING_FOLDS))
N_AUTHORITY_FOLDS = len(AUTHORITY_FOLDS)
# 6 disjoint test years (R2017-R2022). A+B overlap 2018/2019 so they are
# companions, not pooled. Sign analogue of 6/8 is 5/6.
SIGN_MIN_POSITIVE = 5
EXPECTED_EVENTS = 7_500
EXPECTED_SESSIONS = 1_320
VERTICAL_SIGMA = 0.008
C0_HURDLE_BPS = 3.0
# Instrument-change gate (T-01): SSF is earned only if the pre-registered
# c=5 companion still clears pooled K5. C0 at 3 bps is the historical bound.
C0_INSTRUMENT_HURDLE_BPS = 5.0


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _fold_slice(panel: pl.DataFrame, fold_id: str) -> pl.DataFrame:
    spec = ROLLING_FOLDS[fold_id]
    lo, hi = parse_period_range(spec.test_period)
    return filter_by_period(panel, lo, hi, datetime_col="date")


def _arrays(sub: pl.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    path = sub["side_drift"].to_numpy().astype(float)
    sess = sub["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    ceff = (
        sub["c_eff_bps"].to_numpy().astype(float) / BPS
        if "c_eff_bps" in sub.columns
        else np.full(path.shape, np.nan)
    )
    return path, sess, ceff


def _print_prereg() -> None:
    plan = declare_admit_power(
        EXPECTED_EVENTS, EXPECTED_SESSIONS, assumed_sigma=VERTICAL_SIGMA
    )
    print("\n=== C0 PRE-REGISTRATION (before the peek) ===")
    print(f"  rule={PRIMARY_RULE_ID} side=short")
    print(f"  disaster_sl={DISASTER_SL * BPS:.0f}bps clip (not drop)")
    print(f"  folds={','.join(AUTHORITY_FOLDS)} n_folds={N_AUTHORITY_FOLDS} sign>={SIGN_MIN_POSITIVE}")
    print(f"  costs_bps={C0_HAIRCUTS_BPS} authority={C0_HURDLE_BPS}")
    print(
        f"  AdmitPowerPlan n={plan.expected_admit_n} sess={plan.expected_sessions} "
        f"expected_mde={plan.expected_mde_bps:.1f}bps ({plan.note})"
    )
    if plan.expected_mde_bps >= C0_HURDLE_BPS:
        print(
            f"  expected_verdict=INCONCLUSIVE "
            f"(MDE {plan.expected_mde_bps:.1f} >= hurdle {C0_HURDLE_BPS:.0f})"
        )
    else:
        print("  expected_verdict=FAIL more likely than PASS (thin fade vs 3 bps)")


def _pooled_verdict(pooled, hurdle_bps: float) -> str:
    mde_bps = pooled.mde * BPS if pooled.mde is not None else float("nan")
    if pooled.passed:
        return "PASS"
    if np.isfinite(mde_bps) and mde_bps >= hurdle_bps:
        return "INCONCLUSIVE"
    return "FAIL"


def _rule_table(
    panel: pl.DataFrame,
    rule_id: str,
    *,
    n_boot: int,
    seed: int,
    authority: bool,
) -> dict[float, str] | None:
    tag = "AUTHORITY" if authority else "companion"
    print(f"\n=== C0 {tag} rule={rule_id} ===")
    fold_points: dict[float, dict[str, float]] = {bps: {} for bps in C0_HAIRCUTS_BPS}
    ev_parts: dict[float, list[np.ndarray]] = {bps: [] for bps in C0_HAIRCUTS_BPS}
    sess_parts: dict[float, list[np.ndarray]] = {bps: [] for bps in C0_HAIRCUTS_BPS}
    n_dropped_left = 0
    n_clipped = 0
    for fold_id in AUTHORITY_FOLDS:
        sub = _fold_slice(panel, fold_id).filter(pl.col("rule_id") == rule_id)
        raw = sub["side_drift_raw"].to_numpy() if "side_drift_raw" in sub.columns else None
        path, sess, ceff = _arrays(sub)
        m = np.isfinite(path)
        if raw is not None:
            n_dropped_left += int((raw < -DISASTER_SL).sum())
            n_clipped += int((path == -DISASTER_SL).sum())
        print(f"   {fold_id} n={int(m.sum())} sess={int(np.unique(sess[m]).size) if m.any() else 0}")
        for bps in C0_HAIRCUTS_BPS:
            ev = path_ev_net(path, bps / BPS)
            k5 = k5_economics(ev[m], sess[m], fold=fold_id, n_boot=n_boot, seed=seed)
            print(f"      c={bps:.0f}bps {k5.note}")
            if np.isfinite(k5.value):
                fold_points[bps][fold_id] = k5.value
                ev_parts[bps].append(ev[m])
                sess_parts[bps].append(sess[m])
        if m.any() and np.isfinite(ceff[m]).any():
            ev_c = path_ev_net(path, ceff)
            k5c = k5_economics(
                ev_c[m], sess[m], fold=fold_id, n_boot=n_boot, seed=seed
            )
            print(f"      c_eff companion {k5c.note}")

    print(
        f"   disaster_clip: rows_at_floor={n_clipped} "
        f"(raw_below_floor={n_dropped_left}; those are clipped, not dropped)"
    )
    if not authority:
        return None
    ladder: dict[float, str] = {}
    for bps in C0_HAIRCUTS_BPS:
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
        print(f"   C0 verdict c={bps:.0f}bps={verdict}")
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
        "Successor S2 C0 - 8-fold fade haircut. "
        "Prereg: docs/archive/horizon-successor-s2-c0-preregistration.md"
    )
    _print_prereg()

    stock, *_ = load_horizon_data(
        data_dir=args.data_dir,
        config_path=args.config,
        start_period="2015",
        end_period="2022",
    )
    stock = _select_symbols(stock, args.max_symbols)
    print(f"   stock rows={stock.height} symbols={stock['symbol'].n_unique()}")

    events = transition_candidate_events(build_candidate_event_panel(stock))
    print(f"   transition events={events.height}")
    drifted = attach_clipped_side_drift(events, stock)
    drifted = drifted.with_columns(
        side_drift_raw=pl.when(pl.col("side") == "long")
        .then(pl.col("fwd_long"))
        .otherwise(-pl.col("fwd_long"))
    )
    # c_eff companion on event bars.
    panel = attach_tradability_mask(
        corwin_schultz_spread_bps(
            drifted.join(
                stock.select(["symbol", "date", "open", "high", "low", "close", "volume"]),
                on=["symbol", "date"],
                how="left",
            )
        )
    )
    panel = panel.filter(pl.col("side_drift").is_finite())
    print(f"   drifted rows={panel.height} (no left-tail drop)")

    ladder = _rule_table(
        panel,
        PRIMARY_RULE_ID,
        n_boot=args.n_boot,
        seed=args.seed,
        authority=True,
    )
    for rid in COMPANION_RULE_IDS:
        _rule_table(
            panel, rid, n_boot=args.n_boot, seed=args.seed, authority=False
        )

    c3 = ladder[C0_HURDLE_BPS] if ladder else "INCONCLUSIVE"
    c5 = ladder.get(C0_INSTRUMENT_HURDLE_BPS, "INCONCLUSIVE") if ladder else "INCONCLUSIVE"
    print(f"\nC0 historical c={C0_HURDLE_BPS:.0f}bps={c3}")
    print(
        f"P2 instrument gate c={C0_INSTRUMENT_HURDLE_BPS:.0f}bps={c5} "
        f"(SSF earned only on PASS)"
    )
    if c5 == "PASS":
        print("C0 ladder PASS at 5 bps - SSF earned only if forward RT floor < c_max.")
        sys.exit(0)
    if c5 == "INCONCLUSIVE":
        print("C0 ladder INCONCLUSIVE at 5 bps. Do not download SSF.")
        sys.exit(3)
    print("C0 ladder FAIL at 5 bps - P2 STOP. Do not download SSF.")
    sys.exit(2)


if __name__ == "__main__":
    main()
