"""Short-sleeve Horizon eval — S1 circuit/UC hygiene, H7 path slices, S2 TOD report-first."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.horizon.eval.constants import (
    APPLY_S1_SHORT,
    CIRCUIT_RANGE_EPS,
    H_BARS,
    MetricResult,
    k_for,
)

# Report-first S2 afternoon split (bar-end). Aligns with Precision Short post-13:00 hygiene.
S2_AFTERNOON_START = dt.time(13, 0)


def s1_circuit_ok_expr() -> pl.Expr:
    """Pre-registered S1: exclude decision-bar circuit or forward UC trap."""
    return ~pl.col("is_circuit_bar") & ~pl.col("fwd_circuit_hit")


def s1_activation_note(
    scored: pl.DataFrame,
    panel: pl.DataFrame,
    direction: str,
) -> MetricResult:
    """Report whether S1 Short hygiene is active and how many rows it dropped."""
    if direction != "short":
        return MetricResult("S1", direction, None, None, None, panel.height, None, "n/a")
    if not APPLY_S1_SHORT:
        return MetricResult(
            "S1", direction, 0.0, None, None, panel.height, None, "off"
        )

    # Local import avoids cycle: panel ↔ short_eval (via prepare_eval_panel).
    from src.horizon.eval.panel import annotate_hygiene_flags, eligible_expr

    base = annotate_hygiene_flags(scored)
    if "time_only" not in base.columns:
        base = base.with_columns(time_only=pl.col("date").dt.time())
    pre = base.filter(eligible_expr(direction))
    n_pre = pre.height
    n_post = panel.height
    dropped = n_pre - n_post
    pct = dropped / n_pre if n_pre else 0.0
    return MetricResult(
        "S1",
        direction,
        pct,
        None,
        None,
        n_post,
        None,
        f"on drop={dropped}/{n_pre} eps={CIRCUIT_RANGE_EPS} H={H_BARS}",
    )


def _slice_point_metrics(
    panel: pl.DataFrame,
    direction: str,
    slice_name: str,
    prefix: str = "H7",
) -> list[MetricResult]:
    """Point-only H1/H2/H5 on a panel slice — diagnostic, no CI ship claims."""
    from src.horizon.eval.bar_stats import per_bar_ic, per_bar_topk_stats

    k = k_for(direction)
    n = panel.height
    names = (f"{prefix}h1", f"{prefix}h2", f"{prefix}h5")
    if n == 0:
        return [
            MetricResult(
                name,
                direction,
                None,
                None,
                None,
                0,
                None,
                f"slice={slice_name} empty",
            )
            for name in names
        ]

    ic_df = per_bar_ic(panel)
    h1 = float(ic_df["ic"].mean()) if ic_df.height else None
    bar_stats = per_bar_topk_stats(panel, k)
    h2 = float(bar_stats["spread"].mean()) if bar_stats.height else None
    finite_h5 = bar_stats.filter(
        pl.col("h5").is_finite()
        & (pl.col("n_tb_top") > 0)
        & (pl.col("n_tb_rest") > 0)
    )
    h5 = float(finite_h5["h5"].mean()) if finite_h5.height else None
    p_top = float(finite_h5["p_tb_top"].mean()) if finite_h5.height else float("nan")
    note = f"slice={slice_name}"
    if finite_h5.height:
        note = f"slice={slice_name} p_top={p_top:.3f}"
    return [
        MetricResult(names[0], direction, h1, None, None, ic_df.height, None, note),
        MetricResult(names[1], direction, h2, None, None, bar_stats.height, None, note),
        MetricResult(names[2], direction, h5, None, None, finite_h5.height, None, note),
    ]


def h7_path_slice_diagnostics(
    panel: pl.DataFrame,
    direction: str,
) -> list[MetricResult]:
    """
    Short-focused H7 path slices (point estimates only).

    Clean / fwd-circuit / expiry / non-expiry — report-only, never gates ship.
    """
    if direction != "short" or panel.height == 0:
        return []
    if "is_circuit_bar" not in panel.columns:
        return []

    clean = panel.filter(~pl.col("is_circuit_bar") & ~pl.col("fwd_circuit_hit"))
    dirty = panel.filter(pl.col("fwd_circuit_hit"))
    expiry = panel.filter(pl.col("is_expiry_day"))
    non_expiry = panel.filter(~pl.col("is_expiry_day"))
    results: list[MetricResult] = []
    results.extend(_slice_point_metrics(clean, direction, "clean"))
    results.extend(_slice_point_metrics(dirty, direction, "fwd_circuit"))
    results.extend(_slice_point_metrics(expiry, direction, "expiry"))
    results.extend(_slice_point_metrics(non_expiry, direction, "non_expiry"))
    return results


def s2_tod_diagnostics(panel: pl.DataFrame, direction: str) -> list[MetricResult]:
    """
    S2 report-first: morning vs afternoon Short path quality (no hard cut).

    Afternoon = ``time_only >= 13:00`` bar-end. Never gates ship.
    """
    if direction != "short":
        return [
            MetricResult("S2cov", direction, None, None, None, panel.height, None, "n/a")
        ]
    if panel.height == 0:
        return [
            MetricResult("S2cov", direction, None, None, None, 0, None, "empty"),
        ]

    afternoon = panel.filter(pl.col("time_only") >= S2_AFTERNOON_START)
    morning = panel.filter(pl.col("time_only") < S2_AFTERNOON_START)
    pct_pm = afternoon.height / panel.height
    n_bars_am = morning.select(pl.col("date").n_unique()).item() if morning.height else 0
    n_bars_pm = (
        afternoon.select(pl.col("date").n_unique()).item() if afternoon.height else 0
    )
    results: list[MetricResult] = [
        MetricResult(
            "S2cov",
            direction,
            pct_pm,
            None,
            None,
            panel.height,
            None,
            (
                f"pm>={S2_AFTERNOON_START.strftime('%H:%M')} "
                f"bars_am={n_bars_am} bars_pm={n_bars_pm} report-first"
            ),
        )
    ]
    results.extend(_slice_point_metrics(morning, direction, "morning", prefix="S2"))
    results.extend(_slice_point_metrics(afternoon, direction, "afternoon", prefix="S2"))
    return results
