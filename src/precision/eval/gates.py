"""Tier 3 Precision eval — P0 preconditions and gated P1 / P2 / P3."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.horizon.eval.bar_stats import per_bar_topk_stats
from src.horizon.eval.gates import h5_stock_tb_bridge
from src.horizon.eval.panel import prepare_eval_panel as prepare_horizon_panel
from src.precision.eval.constants import (
    ROUND_TRIP_COST,
    MetricResult,
    k_for,
    min_fires_for,
    session_block_diff_ci,
    session_block_mean_ci,
    session_ids,
)
from src.precision.scores import check_rank_edge_polarity
from src.utils.eval_common import MIN_SESSIONS


def p0_preconditions(
    raw_sleeve: pl.DataFrame,
    gated: pl.DataFrame,
    direction: str,
) -> list[MetricResult]:
    """Binary P0 checklist. Fail any wiring / K / MIS check → do not gate P1–P3."""
    k = k_for(direction)
    n_raw = raw_sleeve.height
    n_gated = gated.height

    polarity = check_rank_edge_polarity(raw_sleeve, bar_col="decision_bar")
    p0_pol = MetricResult(
        "P0pol",
        direction,
        float(polarity["rank_polarity_violations"]),
        None,
        None,
        int(polarity["rank_polarity_groups"]),
        bool(polarity["rank_polarity_ok"]),
        f"violations={polarity['rank_polarity_violations']}",
    )

    max_rank_val = raw_sleeve["horizon_rank"].max() if n_raw else None
    max_rank = int(max_rank_val) if max_rank_val is not None else 0
    p0_k = MetricResult(
        "P0k",
        direction,
        float(max_rank),
        None,
        None,
        n_raw,
        max_rank <= k and n_raw > 0,
        f"live_max_rank={max_rank} locked_K={k}",
    )

    n_bleed = (
        int(raw_sleeve.filter(pl.col("auction_bleed")).height) if n_raw else 0
    )
    n_late = (
        int(raw_sleeve.filter(pl.col("past_last_entry")).height) if n_raw else 0
    )
    p0_mis = MetricResult(
        "P0mis",
        direction,
        float(n_bleed + n_late),
        None,
        None,
        n_raw,
        n_bleed == 0 and n_late == 0 and n_raw > 0,
        f"bleed={n_bleed} past_last={n_late}",
    )

    n_cir = (
        int(raw_sleeve.filter(pl.col("circuit_block")).height) if n_raw else 0
    )
    p0_cir = MetricResult(
        "P0cir",
        direction,
        n_cir / n_raw if n_raw else None,
        None,
        None,
        n_cir,
        None,
        f"excluded={n_cir} gated={n_gated} (flag/exclude, not a fail)",
    )
    return [p0_pol, p0_k, p0_mis, p0_cir]


def p0_ok(metrics: list[MetricResult]) -> bool:
    return all(
        m.gate_pass for m in metrics if m.name in ("P0pol", "P0k", "P0mis")
    )


def horizon_h5_ci_lb(
    scored: pl.DataFrame | None,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """Same-sleeve Horizon H5 CI LB — P3 promotion unlock (Option C)."""
    if scored is None or scored.height == 0:
        return MetricResult(
            "H5pre",
            direction,
            None,
            None,
            None,
            0,
            False,
            "H5 not measured",
        )
    panel = prepare_horizon_panel(scored, direction)
    bar_stats = per_bar_topk_stats(panel, k_for(direction))
    h5_metrics = h5_stock_tb_bridge(bar_stats, direction, n_boot, rng)
    h5 = next(m for m in h5_metrics if m.name == "H5")
    unlocked = h5.ci_low is not None and h5.ci_low > 0.0
    return MetricResult(
        "H5pre",
        direction,
        h5.value,
        h5.ci_low,
        h5.ci_high,
        h5.n,
        unlocked,
        h5.note if unlocked else f"UPSTREAM_BLOCKED {h5.note}",
    )


def p1_selectivity(
    gated: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """mean(NaiveTBPathEV | Fired) − mean(NaiveTBPathEV | Skipped)."""
    finite = gated.filter(pl.col("naive_net").is_finite())
    fired = finite.filter(pl.col("precision_fire"))
    skipped = finite.filter(~pl.col("precision_fire"))
    n_fire, n_skip = fired.height, skipped.height
    n_sess = (
        finite.select(pl.col("date_only").n_unique()).item() if finite.height else 0
    )
    min_n = min_fires_for(direction)
    if n_fire < min_n or n_skip == 0 or n_sess < MIN_SESSIONS:
        return MetricResult(
            "P1",
            direction,
            None,
            None,
            None,
            n_fire,
            False,
            f"thin fires={n_fire} skip={n_skip} sess={n_sess}",
        )

    a = fired["naive_net"].to_numpy()
    b = skipped["naive_net"].to_numpy()
    point, ci_lo, ci_hi = session_block_diff_ci(
        a,
        fired["date_only"].to_list(),
        b,
        skipped["date_only"].to_list(),
        n_boot,
        rng,
    )
    return MetricResult(
        "P1",
        direction,
        point,
        ci_lo,
        ci_hi,
        n_fire,
        ci_lo > 0.0,
        f"skip={n_skip} sess={n_sess}",
    )


def p2_timing(
    gated: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """mean(PrecNet − NaiveNet | Fired) — same frozen widths, fill vs decision-close."""
    fired = gated.filter(
        pl.col("precision_fire") & pl.col("timing_lift").is_finite()
    )
    n_fire = fired.height
    n_sess = (
        fired.select(pl.col("date_only").n_unique()).item() if n_fire else 0
    )
    min_n = min_fires_for(direction)
    if n_fire < min_n or n_sess < MIN_SESSIONS:
        return MetricResult(
            "P2",
            direction,
            None,
            None,
            None,
            n_fire,
            False,
            f"thin fires={n_fire} sess={n_sess}",
        )

    values = fired["timing_lift"].to_numpy()
    point, ci_lo, ci_hi = session_block_mean_ci(
        values, session_ids(fired["date_only"].to_list()), n_boot, rng
    )
    return MetricResult(
        "P2",
        direction,
        point,
        ci_lo,
        ci_hi,
        n_fire,
        ci_lo > 0.0,
        f"sess={n_sess}",
    )


def p3_expectancy(
    gated: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
    *,
    h5_unlocked: bool,
) -> MetricResult:
    """mean(gross − c* | Fired), unsized. Gated only after same-sleeve H5 CI LB > 0."""
    fired = gated.filter(
        pl.col("precision_fire") & pl.col("prec_net").is_finite()
    )
    n_fire = fired.height
    n_sess = (
        fired.select(pl.col("date_only").n_unique()).item() if n_fire else 0
    )
    min_n = min_fires_for(direction)
    if n_fire < min_n or n_sess < MIN_SESSIONS:
        return MetricResult(
            "P3",
            direction,
            None,
            None,
            None,
            n_fire,
            False if h5_unlocked else None,
            f"thin fires={n_fire} sess={n_sess}",
        )

    values = fired["prec_net"].to_numpy()
    point, ci_lo, ci_hi = session_block_mean_ci(
        values, session_ids(fired["date_only"].to_list()), n_boot, rng
    )
    if not h5_unlocked:
        return MetricResult(
            "P3",
            direction,
            point,
            ci_lo,
            ci_hi,
            n_fire,
            None,
            f"UPSTREAM_BLOCKED report-only c*={ROUND_TRIP_COST:.4f} sess={n_sess}",
        )
    return MetricResult(
        "P3",
        direction,
        point,
        ci_lo,
        ci_hi,
        n_fire,
        ci_lo > 0.0,
        f"c*={ROUND_TRIP_COST:.4f} sess={n_sess}",
    )


def precondition_blocked(
    name: str, direction: str, n: int
) -> MetricResult:
    return MetricResult(
        name, direction, None, None, None, n, False, "precondition-fail"
    )
