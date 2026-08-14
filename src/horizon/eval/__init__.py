"""Tier 2 Horizon eval harness — see docs/horizon-tier2-eval-verdict.md."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.horizon.eval.bar_stats import per_bar_topk_stats
from src.horizon.eval.constants import N_BOOT, MetricResult, format_report, k_for
from src.horizon.eval.diagnostics import (
    adv_tercile_topk_diagnostics,
    h4_archive_cost_netted_spread,
    h4_cost_netted_spread,
    h6_coverage,
    h7_hygiene_diagnostics,
    h9_calibration_diagnostics,
    h9_k_sweep,
)
from src.horizon.eval.gates import (
    h1_spearman_ic,
    h2_topk_spread,
    h3_rank_monotonicity,
    h5_stock_tb_bridge,
    h10_null_leakage,
    universe_parity_precondition,
)
from src.horizon.eval.long_eval import l1_activation_note, l2_emission_diagnostics
from src.horizon.eval.panel import annotate_hygiene_flags, prepare_eval_panel
from src.horizon.eval.short_eval import s1_activation_note, s2_tod_diagnostics

__all__ = [
    "N_BOOT",
    "MetricResult",
    "annotate_hygiene_flags",
    "evaluate_direction",
    "evaluate_horizon",
    "format_report",
    "k_for",
]


def evaluate_direction(
    scored: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """Run precondition → H1 → H3 → H2 → H5 (+ diagnostics) for one sleeve."""
    panel = prepare_eval_panel(scored, direction)
    metrics: list[MetricResult] = [
        universe_parity_precondition(panel, direction),
        h10_null_leakage(panel, direction, n_boot, rng),
        h6_coverage(panel, direction),
        s1_activation_note(scored, panel, direction),
        l1_activation_note(direction, panel),
    ]
    metrics.extend(h7_hygiene_diagnostics(panel, direction))

    preconds_ok = all(m.gate_pass for m in metrics if m.name in ("universe", "H10"))
    if not preconds_ok or panel.height == 0:
        for name in ("H1", "H3", "H2", "H5"):
            metrics.append(
                MetricResult(
                    name,
                    direction,
                    None,
                    None,
                    None,
                    panel.height,
                    False,
                    "precondition-fail",
                )
            )
        return metrics

    metrics.append(h1_spearman_ic(panel, direction, n_boot, rng))

    bar_stats = per_bar_topk_stats(panel, k_for(direction))
    metrics.append(h3_rank_monotonicity(bar_stats, direction, n_boot, rng))
    metrics.append(h2_topk_spread(bar_stats, direction, n_boot, rng))
    metrics.append(h4_cost_netted_spread(bar_stats, direction))
    metrics.append(h4_archive_cost_netted_spread(bar_stats, direction))
    metrics.extend(h5_stock_tb_bridge(bar_stats, direction, n_boot, rng))
    metrics.extend(adv_tercile_topk_diagnostics(panel, direction))
    metrics.extend(h9_calibration_diagnostics(panel, direction))
    metrics.extend(h9_k_sweep(panel, direction))
    metrics.extend(s2_tod_diagnostics(panel, direction))
    metrics.extend(l2_emission_diagnostics(panel, direction))
    return metrics


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
