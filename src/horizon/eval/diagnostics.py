"""Tier 2 Horizon eval — report-only diagnostics (H4, H6–H7, H9, ADV)."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.horizon.eval.bar_stats import _mean_or_nan, per_bar_topk_stats
from src.horizon.eval.constants import (
    CIRCUIT_RANGE_EPS,
    H_BARS,
    K_SWEEP,
    MIN_NAMES_PER_BAR,
    MetricResult,
    k_for,
)
from src.labels.triple_barrier import ARCHIVE_ROUND_TRIP_COST, ROUND_TRIP_COST


def h4_cost_netted_spread(bar_stats: pl.DataFrame, direction: str) -> MetricResult:
    """Diagnostic companion: Top-K cost-netted vs Rest (flat ROUND_TRIP_COST)."""
    n = bar_stats.height
    if n == 0:
        return MetricResult("H4", direction, None, None, None, 0, None, "empty")
    point = float(bar_stats["cost_spread"].mean())
    return MetricResult(
        "H4",
        direction,
        point,
        None,
        None,
        n,
        None,
        f"c={ROUND_TRIP_COST:.4f}",
    )


def h4_archive_cost_netted_spread(
    bar_stats: pl.DataFrame, direction: str
) -> MetricResult:
    """Report-only: same H4 haircut at ARCHIVE_ROUND_TRIP_COST (30 bps stress)."""
    n = bar_stats.height
    if n == 0:
        return MetricResult("H4arch", direction, None, None, None, 0, None, "empty")
    point = float(bar_stats["archive_cost_spread"].mean())
    return MetricResult(
        "H4arch",
        direction,
        point,
        None,
        None,
        n,
        None,
        f"c={ARCHIVE_ROUND_TRIP_COST:.4f} report-only",
    )


def adv_tercile_topk_diagnostics(
    panel: pl.DataFrame, direction: str
) -> list[MetricResult]:
    """
    Report-only ADV/liquidity tercile of Top-K TB+1 and working-c H4.

    Uses causal ``adv_rank_20d`` (0–1 XS percentile; higher = more liquid).
    Same harness invocation — not a tiered ``c`` and not an extra peek.
    """
    k = k_for(direction)
    if "adv_rank_20d" not in panel.columns or panel.height == 0:
        return [
            MetricResult(
                "ADVt",
                direction,
                None,
                None,
                None,
                0,
                None,
                "missing adv_rank_20d",
            )
        ]

    top = panel.filter(
        (pl.col("eval_rank") <= k) & pl.col("adv_rank_20d").is_finite()
    )
    if top.height == 0:
        return [
            MetricResult(
                "ADVt", direction, None, None, None, 0, None, "empty Top-K"
            )
        ]

    # Terciles on universe rank: lo=thin tail, mid, hi=liquid.
    buckets = (
        top.with_columns(
            adv_bucket=pl.when(pl.col("adv_rank_20d") <= 1.0 / 3.0)
            .then(pl.lit("lo"))
            .when(pl.col("adv_rank_20d") <= 2.0 / 3.0)
            .then(pl.lit("mid"))
            .otherwise(pl.lit("hi"))
        )
        .group_by("adv_bucket")
        .agg(
            n=pl.len(),
            p_tb=(pl.col("tb_label") == 1).mean(),
            mean_net=pl.col("adj_excess").mean() - ROUND_TRIP_COST,
        )
        .sort("adv_bucket")
    )

    share = {
        row["adv_bucket"]: row["n"] / top.height for row in buckets.iter_rows(named=True)
    }
    p_tb = {
        row["adv_bucket"]: row["p_tb"] for row in buckets.iter_rows(named=True)
    }
    mean_net = {
        row["adv_bucket"]: row["mean_net"] for row in buckets.iter_rows(named=True)
    }
    note = (
        f"share lo/mid/hi="
        f"{share.get('lo', 0):.2f}/{share.get('mid', 0):.2f}/{share.get('hi', 0):.2f} "
        f"TB+1={p_tb.get('lo', float('nan')):.3f}/"
        f"{p_tb.get('mid', float('nan')):.3f}/"
        f"{p_tb.get('hi', float('nan')):.3f} "
        f"net@c*={mean_net.get('lo', float('nan')):.4f}/"
        f"{mean_net.get('mid', float('nan')):.4f}/"
        f"{mean_net.get('hi', float('nan')):.4f}"
    )
    # Point = Top-K mass in thin (lo) tercile — stress exposure under single c*.
    return [
        MetricResult(
            "ADVt",
            direction,
            float(share.get("lo", 0.0)),
            None,
            None,
            int(top.height),
            None,
            note,
        )
    ]


def h6_coverage(panel: pl.DataFrame, direction: str) -> MetricResult:
    """Eligible-name counts / scarcity diagnostic."""
    if panel.height == 0:
        return MetricResult("H6", direction, None, None, None, 0, None, "empty")
    per_bar = panel.group_by("date").agg(n=pl.len())
    median_n = float(per_bar["n"].median())
    n_sessions = panel.select(pl.col("date_only").n_unique()).item()
    n_bars = per_bar.height
    k = k_for(direction)
    thin = int((per_bar["n"] < 15).sum())
    return MetricResult(
        "H6",
        direction,
        median_n,
        None,
        None,
        int(panel.height),
        None,
        f"sess={n_sessions} bars={n_bars} K={k} thin<15={thin}",
    )


def h7_hygiene_diagnostics(
    panel: pl.DataFrame,
    direction: str,
) -> list[MetricResult]:
    """
    H7: F&O list status, circuit / expiry coverage, Short path slices.

    Report-only — never gates ship. F&O membership list is absent this cycle.
    """
    from src.horizon.eval.short_eval import h7_path_slice_diagnostics

    results: list[MetricResult] = []
    n = panel.height

    if direction == "short":
        results.append(
            MetricResult(
                "H7fnc",
                direction,
                None,
                None,
                None,
                n,
                None,
                "fno_list=absent",
            )
        )
    else:
        results.append(
            MetricResult("H7fnc", direction, None, None, None, n, None, "n/a")
        )

    if n == 0 or "is_circuit_bar" not in panel.columns:
        results.append(
            MetricResult("H7cir", direction, None, None, None, n, None, "empty")
        )
        results.append(
            MetricResult("H7exp", direction, None, None, None, n, None, "empty")
        )
        return results

    k = k_for(direction)
    pct_bar = float(panel["is_circuit_bar"].mean())
    pct_fwd = float(panel["fwd_circuit_hit"].mean())
    topk = panel.filter(pl.col("eval_rank") <= k)
    pct_topk_bar = float(topk["is_circuit_bar"].mean()) if topk.height else 0.0
    pct_topk_fwd = float(topk["fwd_circuit_hit"].mean()) if topk.height else 0.0
    results.append(
        MetricResult(
            "H7cir",
            direction,
            pct_fwd,
            None,
            None,
            n,
            None,
            (
                f"bar={pct_bar:.4f} fwd={pct_fwd:.4f} "
                f"topk_bar={pct_topk_bar:.4f} topk_fwd={pct_topk_fwd:.4f} "
                f"eps={CIRCUIT_RANGE_EPS} H={H_BARS}"
            ),
        )
    )

    n_exp_rows = int(panel.filter(pl.col("is_expiry_day")).height)
    n_exp_sess = panel.filter(pl.col("is_expiry_day")).select(
        pl.col("date_only").n_unique()
    ).item()
    n_sess = panel.select(pl.col("date_only").n_unique()).item()
    pct_exp = n_exp_rows / n if n else 0.0
    results.append(
        MetricResult(
            "H7exp",
            direction,
            pct_exp,
            None,
            None,
            n,
            None,
            f"exp_rows={n_exp_rows} exp_sess={n_exp_sess}/{n_sess} weekday=Thu",
        )
    )

    results.extend(h7_path_slice_diagnostics(panel, direction))
    return results


def h9_calibration_diagnostics(panel: pl.DataFrame, direction: str) -> list[MetricResult]:
    """
    H9: top-vs-bottom adj_excess separation + TB+1 by score quintile.

    Report-only. Top/bottom = highest/lowest 20% of eval_score within each bar.
    """
    results: list[MetricResult] = []
    if panel.height == 0:
        return [
            MetricResult("H9sep", direction, None, None, None, 0, None, "empty"),
            MetricResult("H9cal", direction, None, None, None, 0, None, "empty"),
        ]

    sep_rows: list[float] = []
    q_tb: dict[int, list[float]] = {q: [] for q in range(1, 6)}

    for (_,), g in panel.group_by("date", maintain_order=True):
        n = g.height
        if n < MIN_NAMES_PER_BAR:
            continue
        # Quintile on eval_score (5 ≈ best). Need enough names for top/bottom 20%.
        n_tail = max(1, n // 5)
        ranked = g.sort("eval_score", descending=True)
        top = ranked.head(n_tail)
        bot = ranked.tail(n_tail)
        top_m = _mean_or_nan(top["adj_excess"])
        bot_m = _mean_or_nan(bot["adj_excess"])
        if np.isfinite(top_m) and np.isfinite(bot_m):
            sep_rows.append(top_m - bot_m)

        with_q = g.with_columns(
            score_q=pl.col("eval_score")
            .qcut(5, labels=["1", "2", "3", "4", "5"], allow_duplicates=True)
        )
        for q_label, qg in with_q.group_by("score_q"):
            label = q_label[0] if isinstance(q_label, tuple) else q_label
            if label is None:
                continue
            q = int(label)
            tb = qg.filter(pl.col("tb_label").is_not_null())
            if tb.height == 0:
                continue
            rate = _mean_or_nan(tb["tb_label"] == 1)
            if np.isfinite(rate):
                q_tb[q].append(rate)

    n_sep = len(sep_rows)
    sep = float(np.mean(sep_rows)) if n_sep else None
    results.append(
        MetricResult(
            "H9sep",
            direction,
            sep,
            None,
            None,
            n_sep,
            None,
            "top20-bot20 adj_excess",
        )
    )

    q_means = {
        q: (float(np.mean(vals)) if vals else float("nan")) for q, vals in q_tb.items()
    }
    # Calibration lift: Q5 TB+1 − Q1 TB+1 (higher score quintile should win).
    cal = None
    if np.isfinite(q_means[5]) and np.isfinite(q_means[1]):
        cal = q_means[5] - q_means[1]
    note = " ".join(f"q{q}={q_means[q]:.3f}" for q in range(1, 6) if np.isfinite(q_means[q]))
    results.append(
        MetricResult(
            "H9cal",
            direction,
            cal,
            None,
            None,
            panel.height,
            None,
            note or "thin",
        )
    )
    return results


def h9_k_sweep(panel: pl.DataFrame, direction: str) -> list[MetricResult]:
    """Point H2/H5 for K in {3,5,8} — diagnostic only; gated K unchanged."""
    results: list[MetricResult] = []
    gated_k = k_for(direction)
    if panel.height == 0:
        for k in K_SWEEP:
            results.append(
                MetricResult(
                    "H9ks",
                    direction,
                    None,
                    None,
                    None,
                    0,
                    None,
                    f"K={k} empty gated={gated_k}",
                )
            )
        return results

    for k in K_SWEEP:
        bar_stats = per_bar_topk_stats(panel, k)
        finite_h5 = bar_stats.filter(
            pl.col("h5").is_finite()
            & (pl.col("n_tb_top") > 0)
            & (pl.col("n_tb_rest") > 0)
        )
        h2 = float(bar_stats["spread"].mean()) if bar_stats.height else None
        h5 = float(finite_h5["h5"].mean()) if finite_h5.height else None
        p_top = (
            float(finite_h5["p_tb_top"].mean()) if finite_h5.height else float("nan")
        )
        tag = "gated" if k == gated_k else "diag"
        note = f"K={k} {tag}"
        if finite_h5.height and np.isfinite(p_top):
            note = f"K={k} {tag} h5={h5:.4f} p_top={p_top:.3f}" if h5 is not None else note
        results.append(
            MetricResult(
                "H9ks",
                direction,
                h2,
                None,
                None,
                bar_stats.height,
                None,
                note,
            )
        )
    return results
