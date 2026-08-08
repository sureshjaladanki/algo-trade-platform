"""Precision trade diagnostics — hit-rate / PnL slices for MLflow + console."""

from __future__ import annotations

import math

import polars as pl

from src.labels.triple_barrier import ROUND_TRIP_COST
from src.precision.scores import check_rank_edge_polarity

_EXIT_REASONS = ("TP", "SL", "TIMEOUT", "MIS_FLATTEN")
_SLICE_METRICS = (
    "mean_gross_ret",
    "mean_net_ret",
    "tp_rate",
    "sl_rate",
    "timeout_rate",
    "tb_tp_rate",
    "prec_tp_rate",
)
_NESTED_GROUPS = (
    ("by_entry_reason", "entry"),
    ("by_rank", "rank"),
    ("by_direction", "dir"),
    ("by_edge_score_quartile", "edge"),
    ("by_edge_score_quartile_long", "edge_long"),
    ("by_edge_score_quartile_short", "edge_short"),
)
_SUMMARY_NESTED_KEYS = frozenset(
    {
        "by_direction",
        "by_entry_reason",
        "by_rank",
        "by_edge_score_quartile",
        "by_edge_score_quartile_long",
        "by_edge_score_quartile_short",
        "edge_score_floors",
    }
)
# Phase 1 default TOP_K=5 (1–2 / 3–5); 6–8 appears only in top_k=8 ablations.
_RANK_BANDS = (
    ("1-2", pl.col("horizon_rank") <= 2),
    ("3-5", (pl.col("horizon_rank") >= 3) & (pl.col("horizon_rank") <= 5)),
    ("6-8", (pl.col("horizon_rank") >= 6) & (pl.col("horizon_rank") <= 8)),
)
_TB_LABEL = {"long": "tb_label_long", "short": "tb_label_short"}


def _slice_stats(
    fires: pl.DataFrame,
    *,
    label_col: str | None = None,
) -> dict[str, float | int]:
    """Per-slice n / gross / net / exit mix (+ optional TB TP rate)."""
    n = fires.height
    if n == 0:
        return {"n": 0}

    mean_gross = float(fires["gross_ret"].mean())
    stats: dict[str, float | int] = {
        "n": n,
        "mean_gross_ret": mean_gross,
        "mean_net_ret": mean_gross - ROUND_TRIP_COST,
        "mean_size_mult": float(fires["size_mult"].mean()),
        "tp_rate": fires.filter(pl.col("exit_reason") == "TP").height / n,
        "sl_rate": fires.filter(pl.col("exit_reason") == "SL").height / n,
        "timeout_rate": fires.filter(pl.col("exit_reason") == "TIMEOUT").height / n,
        "mis_flatten_rate": (
            fires.filter(pl.col("exit_reason") == "MIS_FLATTEN").height / n
        ),
    }
    if label_col is None:
        return stats

    labeled = fires.drop_nulls(subset=[label_col])
    if labeled.height == 0:
        return stats

    n_lab = labeled.height
    stats["tb_tp_rate"] = labeled.filter(pl.col(label_col) == 1).height / n_lab
    stats["prec_tp_rate"] = (
        labeled.filter(pl.col("exit_reason") == "TP").height / n_lab
    )
    return stats


def _stats_by_mask(
    fires: pl.DataFrame,
    bands: tuple[tuple[str, pl.Expr], ...],
) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for label, mask in bands:
        subset = fires.filter(mask)
        if subset.height:
            out[label] = _slice_stats(subset)
    return out


def _stats_by_values(
    fires: pl.DataFrame,
    col: str,
    values: tuple[str, ...],
    *,
    label_cols: dict[str, str] | None = None,
) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for value in values:
        subset = fires.filter(pl.col(col) == value)
        if subset.height == 0:
            continue
        label_col = (label_cols or {}).get(value)
        out[value] = _slice_stats(subset, label_col=label_col)
    return out


def _edge_quartiles(
    scored: pl.DataFrame,
) -> tuple[dict[str, float], dict[str, dict]]:
    """Quantile floors + Q1–Q4 slice stats on ``edge_score`` (Q1 = weakest)."""
    if scored.height < 4:
        return {}, {}

    q25, q50, q75 = scored.select(
        pl.col("edge_score").quantile(0.25).alias("q25"),
        pl.col("edge_score").quantile(0.50).alias("q50"),
        pl.col("edge_score").quantile(0.75).alias("q75"),
    ).row(0)

    floors = {"q25": float(q25), "q50": float(q50), "q75": float(q75)}
    bands = (
        ("Q1_weak", pl.col("edge_score") <= q25),
        ("Q2", (pl.col("edge_score") > q25) & (pl.col("edge_score") <= q50)),
        ("Q3", (pl.col("edge_score") > q50) & (pl.col("edge_score") <= q75)),
        ("Q4_strong", pl.col("edge_score") > q75),
    )
    by_q: dict[str, dict] = {}
    for label, mask in bands:
        subset = scored.filter(mask)
        if subset.height:
            by_q[label] = _slice_stats(subset)
    return floors, by_q


def _attach_edge_diagnostics(out: dict, fires: pl.DataFrame) -> None:
    scored = fires.drop_nulls(subset=["edge_score"])
    floors: dict[str, float] = {}

    pooled_floors, pooled_q = _edge_quartiles(scored)
    for k, v in pooled_floors.items():
        floors[f"pooled_{k}"] = v
        out[f"edge_score_{k}"] = v
    out["by_edge_score_quartile"] = pooled_q

    for direction in ("long", "short"):
        sleeve = scored.filter(pl.col("horizon_direction") == direction)
        sleeve_floors, sleeve_q = _edge_quartiles(sleeve)
        for k, v in sleeve_floors.items():
            floors[f"{direction}_{k}"] = v
            out[f"{direction}_edge_score_{k}"] = v
        out[f"by_edge_score_quartile_{direction}"] = sleeve_q

    out["edge_score_floors"] = floors


def summarize_precision_trades(trades: pl.DataFrame) -> dict:
    """
    Hit-rate / PnL diagnostics vs TB label expectations.

    Score slices use ``edge_score`` only (pooled + per sleeve). Raw
    ``horizon_score`` quartiles are omitted — Long/Short polarity makes
    pooled raw scores untrustworthy.
    """
    if trades.height == 0:
        return {"episodes": 0, "fires": 0, "fire_rate": 0.0}

    fires = trades.filter(pl.col("precision_fire"))
    n, n_fire = trades.height, fires.height
    out: dict = {
        "episodes": n,
        "fires": n_fire,
        "fire_rate": n_fire / n,
        **check_rank_edge_polarity(trades),
    }
    if n_fire == 0:
        return out

    out["mean_gross_ret"] = float(fires["gross_ret"].mean())
    out["mean_net_ret"] = out["mean_gross_ret"] - ROUND_TRIP_COST
    out["mean_size_mult"] = float(fires["size_mult"].mean())
    for reason in _EXIT_REASONS:
        out[f"exit_{reason.lower()}"] = fires.filter(
            pl.col("exit_reason") == reason
        ).height

    by_direction = _stats_by_values(
        fires, "horizon_direction", ("long", "short"), label_cols=_TB_LABEL
    )
    out["by_direction"] = by_direction
    for direction, stats in by_direction.items():
        out[f"{direction}_n"] = stats["n"]
        for key in ("tb_tp_rate", "prec_tp_rate"):
            if key in stats:
                out[f"{direction}_{key}"] = stats[key]

    # Per-sleeve fire counts for n-gates (≥300–500 to lock continuous thresholds).
    out["long_fire_n"] = int(by_direction.get("long", {}).get("n", 0))
    out["short_fire_n"] = int(by_direction.get("short", {}).get("n", 0))

    out["by_entry_reason"] = _stats_by_values(
        fires, "entry_reason", ("setup", "fallback")
    )
    out["by_rank"] = _stats_by_mask(fires, _RANK_BANDS)
    _attach_edge_diagnostics(out, fires)
    return out


def format_precision_summary(summary: dict) -> list[str]:
    """Human-readable lines for the Precision summary dict."""
    lines = ["Precision summary:"]
    for key, val in summary.items():
        if key in _SUMMARY_NESTED_KEYS:
            continue
        if isinstance(val, float):
            lines.append(f"   {key}: {val:.4f}")
        else:
            lines.append(f"   {key}: {val}")

    floors = summary.get("edge_score_floors") or {}
    if floors:
        lines.append("\nEdge-score floors (q25 / q50 / q75):")
        for name, val in floors.items():
            lines.append(f"   {name}: {val:.6f}")

    _append_group(lines, "By entry reason", summary.get("by_entry_reason"))
    _append_group(lines, "By rank", summary.get("by_rank"))
    _append_group(lines, "By direction", summary.get("by_direction"))
    _append_group(
        lines,
        "By edge_score quartile (pooled)",
        summary.get("by_edge_score_quartile"),
    )
    _append_group(
        lines,
        "By edge_score quartile (long)",
        summary.get("by_edge_score_quartile_long"),
    )
    _append_group(
        lines,
        "By edge_score quartile (short)",
        summary.get("by_edge_score_quartile_short"),
    )
    return lines


def _append_group(lines: list[str], title: str, group: dict | None) -> None:
    if not group:
        return
    lines.append(f"\n{title}:")
    for name, stats in group.items():
        parts = [f"n={stats.get('n', 0)}"]
        parts.extend(
            f"{metric}={stats[metric]:.4f}"
            for metric in _SLICE_METRICS
            if isinstance(stats.get(metric), float)
        )
        lines.append(f"   {name}: " + "  ".join(parts))


def flatten_precision_summary_metrics(summary: dict) -> dict[str, float]:
    """Flatten nested summary slices into scalar MLflow metrics."""
    flat: dict[str, float] = {}
    for key, val in summary.items():
        if isinstance(val, bool):
            flat[key] = float(val)
        elif isinstance(val, (int, float)) and math.isfinite(float(val)):
            flat[key] = float(val)

    for group_key, prefix in _NESTED_GROUPS:
        for name, stats in (summary.get(group_key) or {}).items():
            tag = str(name).replace("-", "_").lower()
            for metric, mval in stats.items():
                if isinstance(mval, (int, float)) and math.isfinite(float(mval)):
                    flat[f"{prefix}_{tag}_{metric}"] = float(mval)
    return flat
