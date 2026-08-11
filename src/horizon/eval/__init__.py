"""Tier 2 Horizon eval harness — see docs/horizon-tier2-eval-verdict.md."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.horizon.eval.common import N_BOOT, MetricResult, format_report, k_for
from src.horizon.eval.metrics import evaluate_direction

__all__ = [
    "N_BOOT",
    "MetricResult",
    "evaluate_horizon",
    "format_report",
    "k_for",
]


def evaluate_horizon(
    scored: pl.DataFrame,
    directions: list[str],
    n_boot: int,
    seed: int,
) -> list[MetricResult]:
    """
    Run Horizon eval on a scored holdout panel.

    ``scored`` must carry horizon_score, fwd_excess_ret, cascade regimes,
    valid_label_*, and tb_label_* (from build_horizon_features + predict).
    Gates are Long/Short separate — never pooled.
    """
    rng = np.random.default_rng(seed)
    metrics: list[MetricResult] = []
    for direction in directions:
        metrics.extend(evaluate_direction(scored, direction, n_boot, rng))
    return metrics
