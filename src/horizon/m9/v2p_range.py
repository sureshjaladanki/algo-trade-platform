"""P1 V2p — range-space selection on Nifty remaining-session residual."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import polars as pl

from src.horizon.fresh.friction import BPS
from src.horizon.fresh.gates import GateResult, k4_three_way, mde_from_ci
from src.regime.intraday import NSE_OPEN_BLEED_BAR
from src.utils.eval_common import N_BOOT, session_block_mean_ci

# Locked in docs/archive/horizon-successor-s1-preregistration.md (V2p-0 ledger).
V2P_RESIDUAL_THRESHOLD = 0.0
# V2p-b: first bar after auction bleed = 09:45, when Stage B open_30m is known.
V2P_POST_OPEN_MIN_TIME = dt.time(9, 45)
# V2p-c: short-premium tercile. Prereg docs/archive/horizon-successor-s1-v2pc-preregistration.md
V2PC_TERCILE = 1.0 / 3.0
V2PC_ABORT_MDE_BPS = 15.0
V2PC_THIN_N = 30
V2PC_THIN_SESSIONS = 20


def _select_at_first_bar(
    panel: pl.DataFrame,
    *,
    min_time: dt.time | None,
) -> pl.DataFrame:
    df = panel.sort("date")
    if min_time is not None:
        tcol = (
            pl.col("time_only")
            if "time_only" in df.columns
            else pl.col("date").dt.time()
        )
        df = df.filter(tcol >= min_time)
    first = df.group_by("date_only", maintain_order=True).first()
    resid = pl.col("range_q50") - pl.col("range_imp_vix")
    return first.filter(resid > V2P_RESIDUAL_THRESHOLD).with_columns(
        residual=resid,
        range_minus_imp=pl.col("remaining_range") - pl.col("range_imp_vix"),
    )


def select_v2p_sessions(panel: pl.DataFrame) -> pl.DataFrame:
    """V2p-0 ledger: first bar of the session. Thin; superseded by post-open."""
    return _select_at_first_bar(panel, min_time=None)


def select_v2p_post_open_sessions(panel: pl.DataFrame) -> pl.DataFrame:
    """
    V2p-b: first bar at or after 09:45 with residual > 0.

    ``NSE_OPEN_BLEED_BAR`` is 09:30; Stage B opening 30m completes at 09:45.
    """
    assert V2P_POST_OPEN_MIN_TIME > NSE_OPEN_BLEED_BAR
    return _select_at_first_bar(panel, min_time=V2P_POST_OPEN_MIN_TIME)


def v2p_session_gate(
    selected: pl.DataFrame,
    *,
    fold: str,
    n_boot: int = N_BOOT,
    seed: int = 0,
) -> GateResult:
    """Cost-free session-block CI on mean(R − R_imp). Three-way vs 0."""
    y = selected["range_minus_imp"].to_numpy().astype(float)
    sess = selected["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    m = np.isfinite(y)
    n = int(m.sum())
    n_sess = int(np.unique(sess[m]).size) if n else 0
    if n < 30 or n_sess < 20:
        return GateResult(
            "V2p",
            fold,
            float("nan"),
            0.0,
            False,
            f"thin n={n} sess={n_sess}",
            verdict="INCONCLUSIVE",
        )
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(y[m], sess[m], n_boot, rng)
    mde = mde_from_ci(lo, hi)
    verdict = k4_three_way(point, lo, hi, c_star=0.0)
    return GateResult(
        "V2p",
        fold,
        point,
        0.0,
        verdict.value == "PASS",
        f"CI=[{lo:+.5f},{hi:+.5f}] mde={mde:.5f} n={n} sess={n_sess}",
        mde=mde,
        ci_lo=lo,
        ci_hi=hi,
        verdict=verdict.value,
    )


def first_post_open_clock(panel: pl.DataFrame) -> pl.DataFrame:
    """One row per session: first bar at or after 09:45. No residual filter."""
    assert V2P_POST_OPEN_MIN_TIME > NSE_OPEN_BLEED_BAR
    df = panel.sort("date")
    tcol = (
        pl.col("time_only")
        if "time_only" in df.columns
        else pl.col("date").dt.time()
    )
    return (
        df.filter(tcol >= V2P_POST_OPEN_MIN_TIME)
        .group_by("date_only", maintain_order=True)
        .first()
    )


@dataclass(frozen=True)
class V2pcScale:
    """Train-locked implied calibration and residual location/scale (V2p-c)."""

    intercept: float
    slope: float
    resid_mean: float
    resid_std: float
    tercile_threshold: float


def fit_v2pc_scale(train_clock: pl.DataFrame) -> V2pcScale:
    """
    Fit ``remaining_range ~ implied`` on train 09:45 bars.

    Selection residual is ``range_q50 − (a + b·implied)`` — the head vs
    calibrated implied, so test selection does not see realized range.
    """
    y = train_clock["remaining_range"].to_numpy().astype(float)
    imp = train_clock["range_imp_vix"].to_numpy().astype(float)
    q50 = train_clock["range_q50"].to_numpy().astype(float)
    m = np.isfinite(y) & np.isfinite(imp) & np.isfinite(q50) & (y > 0) & (imp > 0)
    n = int(m.sum())
    x = np.column_stack([np.ones(n), imp[m]])
    beta, _, _, _ = np.linalg.lstsq(x, y[m], rcond=None)
    calib = beta[0] + beta[1] * imp[m]
    resid = q50[m] - calib
    mu = float(resid.mean())
    sigma = float(resid.std(ddof=1))
    z = (resid - mu) / sigma
    return V2pcScale(
        intercept=float(beta[0]),
        slope=float(beta[1]),
        resid_mean=mu,
        resid_std=sigma,
        tercile_threshold=float(np.quantile(z, V2PC_TERCILE)),
    )


def attach_v2pc_residual(clock: pl.DataFrame, scale: V2pcScale) -> pl.DataFrame:
    """Apply train location/scale. Does not use realized range for the z-score."""
    imp = clock["range_imp_vix"].to_numpy().astype(float)
    q50 = clock["range_q50"].to_numpy().astype(float)
    calib = scale.intercept + scale.slope * imp
    resid = q50 - calib
    z = (resid - scale.resid_mean) / scale.resid_std
    return clock.with_columns(
        range_imp_cal=pl.Series(calib),
        v2pc_residual=pl.Series(resid),
        v2pc_z=pl.Series(z),
    )


def select_v2pc_sessions(clock: pl.DataFrame, scale: V2pcScale) -> pl.DataFrame:
    """Bottom tercile of standardized residual (implied richest vs the head)."""
    return attach_v2pc_residual(clock, scale).filter(
        pl.col("v2pc_z") <= scale.tercile_threshold
    )


def _imp_minus_realized(clock: pl.DataFrame) -> np.ndarray:
    return (
        clock["range_imp_vix"].to_numpy() - clock["remaining_range"].to_numpy()
    ).astype(float)


def v2pc_paired_values(
    selected: pl.DataFrame,
    universe: pl.DataFrame,
) -> np.ndarray:
    """mean(R_imp − R) selected minus the all-session mean (same clock)."""
    mu_all = float(np.nanmean(_imp_minus_realized(universe)))
    return _imp_minus_realized(selected) - mu_all


def v2pc_session_gate(
    selected: pl.DataFrame,
    universe: pl.DataFrame,
    *,
    fold: str,
    n_boot: int = N_BOOT,
    seed: int = 0,
) -> GateResult:
    """
    Cost-free session-block CI on the paired difference.

    PASS if CI LB > 0. FAIL if LB ≤ 0 on a passable (not thin) sample.
    Thin → INCONCLUSIVE; do not record FAIL.
    """
    y = v2pc_paired_values(selected, universe)
    sess = selected["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    m = np.isfinite(y)
    n = int(m.sum())
    n_sess = int(np.unique(sess[m]).size) if n else 0
    if n < V2PC_THIN_N or n_sess < V2PC_THIN_SESSIONS:
        return GateResult(
            "V2p-c",
            fold,
            float("nan"),
            0.0,
            False,
            f"thin n={n} sess={n_sess}",
            verdict="INCONCLUSIVE",
        )
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(y[m], sess[m], n_boot, rng)
    mde = mde_from_ci(lo, hi)
    passed = lo > 0.0
    return GateResult(
        "V2p-c",
        fold,
        point,
        0.0,
        passed,
        f"CI=[{lo * BPS:+.1f},{hi * BPS:+.1f}]bps "
        f"mde={mde * BPS:.1f}bps n={n} sess={n_sess}",
        mde=mde,
        ci_lo=lo,
        ci_hi=hi,
        verdict="PASS" if passed else "FAIL",
    )
