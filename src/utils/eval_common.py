"""Shared eval harness primitives for Tier 1 / Tier 2 gate reports."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

H_BARS = 4
N_BOOT = 500
MIN_SESSIONS = 30
MIN_BARS = 100


@dataclass(frozen=True)
class MetricResult:
    name: str
    side: str
    value: float | None
    ci_low: float | None
    ci_high: float | None
    n: int
    gate_pass: bool | None
    note: str = ""


def bootstrap_ci(
    values: np.ndarray,
    n_boot: int,
    rng: np.random.Generator,
) -> tuple[float, float, float]:
    """Point mean + 95% CI from iid with-replacement draws over ``values``."""
    point = float(values.mean())
    draws = rng.choice(values, size=(n_boot, values.size), replace=True).mean(axis=1)
    return point, float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def session_block_mean_ci(
    values: np.ndarray,
    session_ids: np.ndarray,
    n_boot: int,
    rng: np.random.Generator,
) -> tuple[float, float, float]:
    """
    Bar-weighted mean with session-block bootstrap 95% CI.

    Resamples sessions with replacement; concatenates all bars from each drawn
    session (duplicates count when a session is redrawn).
    """
    point = float(values.mean())
    sessions = np.unique(session_ids)
    sess_to_idx = {int(s): np.flatnonzero(session_ids == s) for s in sessions}
    boot = np.empty(n_boot)
    for b in range(n_boot):
        drawn = rng.choice(sessions, size=sessions.size, replace=True)
        idxs = np.concatenate([sess_to_idx[int(s)] for s in drawn])
        boot[b] = float(values[idxs].mean()) if idxs.size else point
    return point, float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def format_report(metrics: list[MetricResult], title: str) -> str:
    side_w = max((len(m.side) for m in metrics), default=10)
    side_w = max(side_w, 10)
    lines = [title, "=" * len(title)]
    header = (
        f"{'metric':<14} {'side':<{side_w}} {'value':>10} "
        f"{'ci_lo':>10} {'ci_hi':>10} {'n':>7} {'gate':>6}  note"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for m in metrics:
        val = (
            f"{m.value:10.4f}"
            if m.value is not None and np.isfinite(m.value)
            else f"{'-':>10}"
        )
        lo = (
            f"{m.ci_low:10.4f}"
            if m.ci_low is not None and np.isfinite(m.ci_low)
            else f"{'-':>10}"
        )
        hi = (
            f"{m.ci_high:10.4f}"
            if m.ci_high is not None and np.isfinite(m.ci_high)
            else f"{'-':>10}"
        )
        gate = {True: "PASS", False: "FAIL"}.get(m.gate_pass, "-")
        lines.append(
            f"{m.name:<14} {m.side:<{side_w}} {val} {lo} {hi} {m.n:7d} {gate:>6}  {m.note}"
        )
    return "\n".join(lines)
