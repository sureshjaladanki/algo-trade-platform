"""Tier 2 Horizon eval constants — shared primitives live in ``src.utils.eval_common``."""

from __future__ import annotations

from src.utils.eval_common import (
    H_BARS,
    MIN_BARS,
    MIN_SESSIONS,
    N_BOOT,
    MetricResult,
    format_report,
    session_block_mean_ci,
)

# Locked K (docs/horizon-tier2-eval-verdict.md) — Long matches Precision TOP_K.
K_LONG = 5
K_SHORT = 3

MIN_BARS_LONG = MIN_BARS
MIN_BARS_SHORT = 150
MIN_NAMES_PER_BAR = 5

# Null IC must not show spurious positive skill (H10).
H10_NULL_ABS_MAX = 0.02


def min_bars_for(direction: str) -> int:
    return MIN_BARS_LONG if direction == "long" else MIN_BARS_SHORT


def k_for(direction: str) -> int:
    return K_LONG if direction == "long" else K_SHORT


def side_sign(direction: str) -> float:
    return 1.0 if direction == "long" else -1.0


__all__ = [
    "H_BARS",
    "N_BOOT",
    "MIN_SESSIONS",
    "MIN_BARS",
    "MIN_BARS_LONG",
    "MIN_BARS_SHORT",
    "MIN_NAMES_PER_BAR",
    "H10_NULL_ABS_MAX",
    "K_LONG",
    "K_SHORT",
    "MetricResult",
    "format_report",
    "session_block_mean_ci",
    "min_bars_for",
    "k_for",
    "side_sign",
]
