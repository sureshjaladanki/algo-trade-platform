"""Pre-registered K1–K5 gates for fresh Horizon (do not overload H1–H5 ship language)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
from scipy import stats

from src.horizon.fresh.friction import ARCHIVE_C_STAR, BPS, C_STAR, K2_MIN_MOVE
from src.utils.eval_common import N_BOOT, session_block_mean_ci

K1_SPEARMAN_MIN = 0.45
K3_CALIB_TOL_PP = 3.0  # ±3 percentage points
K5_MIN_TRADES = 150
K5_MIN_SESSIONS = 40
# Gross dispersion sketch at 200/100 for admit-power pre-declaration (bps → frac).
DEFAULT_GROSS_SIGMA = 0.0137


class K4Verdict(str, Enum):
    """Blueprint §10.3 three-way K4 decision (pre-registered M5P)."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class GateResult:
    gate: str
    fold: str
    value: float
    threshold: float
    passed: bool
    note: str = ""
    mde: float | None = None
    ci_lo: float | None = None
    ci_hi: float | None = None
    verdict: str | None = None


def mde_from_ci(lo: float, hi: float) -> float:
    """Minimum detectable effect = half-width of the session-block CI."""
    return (hi - lo) / 2.0


def k4_three_way(
    point: float,
    lo: float,
    hi: float,
    *,
    c_star: float = C_STAR,
) -> K4Verdict:
    """
    Pre-registered K4 decision rule (blueprint §10.3 / M5P).

    PASS if CI LB > 0; FAIL if CI UB < c*; otherwise INCONCLUSIVE.
    """
    if lo > 0.0:
        return K4Verdict.PASS
    if hi < c_star:
        return K4Verdict.FAIL
    return K4Verdict.INCONCLUSIVE


def k1_range_spearman(
    pred: np.ndarray,
    realized: np.ndarray,
    *,
    fold: str,
) -> GateResult:
    """K1: OOS Spearman(pred, realized remaining range) ≥ 0.45."""
    mask = np.isfinite(pred) & np.isfinite(realized)
    if mask.sum() < 30:
        return GateResult("K1", fold, float("nan"), K1_SPEARMAN_MIN, False, "thin")
    rho, _ = stats.spearmanr(pred[mask], realized[mask])
    rho_f = float(rho)
    return GateResult(
        "K1", fold, rho_f, K1_SPEARMAN_MIN, rho_f >= K1_SPEARMAN_MIN, "spearman"
    )


def k2_post_gate_move(
    abs_moves: np.ndarray,
    session_ids: np.ndarray,
    *,
    fold: str,
    n_boot: int = N_BOOT,
    seed: int = 0,
) -> GateResult:
    """K2: post-gate mean |move| ≥ 8c (session-block CI point)."""
    mask = np.isfinite(abs_moves)
    if mask.sum() < 30:
        return GateResult("K2", fold, float("nan"), K2_MIN_MOVE, False, "thin")
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(
        abs_moves[mask], session_ids[mask], n_boot, rng
    )
    mde = mde_from_ci(lo, hi)
    return GateResult(
        "K2",
        fold,
        point,
        K2_MIN_MOVE,
        point >= K2_MIN_MOVE,
        f"mean_|move| mde={mde * BPS:.1f}bps n={int(mask.sum())} "
        f"sess={int(np.unique(session_ids[mask]).size)}",
        mde=mde,
        ci_lo=lo,
        ci_hi=hi,
    )


def k3_tp_calibration(
    p_tp_hat: np.ndarray,
    hit_tp: np.ndarray,
    *,
    fold: str,
    n_bins: int = 10,
    tol_pp: float = K3_CALIB_TOL_PP,
) -> GateResult:
    """
    K3 (M5 original, report-only): max absolute decile gap in percentage points.

    Superseded by ``k3_calibration_ece`` — a max over 10 bins has a null far
    above zero, so this cannot be compared to a flat 3 pp threshold. Kept so the
    M5 ledger stays reproducible.
    """
    mask = np.isfinite(p_tp_hat) & np.isfinite(hit_tp)
    if mask.sum() < 50:
        return GateResult("K3", fold, float("nan"), tol_pp, False, "thin")
    p = p_tp_hat[mask]
    y = hit_tp[mask].astype(float)
    # Quantile bins on predicted P(TP)
    edges = np.quantile(p, np.linspace(0, 1, n_bins + 1))
    edges[0] -= 1e-9
    edges[-1] += 1e-9
    max_gap_pp = 0.0
    n_used = 0
    for i in range(n_bins):
        in_bin = (p >= edges[i]) & (p < edges[i + 1])
        if in_bin.sum() < 5:
            continue
        gap_pp = abs(float(p[in_bin].mean()) - float(y[in_bin].mean())) * 100.0
        max_gap_pp = max(max_gap_pp, gap_pp)
        n_used += 1
    if n_used < 3:
        return GateResult("K3", fold, float("nan"), tol_pp, False, "thin_bins")
    return GateResult(
        "K3",
        fold,
        max_gap_pp,
        tol_pp,
        max_gap_pp <= tol_pp,
        f"max_|gap|_pp bins={n_used}",
    )


def k3_calibration_ece(
    p_tp_hat: np.ndarray,
    hit_tp: np.ndarray,
    *,
    fold: str,
    n_bins: int = 10,
    tol_pp: float = K3_CALIB_TOL_PP,
    n_boot: int = 200,
    seed: int = 0,
) -> GateResult:
    """
    K3 (corrected): n-weighted ECE ≤ ``tol_pp`` **and** max decile gap ≤ its
    bootstrap null p95 (blueprint §10.3).

    ``k3_tp_calibration`` gated on the **max** absolute decile gap against a flat
    3 pp threshold. A max over 10 bins is not centred on zero: at ~200 rows per
    bin and p≈0.33 the per-bin binomial standard error alone is ~3.3 pp, so a
    perfectly calibrated head fails almost surely. ECE averages instead of
    maximising; the max gap is compared to its own null, not to 3 pp.
    """
    mask = np.isfinite(p_tp_hat) & np.isfinite(hit_tp)
    if mask.sum() < 50:
        return GateResult("K3", fold, float("nan"), tol_pp, False, "thin")
    p = p_tp_hat[mask]
    y = hit_tp[mask].astype(float)
    edges = np.quantile(p, np.linspace(0, 1, n_bins + 1))
    edges[0] -= 1e-9
    edges[-1] += 1e-9

    def _bin_gaps(target: np.ndarray) -> tuple[float, float]:
        """(n-weighted ECE, max gap) in percentage points."""
        total, ece, max_gap = 0, 0.0, 0.0
        for i in range(n_bins):
            in_bin = (p >= edges[i]) & (p < edges[i + 1])
            n_bin = int(in_bin.sum())
            if n_bin < 5:
                continue
            gap = abs(float(p[in_bin].mean()) - float(target[in_bin].mean())) * 100.0
            ece += gap * n_bin
            max_gap = max(max_gap, gap)
            total += n_bin
        return (ece / total if total else float("nan"), max_gap)

    ece, max_gap = _bin_gaps(y)
    # Null band: resample outcomes from the predicted probabilities themselves.
    rng = np.random.default_rng(seed)
    null_max = np.array(
        [_bin_gaps(rng.binomial(1, np.clip(p, 0, 1)).astype(float))[1] for _ in range(n_boot)]
    )
    null_p95 = float(np.percentile(null_max, 95))
    # Blueprint §10.3: ECE ≤ 3 pp AND max decile gap ≤ its own bootstrap null p95.
    ece_ok = ece <= tol_pp
    gap_ok = max_gap <= null_p95
    return GateResult(
        "K3",
        fold,
        ece,
        tol_pp,
        ece_ok and gap_ok,
        f"ECE_pp={ece:.2f} max_gap_pp={max_gap:.2f} null_p95_max={null_p95:.2f}",
    )


def k4_edge_over_driftless(
    hit_tp: np.ndarray,
    sl_w: np.ndarray,
    tp_w: np.ndarray,
    session_ids: np.ndarray,
    *,
    fold: str,
    n_boot: int = N_BOOT,
    seed: int = 0,
    resolved: np.ndarray | None = None,
) -> GateResult:
    """
    K4 companion: realized P(TP) − s/(g+s); session-block CI LB > 0.

    ``s/(g+s)`` is the gambler's-ruin probability for a race with **no** time
    limit. Under an MIS vertical some paths time out, so unconditional P(TP)
    is diluted by roughly ``P(TO) × s/(g+s)`` even for a driftless walk. Pass
    ``resolved`` (label ≠ timeout) to compare P(TP | resolved) instead, which is
    the quantity the formula actually describes.
    """
    span = tp_w + sl_w
    driftless = sl_w / span
    edge = hit_tp.astype(float) - driftless
    mask = np.isfinite(edge) & (span > 0)
    if resolved is not None:
        mask = mask & resolved
    if mask.sum() < 30:
        return GateResult("K4", fold, float("nan"), 0.0, False, "thin")
    rng = np.random.default_rng(seed)
    point, lo, _hi = session_block_mean_ci(edge[mask], session_ids[mask], n_boot, rng)
    scope = "resolved" if resolved is not None else "all"
    return GateResult(
        "K4", fold, point, 0.0, lo > 0.0, f"CI_LB={lo:.4f} scope={scope}"
    )


def k4_martingale_residual(
    path_ret: np.ndarray,
    session_ids: np.ndarray,
    *,
    fold: str,
    n_boot: int = N_BOOT,
    seed: int = 0,
    c_star: float = C_STAR,
) -> GateResult:
    """
    K4 (authority): mean **gross** path return; three-way verdict (M5P).

    Under the driftless null the entry price is a martingale, so optional
    stopping forces ``E[path_ret] = 0`` at any barrier pair and any timeout mass.
    Decision rule (blueprint §10.3): PASS if CI LB > 0; FAIL if CI UB < c*;
    otherwise INCONCLUSIVE. ``passed`` is True only on PASS.
    """
    mask = np.isfinite(path_ret)
    if mask.sum() < 30:
        return GateResult("K4", fold, float("nan"), 0.0, False, "thin")
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(path_ret[mask], session_ids[mask], n_boot, rng)
    mde = mde_from_ci(lo, hi)
    verdict = k4_three_way(point, lo, hi, c_star=c_star)
    n_sess = int(np.unique(session_ids[mask]).size)
    return GateResult(
        "K4",
        fold,
        point,
        0.0,
        verdict == K4Verdict.PASS,
        f"{verdict.value} CI=[{lo * BPS:+.1f},{hi * BPS:+.1f}]bps "
        f"mde={mde * BPS:.1f}bps n={int(mask.sum())} sess={n_sess}",
        mde=mde,
        ci_lo=lo,
        ci_hi=hi,
        verdict=verdict.value,
    )


def k5_economics(
    ev_net: np.ndarray,
    session_ids: np.ndarray,
    *,
    fold: str,
    n_boot: int = N_BOOT,
    seed: int = 0,
    min_trades: int = K5_MIN_TRADES,
    min_sessions: int = K5_MIN_SESSIONS,
) -> GateResult:
    """
    K5 per-fold companion (report-only after Rev 3).

    Authority gate is ``k5_pooled`` — a per-fold CI LB > 0 is arithmetically
    incompatible with a 1–4 fires/day book (blueprint §10.3). Kept so per-fold
    point estimates and MDEs remain printable.
    """
    mask = np.isfinite(ev_net)
    n = int(mask.sum())
    n_sess = int(np.unique(session_ids[mask]).size) if n else 0
    if n < min_trades or n_sess < min_sessions:
        return GateResult(
            "K5",
            fold,
            float("nan"),
            0.0,
            False,
            f"thin n={n} sess={n_sess}",
        )
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(ev_net[mask], session_ids[mask], n_boot, rng)
    mde = mde_from_ci(lo, hi)
    stress_point = point - (ARCHIVE_C_STAR - C_STAR)
    return GateResult(
        "K5",
        fold,
        point,
        0.0,
        False,  # never the authority pass — see k5_pooled
        f"report_only CI=[{lo * BPS:+.1f},{hi * BPS:+.1f}]bps "
        f"stress30={stress_point * BPS:+.1f}bps "
        f"mde={mde * BPS:.1f}bps n={n} sess={n_sess}",
        mde=mde,
        ci_lo=lo,
        ci_hi=hi,
    )


# Fold sign test: positive point estimate in ≥ this many folds (of 8 rolling).
K5_SIGN_MIN_POSITIVE = 6
K5_SIGN_MIN_FOLDS = 8


def k5_pooled(
    fold_points: dict[str, float],
    ev_net: np.ndarray,
    session_ids: np.ndarray,
    *,
    n_boot: int = N_BOOT,
    seed: int = 0,
    min_positive: int = K5_SIGN_MIN_POSITIVE,
    min_folds: int = K5_SIGN_MIN_FOLDS,
) -> GateResult:
    """
    K5 authority (Rev 3): pooled session-block CI LB > 0, **and** fold sign test.

    ``fold_points`` maps fold_id → per-fold mean EV_net (finite only). Pool
    ``ev_net`` / ``session_ids`` across those folds. Flat-c* and c=30 reprints
    are companions the caller publishes alongside; this gate assumes ``ev_net``
    is already computed on the hurdle in use (row-level ``c_eff`` preferred).
    """
    finite_points = {k: v for k, v in fold_points.items() if np.isfinite(v)}
    n_folds = len(finite_points)
    n_pos = sum(1 for v in finite_points.values() if v > 0.0)
    mask = np.isfinite(ev_net)
    n = int(mask.sum())
    n_sess = int(np.unique(session_ids[mask]).size) if n else 0
    if n_folds < min_folds or n < K5_MIN_TRADES or n_sess < K5_MIN_SESSIONS:
        return GateResult(
            "K5",
            "pooled",
            float("nan"),
            0.0,
            False,
            f"thin folds={n_folds}/{min_folds} n={n} sess={n_sess}",
        )
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(ev_net[mask], session_ids[mask], n_boot, rng)
    mde = mde_from_ci(lo, hi)
    sign_ok = n_pos >= min_positive
    pooled_ok = lo > 0.0
    passed = pooled_ok and sign_ok
    return GateResult(
        "K5",
        "pooled",
        point,
        0.0,
        passed,
        f"pooled_LB={'PASS' if pooled_ok else 'FAIL'} "
        f"sign={n_pos}/{n_folds} (need >={min_positive}) "
        f"CI=[{lo * BPS:+.1f},{hi * BPS:+.1f}]bps "
        f"mde={mde * BPS:.1f}bps n={n} sess={n_sess}",
        mde=mde,
        ci_lo=lo,
        ci_hi=hi,
        verdict="PASS" if passed else "FAIL",
    )


@dataclass(frozen=True)
class AdmitPowerPlan:
    """Pre-declared admit mass and the MDE it implies (blueprint §10.3)."""

    expected_admit_n: int
    expected_sessions: int
    assumed_sigma: float
    expected_mde: float
    note: str = ""

    @property
    def expected_mde_bps(self) -> float:
        return self.expected_mde * BPS


def declare_admit_power(
    expected_admit_n: int,
    expected_sessions: int,
    *,
    assumed_sigma: float = DEFAULT_GROSS_SIGMA,
    clustering_factor: float = 1.25,
) -> AdmitPowerPlan:
    """
    State expected admit count **before** a peek; return the implied MDE.

    ``assumed_sigma`` default ≈ 137 bps (200/100 gross dispersion). Session
    clustering inflates SE by ``clustering_factor`` (rough; session-block bootstrap
    is the authority once the run exists).
    """
    if expected_admit_n <= 0 or expected_sessions <= 0:
        return AdmitPowerPlan(
            expected_admit_n=expected_admit_n,
            expected_sessions=expected_sessions,
            assumed_sigma=assumed_sigma,
            expected_mde=float("nan"),
            note="thin_plan",
        )
    # Effective N after clustering: treat sessions as the independent unit when
    # denser than ~one trade per session, else use admit count.
    n_eff = float(min(expected_admit_n, expected_sessions))
    se = clustering_factor * assumed_sigma / np.sqrt(n_eff)
    # Approximate 95% half-width ≈ 1.96 · SE.
    mde = 1.96 * se
    return AdmitPowerPlan(
        expected_admit_n=expected_admit_n,
        expected_sessions=expected_sessions,
        assumed_sigma=assumed_sigma,
        expected_mde=float(mde),
        note=f"n_eff={n_eff:.0f} se={se * BPS:.1f}bps",
    )


def path_ev_net(
    path_ret: np.ndarray,
    cost: float | np.ndarray = C_STAR,
) -> np.ndarray:
    """Realized EV_net = path return − cost (scalar ``c*`` or row-level ``c_eff``)."""
    return np.asarray(path_ret, dtype=float) - np.asarray(cost, dtype=float)
