"""AUDIT-ONLY (fresh M0 quarantine) — TP-floor Step 0.

See docs/archive/horizon-fresh-quarantine-index.md.
"""

from __future__ import annotations

import polars as pl

from src.horizon.eval.constants import MIN_NAMES_PER_BAR, MetricResult, k_for
from src.horizon.eval.panel import prepare_eval_panel
from src.labels.triple_barrier import TP_FLOOR_LONG, TP_FLOOR_LONG_CANDIDATE

# Locked floors in bps (working c*=20).
FLOOR_60_BPS = TP_FLOOR_LONG * 1e4  # 60
FLOOR_50_BPS = TP_FLOOR_LONG_CANDIDATE * 1e4  # 50

# Hard-stop cuts (charter): OR across cuts; fire on either fold → STOP @ 0/1.
HARD_STOP_NEAR_MISS_MIN = 0.05  # near-miss mass < 5% of Top-K
HARD_STOP_SL_CONTAM_MAX = 0.50  # among near-miss, >50% SL-before-50
HARD_STOP_MEAN_MFE_MIN = 45.0  # mean Abs MFE (bps) < 45 on Top-K


def _mean_or_nan(series: pl.Series) -> float:
    m = series.mean()
    return float(m) if m is not None else float("nan")


def _median_or_nan(series: pl.Series) -> float:
    m = series.median()
    return float(m) if m is not None else float("nan")


def _share(mask: pl.Series) -> float:
    if mask.len() == 0:
        return float("nan")
    return float(mask.mean())


def _exit_mix_note(rows: pl.DataFrame) -> str:
    if rows.height == 0:
        return "empty"
    p_tp = _share(rows["tb_label"] == 1)
    p_sl = _share(rows["tb_label"] == -1)
    p_to = _share(rows["tb_label"] == 0)
    return f"TP/SL/TO={p_tp:.3f}/{p_sl:.3f}/{p_to:.3f}"


def _sl_contaminated(rows: pl.DataFrame) -> pl.Series:
    """
    Among paths that reach +50 bps: SL event at/before first +50 touch.

    Clean convertible mass = t_MFE≥50 < t_SL (or no SL). Same-bar SL-first
    (barrier policy) counts as contaminated.
    """
    has_sl = rows["tb_label"] == -1
    t_sl = rows["tb_exit_h"]
    t_50 = rows["mfe50_first_bar"]
    return has_sl & t_50.is_not_null() & (t_sl <= t_50)


def _eligible_bar_dates(panel: pl.DataFrame, k: int) -> list:
    """Bars with enough names and a non-empty Rest (same gate as other Step 0s)."""
    dates = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, k + 1):
            continue
        if g.filter(pl.col("eval_rank") > k).height == 0:
            continue
        ok = g.filter(
            pl.col("mfe_bps").is_finite()
            & pl.col("tb_label").is_not_null()
            & pl.col("tb_exit_h").is_not_null()
        )
        top = ok.filter(pl.col("eval_rank") <= k)
        rest_ok = ok.filter(pl.col("eval_rank") > k)
        if top.height == 0 or rest_ok.height == 0:
            continue
        dates.append(bar)
    return dates


def tp_floor_diagnostics(scored: pl.DataFrame, direction: str) -> list[MetricResult]:
    """
    Step 0 absolute-MFE crossing / near-miss / SL-contamination for one sleeve.

    Hard-stop inputs (charter, Long): near-miss mass, SL-contam, mean Abs MFE.
    """
    panel = prepare_eval_panel(scored, direction)
    k = k_for(direction)
    required = {"mfe_bps", "tb_label", "tb_exit_h"}
    if panel.height == 0 or not required.issubset(panel.columns):
        missing = sorted(required - set(panel.columns))
        return [
            MetricResult(
                "MFEbps",
                direction,
                None,
                None,
                None,
                0,
                False,
                f"empty or missing {missing}",
            )
        ]

    eligible_dates = _eligible_bar_dates(panel, k)
    n_bars = len(eligible_dates)
    if n_bars == 0:
        return [
            MetricResult(
                "MFEbps", direction, None, None, None, 0, False, "no eligible bars"
            )
        ]

    ok = panel.filter(
        pl.col("date").is_in(eligible_dates)
        & pl.col("mfe_bps").is_finite()
        & pl.col("tb_label").is_not_null()
        & pl.col("tb_exit_h").is_not_null()
    )
    top = ok.filter(pl.col("eval_rank") <= k)
    rest = ok.filter(pl.col("eval_rank") > k)
    n_top = top.height

    mfe_top = _mean_or_nan(top["mfe_bps"])
    mfe_rest = _mean_or_nan(rest["mfe_bps"])
    p50 = _share(top["mfe_bps"] >= FLOOR_50_BPS)
    p60 = _share(top["mfe_bps"] >= FLOOR_60_BPS)
    near_mask = (top["mfe_bps"] >= FLOOR_50_BPS) & (top["mfe_bps"] < FLOOR_60_BPS)
    near_mass = _share(near_mask)
    near_miss = top.filter(near_mask)

    p50_r = _share(rest["mfe_bps"] >= FLOOR_50_BPS)
    p60_r = _share(rest["mfe_bps"] >= FLOOR_60_BPS)
    near_r = _share(
        (rest["mfe_bps"] >= FLOOR_50_BPS) & (rest["mfe_bps"] < FLOOR_60_BPS)
    )

    if near_miss.height > 0 and "mfe50_first_bar" in near_miss.columns:
        sl_contam = _share(_sl_contaminated(near_miss))
        near_exit = _exit_mix_note(near_miss)
    else:
        sl_contam = float("nan")
        near_exit = "empty"

    has_peak = "mfe_abs_peak_bar" in top.columns
    peak_near_med = (
        _median_or_nan(near_miss["mfe_abs_peak_bar"])
        if near_miss.height and has_peak
        else float("nan")
    )
    peak_near_mean = (
        _mean_or_nan(near_miss["mfe_abs_peak_bar"])
        if near_miss.height and has_peak
        else float("nan")
    )
    clearers = top.filter(pl.col("mfe_bps") >= FLOOR_60_BPS)
    peak_clear_med = (
        _median_or_nan(clearers["mfe_abs_peak_bar"])
        if clearers.height and has_peak
        else float("nan")
    )
    peak_clear_mean = (
        _mean_or_nan(clearers["mfe_abs_peak_bar"])
        if clearers.height and has_peak
        else float("nan")
    )

    metrics: list[MetricResult] = [
        MetricResult(
            "MFEbps",
            direction,
            mfe_top,
            None,
            None,
            n_bars,
            None,
            f"top={mfe_top:.2f} rest={mfe_rest:.2f} bps (abs MFE; n_top={n_top})",
        ),
        MetricResult(
            "CROSS50",
            direction,
            p50,
            None,
            None,
            n_bars,
            None,
            f"P(MFE≥{FLOOR_50_BPS:.0f}) top={p50:.3f} rest={p50_r:.3f}",
        ),
        MetricResult(
            "CROSS60",
            direction,
            p60,
            None,
            None,
            n_bars,
            None,
            f"P(MFE≥{FLOOR_60_BPS:.0f}) top={p60:.3f} rest={p60_r:.3f}",
        ),
        MetricResult(
            "DELTA",
            direction,
            p50 - p60,
            None,
            None,
            n_bars,
            None,
            f"P≥50−P≥60 top={p50 - p60:.3f} rest={p50_r - p60_r:.3f}",
        ),
        MetricResult(
            "NEARMISS",
            direction,
            near_mass,
            None,
            None,
            n_bars,
            None,
            (
                f"top={near_mass:.3f} rest={near_r:.3f} "
                f"n_near={near_miss.height} "
                f"band=[{FLOOR_50_BPS:.0f},{FLOOR_60_BPS:.0f})"
            ),
        ),
        MetricResult(
            "NEARmix",
            direction,
            _share(near_miss["tb_label"] == 1) if near_miss.height else float("nan"),
            None,
            None,
            n_bars,
            None,
            f"near-miss under 60bps geometry: {near_exit}",
        ),
        MetricResult(
            "SLcontam",
            direction,
            sl_contam,
            None,
            None,
            n_bars,
            None,
            (
                f"among near-miss: P(t_SL≤t_MFE50)={sl_contam:.3f} "
                f"(clean=reach +50 before SL)"
            ),
        ),
        MetricResult(
            "PEAKbps",
            direction,
            peak_near_med,
            None,
            None,
            n_bars,
            None,
            (
                f"near med/mean={peak_near_med:.2f}/{peak_near_mean:.2f} "
                f"clear60 med/mean={peak_clear_med:.2f}/{peak_clear_mean:.2f}"
            ),
        ),
    ]

    cut_near = near_mass < HARD_STOP_NEAR_MISS_MIN
    cut_sl = (sl_contam > HARD_STOP_SL_CONTAM_MAX) if sl_contam == sl_contam else False
    cut_mfe = mfe_top < HARD_STOP_MEAN_MFE_MIN
    hard_stop = cut_near or cut_sl or cut_mfe
    fired = []
    if cut_near:
        fired.append(f"near<{HARD_STOP_NEAR_MISS_MIN}")
    if cut_sl:
        fired.append(f"SLcontam>{HARD_STOP_SL_CONTAM_MAX}")
    if cut_mfe:
        fired.append(f"MFEbps<{HARD_STOP_MEAN_MFE_MIN}")
    metrics.append(
        MetricResult(
            "HARDSTOP",
            direction,
            1.0 if hard_stop else 0.0,
            None,
            None,
            n_bars,
            hard_stop,
            (
                f"FIRED: {' OR '.join(fired)} -> STOP@0/1"
                if hard_stop
                else (
                    f"near={near_mass:.3f} SLcontam={sl_contam:.3f} "
                    f"MFEbps={mfe_top:.2f} (ok)"
                )
            ),
        )
    )
    return metrics


def evaluate_tp_floor(
    scored: pl.DataFrame,
    directions: list[str],
) -> list[MetricResult]:
    """Run Step 0 TP-floor crossing diagnostics for requested sleeves."""
    metrics: list[MetricResult] = []
    for direction in directions:
        metrics.extend(tp_floor_diagnostics(scored, direction))
    return metrics
