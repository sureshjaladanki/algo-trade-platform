"""Tier 3 Precision eval harness — see docs/precision-tier3-eval-verdict.md."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.precision.eval.constants import N_BOOT, MetricResult, format_report, k_for
from src.precision.eval.diagnostics import diagnostic_metrics
from src.precision.eval.gates import (
    horizon_h5_ci_lb,
    p0_ok,
    p0_preconditions,
    p1_selectivity,
    p2_timing,
    p3_expectancy,
    precondition_blocked,
)
from src.precision.eval.panel import prepare_eval_panel

__all__ = [
    "N_BOOT",
    "MetricResult",
    "evaluate_direction",
    "evaluate_precision",
    "format_report",
    "k_for",
    "prepare_eval_panel",
]


def evaluate_direction(
    trades: pl.DataFrame,
    features_1m: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
    scored: pl.DataFrame | None = None,
) -> list[MetricResult]:
    """Run P0 → P1 → P2 → P3 (+ diagnostics) for one sleeve."""
    gated, raw_sleeve = prepare_eval_panel(trades, features_1m, direction)
    metrics: list[MetricResult] = p0_preconditions(raw_sleeve, gated, direction)
    h5 = horizon_h5_ci_lb(scored, direction, n_boot, rng)
    metrics.append(h5)

    preconds_ok = p0_ok(metrics)
    if not preconds_ok or gated.height == 0:
        for name in ("P1", "P2", "P3"):
            metrics.append(precondition_blocked(name, direction, gated.height))
        metrics.extend(diagnostic_metrics(gated, direction, features_1m, rng))
        return metrics

    metrics.append(p1_selectivity(gated, direction, n_boot, rng))
    metrics.append(p2_timing(gated, direction, n_boot, rng))
    metrics.append(
        p3_expectancy(
            gated, direction, n_boot, rng, h5_unlocked=bool(h5.gate_pass)
        )
    )
    metrics.extend(diagnostic_metrics(gated, direction, features_1m, rng))
    return metrics


def evaluate_precision(
    trades: pl.DataFrame,
    features_1m: pl.DataFrame,
    directions: list[str],
    n_boot: int,
    seed: int,
    scored: pl.DataFrame | None = None,
) -> list[MetricResult]:
    """
    Run Precision eval on a classified episode frame.

    ``trades`` is ``classify_precision`` output (Phase-1 defaults unless ablated).
    ``features_1m`` is the same 1m panel used for fills. ``scored`` is the
    Horizon holdout panel used only for the H5 P3-unlock (never for P1/P2).
    Gates are Long/Short separate — never pooled. Sizing never enters P1–P3.
    """
    rng = np.random.default_rng(seed)
    metrics: list[MetricResult] = []
    for direction in directions:
        metrics.extend(
            evaluate_direction(
                trades, features_1m, direction, n_boot, rng, scored=scored
            )
        )
    return metrics
