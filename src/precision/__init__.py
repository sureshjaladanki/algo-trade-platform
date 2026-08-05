"""Tier 3 Precision — rules-first 1m timing on the Horizon registry."""

from .rules import (
    LONG_FEATURES,
    SHORT_FEATURES,
    build_decision_registry,
    run_precision_rules,
    size_mult_from_rank,
    summarize_precision_trades,
)
from .session import (
    AFTERNOON_COVER_START,
    DECISION_BAR_MINUTES,
    HORIZON_MINUTES,
    TOP_K,
    WAIT_MINUTES,
)

__all__ = [
    "LONG_FEATURES",
    "SHORT_FEATURES",
    "build_decision_registry",
    "run_precision_rules",
    "size_mult_from_rank",
    "summarize_precision_trades",
    "AFTERNOON_COVER_START",
    "DECISION_BAR_MINUTES",
    "HORIZON_MINUTES",
    "TOP_K",
    "WAIT_MINUTES",
]
