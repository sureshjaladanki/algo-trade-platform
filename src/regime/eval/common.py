"""Tier 1 Regime eval constants — shared primitives live in ``src.utils.eval_common``."""

from __future__ import annotations

from src.regime.types import DailyRegime
from src.utils.eval_common import (
    H_BARS,
    MIN_BARS,
    MIN_SESSIONS,
    N_BOOT,
    MetricResult,
    bootstrap_ci,
    format_report,
)

D2_ORDER = (
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
    DailyRegime.HOSTILE.value,
)
TRADEABLE_DAILY = (
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
)

__all__ = [
    "H_BARS",
    "MIN_BARS",
    "MIN_SESSIONS",
    "N_BOOT",
    "D2_ORDER",
    "TRADEABLE_DAILY",
    "MetricResult",
    "bootstrap_ci",
    "format_report",
]
