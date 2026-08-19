"""Pooled session-block CI, MDE, disaster clip, three-way verdict."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.events.constants import (
    DISASTER_CLIP_BPS,
    MIN_FOLD_EVENTS,
    N_BOOT,
)

# 80% power, 5% two-sided.
_Z_ALPHA = 1.959963984540
_Z_BETA = 0.841621233573


@dataclass(frozen=True)
class Interval:
    point: float
    ci_low: float
    ci_high: float
    n: int
    n_sessions: int


def clip_disaster(
    values: np.ndarray,
    floor_bps: float = -DISASTER_CLIP_BPS,
) -> np.ndarray:
    """Clip losses at a wide floor and keep every row."""
    return np.maximum(values, floor_bps)


def mde_bps(sigma_bps: float, n: int) -> float:
    """Minimum detectable effect at 80% power, 5% two-sided."""
    if n <= 0:
        raise ValueError("n must be positive to compute MDE")
    return (_Z_ALPHA + _Z_BETA) * sigma_bps / float(np.sqrt(n))


def session_block_mean_ci(
    values: np.ndarray,
    session_ids: np.ndarray,
    n_boot: int = N_BOOT,
    rng: np.random.Generator | None = None,
) -> Interval:
    """Bar-weighted mean with session-block bootstrap 95% CI (inherited)."""
    if rng is None:
        rng = np.random.default_rng()
    point = float(values.mean())
    sessions = np.unique(session_ids)
    sess_to_idx = {s: np.flatnonzero(session_ids == s) for s in sessions}
    boot = np.empty(n_boot)
    for b in range(n_boot):
        drawn = rng.choice(sessions, size=sessions.size, replace=True)
        idxs = np.concatenate([sess_to_idx[s] for s in drawn])
        boot[b] = float(values[idxs].mean()) if idxs.size else point
    return Interval(
        point=point,
        ci_low=float(np.quantile(boot, 0.025)),
        ci_high=float(np.quantile(boot, 0.975)),
        n=int(values.size),
        n_sessions=int(sessions.size),
    )


def fold_sign_pass(
    fold_means: dict[str, float],
    fold_counts: dict[str, int],
    *,
    min_events: int = MIN_FOLD_EVENTS,
) -> tuple[bool, int, int]:
    """Point estimate positive on a majority of folds with enough events."""
    eligible = [k for k, n in fold_counts.items() if n >= min_events]
    n_pos = sum(1 for k in eligible if fold_means[k] > 0)
    n_eligible = len(eligible)
    if n_eligible == 0:
        return False, 0, 0
    return n_pos > n_eligible / 2.0, n_pos, n_eligible


def three_way_verdict(
    interval: Interval,
    mde: float,
    *,
    sign_ok: bool,
    hurdle: float = 0.0,
) -> str:
    """PASS / FAIL / INCONCLUSIVE. INCONCLUSIVE is not a pass."""
    effect = abs(interval.point)
    if mde >= effect:
        return "INCONCLUSIVE"
    if interval.ci_high < hurdle:
        return "FAIL"
    if interval.ci_low > hurdle and sign_ok:
        return "PASS"
    return "INCONCLUSIVE"
