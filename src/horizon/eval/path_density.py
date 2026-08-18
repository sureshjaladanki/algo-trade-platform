"""AUDIT-ONLY (fresh M0 quarantine) — path-density Step 0.

See docs/archive/horizon-fresh-quarantine-index.md.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from src.horizon.eval.constants import MIN_NAMES_PER_BAR, k_for, min_bars_for
from src.horizon.eval.panel import prepare_eval_panel
from src.utils.eval_common import MIN_SESSIONS, MetricResult, session_block_mean_ci


def _mean_or_nan(series: pl.Series) -> float:
    m = series.mean()
    return float(m) if m is not None else float("nan")


def per_bar_path_density(panel: pl.DataFrame, k: int) -> pl.DataFrame:
    """Per-bar Top-K vs Rest MFE + exit mix + rank-tier cuts."""
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, k + 1):
            continue
        rest = g.filter(pl.col("eval_rank") > k)
        if rest.height == 0:
            continue

        mfe_ok = g.filter(pl.col("mfe_frac").is_finite())
        mfe_top = mfe_ok.filter(pl.col("eval_rank") <= k)
        mfe_rest = mfe_ok.filter(pl.col("eval_rank") > k)
        if mfe_top.height == 0 or mfe_rest.height == 0:
            continue

        tb = g.filter(pl.col("tb_label").is_not_null())
        tb_top = tb.filter(pl.col("eval_rank") <= k)
        tb_rest = tb.filter(pl.col("eval_rank") > k)
        if tb_top.height == 0 or tb_rest.height == 0:
            continue

        r12 = mfe_ok.filter(pl.col("eval_rank") <= 2)
        r3k = mfe_ok.filter((pl.col("eval_rank") >= 3) & (pl.col("eval_rank") <= k))
        tb_r12 = tb.filter(pl.col("eval_rank") <= 2)
        tb_r3k = tb.filter((pl.col("eval_rank") >= 3) & (pl.col("eval_rank") <= k))

        mean_mfe_top = _mean_or_nan(mfe_top["mfe_frac"])
        mean_mfe_rest = _mean_or_nan(mfe_rest["mfe_frac"])
        p_tp_top = _mean_or_nan(tb_top["tb_label"] == 1)
        p_sl_top = _mean_or_nan(tb_top["tb_label"] == -1)
        p_to_top = _mean_or_nan(tb_top["tb_label"] == 0)
        p_tp_rest = _mean_or_nan(tb_rest["tb_label"] == 1)
        p_sl_rest = _mean_or_nan(tb_rest["tb_label"] == -1)
        p_to_rest = _mean_or_nan(tb_rest["tb_label"] == 0)

        rows.append(
            {
                "date": bar,
                "date_only": g["date_only"][0],
                "n_names": g.height,
                "mfe_top": mean_mfe_top,
                "mfe_rest": mean_mfe_rest,
                "mfe_spread": mean_mfe_top - mean_mfe_rest,
                "p_tp_top": p_tp_top,
                "p_sl_top": p_sl_top,
                "p_to_top": p_to_top,
                "p_tp_rest": p_tp_rest,
                "p_sl_rest": p_sl_rest,
                "p_to_rest": p_to_rest,
                "tp_spread": p_tp_top - p_tp_rest,
                "mfe_12": _mean_or_nan(r12["mfe_frac"]) if r12.height else float("nan"),
                "mfe_3k": (
                    _mean_or_nan(r3k["mfe_frac"]) if r3k.height else float("nan")
                ),
                "p_tp_12": (
                    _mean_or_nan(tb_r12["tb_label"] == 1) if tb_r12.height else float("nan")
                ),
                "p_tp_3k": (
                    _mean_or_nan(tb_r3k["tb_label"] == 1) if tb_r3k.height else float("nan")
                ),
            }
        )

    schema = {
        "date": pl.Datetime,
        "date_only": pl.Date,
        "n_names": pl.Int64,
        "mfe_top": pl.Float64,
        "mfe_rest": pl.Float64,
        "mfe_spread": pl.Float64,
        "p_tp_top": pl.Float64,
        "p_sl_top": pl.Float64,
        "p_to_top": pl.Float64,
        "p_tp_rest": pl.Float64,
        "p_sl_rest": pl.Float64,
        "p_to_rest": pl.Float64,
        "tp_spread": pl.Float64,
        "mfe_12": pl.Float64,
        "mfe_3k": pl.Float64,
        "p_tp_12": pl.Float64,
        "p_tp_3k": pl.Float64,
    }
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema=schema)


def _ci_metric(
    name: str,
    direction: str,
    bar_stats: pl.DataFrame,
    col: str,
    n_boot: int,
    rng: np.random.Generator,
    note: str,
) -> MetricResult:
    finite = bar_stats.filter(pl.col(col).is_finite())
    n = finite.height
    n_sessions = finite.select(pl.col("date_only").n_unique()).item() if n else 0
    min_bars = min_bars_for(direction)
    if n < min_bars or n_sessions < MIN_SESSIONS:
        return MetricResult(
            name, direction, None, None, None, n, False, f"thin {note}"
        )
    values = finite[col].to_numpy()
    sessions = finite["date_only"].to_list()
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    return MetricResult(
        name,
        direction,
        point,
        ci_lo,
        ci_hi,
        n,
        ci_lo > 0.0,
        note,
    )


def adv_tercile_mfe_diagnostics(
    panel: pl.DataFrame, direction: str
) -> list[MetricResult]:
    """Report-only ADV tercile of Top-K MFE + TB+1."""
    k = k_for(direction)
    if "adv_rank_20d" not in panel.columns or panel.height == 0:
        return [
            MetricResult(
                "ADVmfe", direction, None, None, None, 0, None, "missing adv_rank_20d"
            )
        ]
    top = panel.filter(
        (pl.col("eval_rank") <= k)
        & pl.col("adv_rank_20d").is_finite()
        & pl.col("mfe_frac").is_finite()
    )
    if top.height == 0:
        return [
            MetricResult("ADVmfe", direction, None, None, None, 0, None, "empty Top-K")
        ]
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
            mean_mfe=pl.col("mfe_frac").mean(),
            p_tb=(pl.col("tb_label") == 1).mean(),
        )
        .sort("adv_bucket")
    )
    share = {r["adv_bucket"]: r["n"] / top.height for r in buckets.iter_rows(named=True)}
    mfe = {r["adv_bucket"]: r["mean_mfe"] for r in buckets.iter_rows(named=True)}
    p_tb = {r["adv_bucket"]: r["p_tb"] for r in buckets.iter_rows(named=True)}
    note = (
        f"share lo/mid/hi="
        f"{share.get('lo', 0):.2f}/{share.get('mid', 0):.2f}/{share.get('hi', 0):.2f} "
        f"MFE={mfe.get('lo', float('nan')):.3f}/"
        f"{mfe.get('mid', float('nan')):.3f}/"
        f"{mfe.get('hi', float('nan')):.3f} "
        f"TB+1={p_tb.get('lo', float('nan')):.3f}/"
        f"{p_tb.get('mid', float('nan')):.3f}/"
        f"{p_tb.get('hi', float('nan')):.3f}"
    )
    return [
        MetricResult(
            "ADVmfe",
            direction,
            float(share.get("lo", 0.0)),
            None,
            None,
            int(top.height),
            None,
            note,
        )
    ]


def path_density_diagnostics(
    scored: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """
    Step 0 path-travel readout for one sleeve.

    Primary separation signals (hard-stop inputs):
      MFE -- mean(Top-K mfe_frac - Rest); CI LB > 0 => travel separation
      EXIT -- mean(Top-K TP-share - Rest); CI LB > 0 => exit-mix separation
    """
    panel = prepare_eval_panel(scored, direction)
    k = k_for(direction)
    if panel.height == 0 or "mfe_frac" not in panel.columns:
        return [
            MetricResult(
                "MFE",
                direction,
                None,
                None,
                None,
                0,
                False,
                "empty or missing mfe_frac",
            )
        ]

    bar_stats = per_bar_path_density(panel, k)
    metrics: list[MetricResult] = []

    mfe = _ci_metric(
        "MFE",
        direction,
        bar_stats,
        "mfe_spread",
        n_boot,
        rng,
        f"Top-Rest mfe/TP_floor K={k}",
    )
    metrics.append(mfe)
    if bar_stats.height:
        metrics.append(
            MetricResult(
                "MFEabs",
                direction,
                float(bar_stats["mfe_top"].mean()),
                None,
                None,
                bar_stats.height,
                None,
                (
                    f"top={float(bar_stats['mfe_top'].mean()):.3f} "
                    f"rest={float(bar_stats['mfe_rest'].mean()):.3f}"
                ),
            )
        )

    exit_m = _ci_metric(
        "EXIT",
        direction,
        bar_stats,
        "tp_spread",
        n_boot,
        rng,
        f"Top-Rest TP-share K={k}",
    )
    metrics.append(exit_m)
    if bar_stats.height:
        metrics.append(
            MetricResult(
                "EXITmix",
                direction,
                float(bar_stats["p_tp_top"].mean()),
                None,
                None,
                bar_stats.height,
                None,
                (
                    f"top TP/SL/TO="
                    f"{float(bar_stats['p_tp_top'].mean()):.3f}/"
                    f"{float(bar_stats['p_sl_top'].mean()):.3f}/"
                    f"{float(bar_stats['p_to_top'].mean()):.3f} "
                    f"rest="
                    f"{float(bar_stats['p_tp_rest'].mean()):.3f}/"
                    f"{float(bar_stats['p_sl_rest'].mean()):.3f}/"
                    f"{float(bar_stats['p_to_rest'].mean()):.3f}"
                ),
            )
        )

    # Rank tier 1–2 vs 3–K (soft-H3-aligned; report-only).
    tier_mfe = bar_stats.filter(
        pl.col("mfe_12").is_finite() & pl.col("mfe_3k").is_finite()
    )
    if tier_mfe.height:
        metrics.append(
            MetricResult(
                "MFEtier",
                direction,
                float((tier_mfe["mfe_12"] - tier_mfe["mfe_3k"]).mean()),
                None,
                None,
                tier_mfe.height,
                None,
                (
                    f"mfe_12={float(tier_mfe['mfe_12'].mean()):.3f} "
                    f"mfe_3k={float(tier_mfe['mfe_3k'].mean()):.3f} "
                    f"tp_12={float(tier_mfe['p_tp_12'].mean()):.3f} "
                    f"tp_3k={float(tier_mfe['p_tp_3k'].mean()):.3f}"
                ),
            )
        )

    metrics.extend(adv_tercile_mfe_diagnostics(panel, direction))

    # Hard-stop companion: SEPARATED if either MFE or EXIT CI LB > 0.
    separated = bool(mfe.gate_pass) or bool(exit_m.gate_pass)
    metrics.append(
        MetricResult(
            "SEP",
            direction,
            1.0 if separated else 0.0,
            None,
            None,
            bar_stats.height,
            separated,
            (
                "MFE|EXIT CI LB>0 -> density signal"
                if separated
                else "no Top-K vs Rest travel separation"
            ),
        )
    )
    return metrics


def evaluate_path_density(
    scored: pl.DataFrame,
    directions: list[str],
    n_boot: int,
    seed: int,
) -> list[MetricResult]:
    """Run Step 0 diagnostics for requested sleeves."""
    rng = np.random.default_rng(seed)
    metrics: list[MetricResult] = []
    for direction in directions:
        metrics.extend(path_density_diagnostics(scored, direction, n_boot, rng))
    return metrics
