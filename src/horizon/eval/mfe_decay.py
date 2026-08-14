"""MFE-decay Step 0 — peak bar, giveback, exit-clock (report-only)."""

from __future__ import annotations

import polars as pl

from src.horizon.eval.constants import H_BARS, MIN_NAMES_PER_BAR, MetricResult, k_for
from src.horizon.eval.panel import prepare_eval_panel

# Hard-stop cuts (charter): dual-fold Top-K mean peak MFE < 0.70 AND giveback < 0.10.
HARD_STOP_MFE_MAX = 0.70
HARD_STOP_GIVEBACK_MAX = 0.10

# Rejected E2 lock (STOP-MEMO) — kept for ledger citation only; not wired to production.
E2_GIVEBACK_EXIT_FRAC = 0.20


def _mean_or_nan(series: pl.Series) -> float:
    m = series.mean()
    return float(m) if m is not None else float("nan")


def _median_or_nan(series: pl.Series) -> float:
    m = series.median()
    return float(m) if m is not None else float("nan")


def per_bar_mfe_decay(panel: pl.DataFrame, k: int) -> pl.DataFrame:
    """Per-bar Top-K vs Rest peak-bar / giveback / Abs MFE cuts."""
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, k + 1):
            continue
        rest = g.filter(pl.col("eval_rank") > k)
        if rest.height == 0:
            continue

        ok = g.filter(
            pl.col("mfe_frac").is_finite()
            & pl.col("giveback_frac").is_finite()
            & pl.col("mfe_peak_bar").is_not_null()
            & pl.col("tb_exit_h").is_not_null()
            & pl.col("tb_label").is_not_null()
        )
        top = ok.filter(pl.col("eval_rank") <= k)
        rest_ok = ok.filter(pl.col("eval_rank") > k)
        if top.height == 0 or rest_ok.height == 0:
            continue

        r12 = ok.filter(pl.col("eval_rank") <= 2)
        r3k = ok.filter((pl.col("eval_rank") >= 3) & (pl.col("eval_rank") <= k))

        early = top.filter(pl.col("mfe_peak_bar") <= 3)
        late = top.filter(pl.col("mfe_peak_bar") >= 4)

        rows.append(
            {
                "date": bar,
                "date_only": g["date_only"][0],
                "n_names": g.height,
                "mfe_top": _mean_or_nan(top["mfe_frac"]),
                "mfe_rest": _mean_or_nan(rest_ok["mfe_frac"]),
                "giveback_top": _mean_or_nan(top["giveback_frac"]),
                "giveback_rest": _mean_or_nan(rest_ok["giveback_frac"]),
                "peak_bar_top_mean": _mean_or_nan(top["mfe_peak_bar"]),
                "peak_bar_top_med": _median_or_nan(top["mfe_peak_bar"]),
                "peak_bar_rest_med": _median_or_nan(rest_ok["mfe_peak_bar"]),
                "exit_h_top_mean": _mean_or_nan(top["tb_exit_h"]),
                "p_tp_top": _mean_or_nan(top["tb_label"] == 1),
                "p_sl_top": _mean_or_nan(top["tb_label"] == -1),
                "p_to_top": _mean_or_nan(top["tb_label"] == 0),
                "early_share": early.height / top.height,
                "early_p_tp": (
                    _mean_or_nan(early["tb_label"] == 1) if early.height else float("nan")
                ),
                "early_giveback": (
                    _mean_or_nan(early["giveback_frac"]) if early.height else float("nan")
                ),
                "late_p_tp": (
                    _mean_or_nan(late["tb_label"] == 1) if late.height else float("nan")
                ),
                "late_giveback": (
                    _mean_or_nan(late["giveback_frac"]) if late.height else float("nan")
                ),
                "peak_12": (
                    _median_or_nan(r12["mfe_peak_bar"]) if r12.height else float("nan")
                ),
                "peak_3k": (
                    _median_or_nan(r3k["mfe_peak_bar"]) if r3k.height else float("nan")
                ),
                "giveback_12": (
                    _mean_or_nan(r12["giveback_frac"]) if r12.height else float("nan")
                ),
                "giveback_3k": (
                    _mean_or_nan(r3k["giveback_frac"]) if r3k.height else float("nan")
                ),
            }
        )

    schema = {
        "date": pl.Datetime,
        "date_only": pl.Date,
        "n_names": pl.Int64,
        "mfe_top": pl.Float64,
        "mfe_rest": pl.Float64,
        "giveback_top": pl.Float64,
        "giveback_rest": pl.Float64,
        "peak_bar_top_mean": pl.Float64,
        "peak_bar_top_med": pl.Float64,
        "peak_bar_rest_med": pl.Float64,
        "exit_h_top_mean": pl.Float64,
        "p_tp_top": pl.Float64,
        "p_sl_top": pl.Float64,
        "p_to_top": pl.Float64,
        "early_share": pl.Float64,
        "early_p_tp": pl.Float64,
        "early_giveback": pl.Float64,
        "late_p_tp": pl.Float64,
        "late_giveback": pl.Float64,
        "peak_12": pl.Float64,
        "peak_3k": pl.Float64,
        "giveback_12": pl.Float64,
        "giveback_3k": pl.Float64,
    }
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema=schema)


def _exit_clock_note(panel: pl.DataFrame, k: int) -> str:
    """Top-K share of exits by barrier bar × type (TP/SL/timeout)."""
    top = panel.filter(
        (pl.col("eval_rank") <= k)
        & pl.col("tb_exit_h").is_not_null()
        & pl.col("tb_label").is_not_null()
    )
    if top.height == 0:
        return "empty Top-K"
    parts: list[str] = []
    for h in range(1, H_BARS + 1):
        slice_h = top.filter(pl.col("tb_exit_h") == h)
        if slice_h.height == 0:
            continue
        n = slice_h.height
        share = n / top.height
        p_tp = float((slice_h["tb_label"] == 1).mean())
        p_sl = float((slice_h["tb_label"] == -1).mean())
        p_to = float((slice_h["tb_label"] == 0).mean())
        parts.append(
            f"h{h}:{share:.2f}(TP/SL/TO={p_tp:.2f}/{p_sl:.2f}/{p_to:.2f})"
        )
    return " ".join(parts) if parts else "thin"


def mfe_decay_diagnostics(
    scored: pl.DataFrame,
    direction: str,
) -> list[MetricResult]:
    """
    Step 0 MFE peak / giveback / exit-clock readout for one sleeve.

    Hard-stop inputs (charter): Top-K mean Abs MFE and mean giveback.
    """
    panel = prepare_eval_panel(scored, direction)
    k = k_for(direction)
    required = {"mfe_frac", "giveback_frac", "mfe_peak_bar", "tb_exit_h"}
    if panel.height == 0 or not required.issubset(panel.columns):
        missing = sorted(required - set(panel.columns))
        return [
            MetricResult(
                "MFEabs",
                direction,
                None,
                None,
                None,
                0,
                False,
                f"empty or missing {missing}",
            )
        ]

    bar_stats = per_bar_mfe_decay(panel, k)
    metrics: list[MetricResult] = []
    n = bar_stats.height

    if n == 0:
        return [
            MetricResult(
                "MFEabs", direction, None, None, None, 0, False, "no eligible bars"
            )
        ]

    mfe_top = float(bar_stats["mfe_top"].mean())
    gb_top = float(bar_stats["giveback_top"].mean())
    peak_med = float(bar_stats["peak_bar_top_med"].mean())
    peak_mean = float(bar_stats["peak_bar_top_mean"].mean())
    early_share = float(bar_stats["early_share"].mean())

    metrics.append(
        MetricResult(
            "MFEabs",
            direction,
            mfe_top,
            None,
            None,
            n,
            None,
            (
                f"top={mfe_top:.3f} rest={float(bar_stats['mfe_rest'].mean()):.3f} "
                f"(path-density Abs MFE / TP floor)"
            ),
        )
    )
    metrics.append(
        MetricResult(
            "GIVEBACK",
            direction,
            gb_top,
            None,
            None,
            n,
            None,
            (
                f"top={gb_top:.3f} rest={float(bar_stats['giveback_rest'].mean()):.3f} "
                f"(MFE_held - fav_at_exit) / TP floor"
            ),
        )
    )
    metrics.append(
        MetricResult(
            "PEAKbar",
            direction,
            peak_med,
            None,
            None,
            n,
            None,
            (
                f"top_med={peak_med:.2f} top_mean={peak_mean:.2f} "
                f"rest_med={float(bar_stats['peak_bar_rest_med'].mean()):.2f} "
                f"early1-3_share={early_share:.3f}"
            ),
        )
    )
    metrics.append(
        MetricResult(
            "EXITclk",
            direction,
            float(bar_stats["exit_h_top_mean"].mean()),
            None,
            None,
            n,
            None,
            _exit_clock_note(panel, k),
        )
    )
    metrics.append(
        MetricResult(
            "EXITmix",
            direction,
            float(bar_stats["p_tp_top"].mean()),
            None,
            None,
            n,
            None,
            (
                f"top TP/SL/TO="
                f"{float(bar_stats['p_tp_top'].mean()):.3f}/"
                f"{float(bar_stats['p_sl_top'].mean()):.3f}/"
                f"{float(bar_stats['p_to_top'].mean()):.3f}"
            ),
        )
    )

    early_gb = bar_stats.filter(pl.col("early_giveback").is_finite())
    late_gb = bar_stats.filter(pl.col("late_giveback").is_finite())
    metrics.append(
        MetricResult(
            "EARLYpk",
            direction,
            early_share,
            None,
            None,
            n,
            None,
            (
                f"early_TP={float(early_gb['early_p_tp'].mean()) if early_gb.height else float('nan'):.3f} "
                f"early_GB={float(early_gb['early_giveback'].mean()) if early_gb.height else float('nan'):.3f} "
                f"late_TP={float(late_gb['late_p_tp'].mean()) if late_gb.height else float('nan'):.3f} "
                f"late_GB={float(late_gb['late_giveback'].mean()) if late_gb.height else float('nan'):.3f}"
            ),
        )
    )

    tier = bar_stats.filter(
        pl.col("peak_12").is_finite()
        & pl.col("peak_3k").is_finite()
        & pl.col("giveback_12").is_finite()
        & pl.col("giveback_3k").is_finite()
    )
    if tier.height:
        metrics.append(
            MetricResult(
                "TIERpk",
                direction,
                float((tier["peak_12"] - tier["peak_3k"]).mean()),
                None,
                None,
                tier.height,
                None,
                (
                    f"peak_12={float(tier['peak_12'].mean()):.2f} "
                    f"peak_3k={float(tier['peak_3k'].mean()):.2f} "
                    f"gb_12={float(tier['giveback_12'].mean()):.3f} "
                    f"gb_3k={float(tier['giveback_3k'].mean()):.3f}"
                ),
            )
        )

    # Per-fold hard-stop candidate (dual-fold AND applied in harness).
    hard_stop = (mfe_top < HARD_STOP_MFE_MAX) and (gb_top < HARD_STOP_GIVEBACK_MAX)
    metrics.append(
        MetricResult(
            "HARDSTOP",
            direction,
            1.0 if hard_stop else 0.0,
            None,
            None,
            n,
            hard_stop,
            (
                f"MFE<{HARD_STOP_MFE_MAX} AND GB<{HARD_STOP_GIVEBACK_MAX} "
                f"-> STOP@0/2"
                if hard_stop
                else (
                    f"MFE={mfe_top:.3f} GB={gb_top:.3f} "
                    f"(need both <{HARD_STOP_MFE_MAX}/<{HARD_STOP_GIVEBACK_MAX})"
                )
            ),
        )
    )
    return metrics


def evaluate_mfe_decay(
    scored: pl.DataFrame,
    directions: list[str],
) -> list[MetricResult]:
    """Run Step 0 MFE-decay diagnostics for requested sleeves."""
    metrics: list[MetricResult] = []
    for direction in directions:
        metrics.extend(mfe_decay_diagnostics(scored, direction))
    return metrics


def select_e1_h_eff(fold_peak_medians: list[float], early_shares: list[float]) -> int | None:
    """
    E1 H_eff lock (charter): exactly one of {3,4} from Step 0 peak-bar rule.

    H_eff=3 if Top-K median peak bar <= 3 on both folds;
    else H_eff=4 if median <= 4 on both folds and early-peak pattern holds;
    else None (E1 not usable).
    """
    if len(fold_peak_medians) < 2 or len(early_shares) < 2:
        return None
    if all(m <= 3.0 for m in fold_peak_medians):
        return 3
    early_ok = all(s >= 0.5 for s in early_shares)
    if all(m <= 4.0 for m in fold_peak_medians) and early_ok:
        return 4
    return None
