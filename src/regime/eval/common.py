"""Shared types / constants for Tier 1 Regime eval."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.regime.types import DailyRegime

H_BARS = 4
MIN_SESSIONS = 30
MIN_BARS = 100
N_BOOT = 500

D2_ORDER = (
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
    DailyRegime.HOSTILE.value,
)
TRADEABLE_DAILY = (
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
)


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
    """Point mean + 95% CI from with-replacement block draws."""
    point = float(values.mean())
    draws = rng.choice(values, size=(n_boot, values.size), replace=True).mean(axis=1)
    return point, float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def format_report(metrics: list[MetricResult], title: str) -> str:
    lines = [title, "=" * len(title)]
    header = (
        f"{'metric':<14} {'side':<28} {'value':>10} "
        f"{'ci_lo':>10} {'ci_hi':>10} {'n':>7} {'gate':>6}  note"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for m in metrics:
        val = f"{m.value:10.4f}" if m.value is not None and np.isfinite(m.value) else f"{'-':>10}"
        lo = f"{m.ci_low:10.4f}" if m.ci_low is not None and np.isfinite(m.ci_low) else f"{'-':>10}"
        hi = f"{m.ci_high:10.4f}" if m.ci_high is not None and np.isfinite(m.ci_high) else f"{'-':>10}"
        gate = {True: "PASS", False: "FAIL"}.get(m.gate_pass, "-")
        lines.append(
            f"{m.name:<14} {m.side:<28} {val} {lo} {hi} {m.n:7d} {gate:>6}  {m.note}"
        )
    return "\n".join(lines)
