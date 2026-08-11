"""Tier 2 Horizon eval — constants, shared panel prep, and gated metrics."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from src.horizon.session import long_entry_ok_expr, short_entry_ok_expr
from src.labels.triple_barrier import ROUND_TRIP_COST
from src.regime.types import DailyRegime, IntradayRegime
from src.utils.eval_common import (
    H_BARS,
    MIN_BARS,
    MIN_SESSIONS,
    N_BOOT,
    MetricResult,
    format_report,
    session_block_mean_ci,
)

# Locked K (docs/horizon-tier2-eval-verdict.md) — Long matches Precision TOP_K.
K_LONG = 5
K_SHORT = 3

MIN_BARS_LONG = MIN_BARS
MIN_BARS_SHORT = 150
MIN_NAMES_PER_BAR = 5

# Null IC must not show spurious positive skill (H10).
H10_NULL_ABS_MAX = 0.02

# Eval-only flat-bar proxy for circuit / UC (D1 / H7). Not a training feature.
CIRCUIT_RANGE_EPS = 1e-4

# Diagnostic K-sweep only — never silently changes gated K_LONG / K_SHORT.
K_SWEEP = (3, 5, 8)

# S1 Short circuit/UC hygiene — measured FAIL on A+B (see v1.1 revision); leave off.
APPLY_S1_SHORT = False

# L1 Long inference-time rank-3 floor — measured FAIL dual-fold soft-H3; leave off.
APPLY_L1_LONG = False

_TRADEABLE_DAILY = (
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
)

_SLEEVE = {
    "long": {
        "intraday": IntradayRegime.TREND_UP.value,
        "valid_label": "valid_label_long",
        "entry_ok": long_entry_ok_expr,
        "tb_col": "tb_label_long",
    },
    "short": {
        "intraday": IntradayRegime.TREND_DOWN.value,
        "valid_label": "valid_label_short",
        "entry_ok": short_entry_ok_expr,
        "tb_col": "tb_label_short",
    },
}

# Polars dt.weekday: Monday=1 … Sunday=7 (ISO). Fold A/B era weekly expiry = Thursday.
_EXPIRY_WEEKDAY = 4


def min_bars_for(direction: str) -> int:
    return MIN_BARS_LONG if direction == "long" else MIN_BARS_SHORT


def k_for(direction: str) -> int:
    return K_LONG if direction == "long" else K_SHORT


def side_sign(direction: str) -> float:
    return 1.0 if direction == "long" else -1.0


def annotate_hygiene_flags(df: pl.DataFrame) -> pl.DataFrame:
    """
    Eval-only circuit / expiry flags on the full bar panel.

    Forward circuit look uses the next ``H_BARS`` same-session bars (diagnostic
    only — never a training feature). Idempotent if flags already present.
    """
    if {"is_circuit_bar", "fwd_circuit_hit", "is_expiry_day"}.issubset(df.columns):
        return df

    out = df
    if "date_only" not in out.columns:
        out = out.with_columns(date_only=pl.col("date").dt.date())
    if "range_pct" not in out.columns:
        out = out.with_columns(
            range_pct=(pl.col("high") - pl.col("low"))
            / pl.col("close").shift(1).over("symbol")
        )

    out = out.sort(["symbol", "date"]).with_columns(
        is_circuit_bar=(
            (pl.col("high") == pl.col("low"))
            | (
                pl.col("range_pct").is_not_null()
                & (pl.col("range_pct") <= CIRCUIT_RANGE_EPS)
            )
        ),
        # Thursday for 2018–2019 folds; post-2025 Tuesday change is OOS.
        is_expiry_day=pl.col("date").dt.weekday() == _EXPIRY_WEEKDAY,
    )

    shift_cols: list[pl.Expr] = []
    for h in range(1, H_BARS + 1):
        shift_cols.append(
            pl.col("is_circuit_bar").shift(-h).over("symbol").alias(f"_cir_{h}")
        )
        shift_cols.append(
            pl.col("date_only").shift(-h).over("symbol").alias(f"_d_{h}")
        )
    drop_cols = [f"_cir_{h}" for h in range(1, H_BARS + 1)] + [
        f"_d_{h}" for h in range(1, H_BARS + 1)
    ]
    return (
        out.with_columns(shift_cols)
        .with_columns(
            fwd_circuit_hit=pl.any_horizontal(
                [
                    pl.col(f"_cir_{h}").fill_null(False)
                    & (pl.col(f"_d_{h}") == pl.col("date_only"))
                    for h in range(1, H_BARS + 1)
                ]
            )
        )
        .drop(drop_cols)
    )


def eligible_expr(direction: str) -> pl.Expr:
    """Same sleeve mask as production predict + MIS-safe label + finite score/y."""
    cfg = _SLEEVE[direction]
    return (
        pl.col("daily_regime").is_in(list(_TRADEABLE_DAILY))
        & (pl.col("intraday_regime") == cfg["intraday"])
        & cfg["entry_ok"]("time_only")
        & pl.col(cfg["valid_label"])
        & pl.col("horizon_score").is_finite()
        & pl.col("fwd_excess_ret").is_finite()
    )


def prepare_eval_panel(scored: pl.DataFrame, direction: str) -> pl.DataFrame:
    """
    Cascade-valid scored rows with eval-only sign convention.

    ``eval_score`` is higher = more actionable for both sleeves (Short flips).
    ``adj_excess`` folds Short's "more negative = better" into the same scale.
    Rank is recomputed descending on ``eval_score`` within each bar (matches
    production Long descending / Short ascending after the flip).

    Short applies S1 circuit/UC hygiene when ``APPLY_S1_SHORT`` (v1.1).
    Long applies L1 rank-3 floor when ``APPLY_L1_LONG`` (v1.1).
    """
    # Local imports avoid cycle: common ↔ long_eval / short_eval.
    from src.horizon.eval.long_eval import apply_l1_rank3_floor
    from src.horizon.eval.short_eval import s1_circuit_ok_expr

    side = side_sign(direction)
    tb_col = _SLEEVE[direction]["tb_col"]

    base = annotate_hygiene_flags(scored)
    if "time_only" not in base.columns:
        base = base.with_columns(time_only=pl.col("date").dt.time())

    mask = eligible_expr(direction)
    if direction == "short" and APPLY_S1_SHORT:
        mask = mask & s1_circuit_ok_expr()

    panel = (
        base.filter(mask)
        .with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
            eval_score=pl.col("horizon_score") * side,
            adj_excess=pl.col("fwd_excess_ret") * side,
            tb_label=pl.col(tb_col),
            direction=pl.lit(direction),
        )
        .with_columns(
            eval_rank=pl.col("eval_score")
            .rank(method="ordinal", descending=True)
            .over("date")
        )
    )
    if direction == "long" and APPLY_L1_LONG:
        panel = apply_l1_rank3_floor(panel)
    return panel


def _mean_or_nan(series: pl.Series) -> float:
    m = series.mean()
    return float(m) if m is not None else float("nan")


def per_bar_ic(panel: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < MIN_NAMES_PER_BAR:
            continue
        ic, _ = spearmanr(
            g["eval_score"].to_numpy(),
            g["adj_excess"].to_numpy(),
        )
        if ic != ic:
            continue
        rows.append(
            {
                "date": bar,
                "date_only": g["date_only"][0],
                "ic": float(ic),
                "n_names": g.height,
            }
        )
    return pl.DataFrame(rows) if rows else pl.DataFrame(
        schema={
            "date": pl.Datetime,
            "date_only": pl.Date,
            "ic": pl.Float64,
            "n_names": pl.Int64,
        }
    )


def per_bar_topk_stats(panel: pl.DataFrame, k: int) -> pl.DataFrame:
    """Per-bar Top-K vs Rest spreads + TB rates + rank-tier means."""
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, k + 1):
            continue
        top = g.filter(pl.col("eval_rank") <= k)
        rest = g.filter(pl.col("eval_rank") > k)
        if rest.height == 0:
            continue

        adj_top = _mean_or_nan(top["adj_excess"])
        adj_rest = _mean_or_nan(rest["adj_excess"])
        spread = adj_top - adj_rest
        cost_spread = (adj_top - ROUND_TRIP_COST) - adj_rest

        r12 = g.filter(pl.col("eval_rank") <= 2)
        r3k = g.filter((pl.col("eval_rank") >= 3) & (pl.col("eval_rank") <= k))
        mean_12 = _mean_or_nan(r12["adj_excess"]) if r12.height else float("nan")
        mean_3k = _mean_or_nan(r3k["adj_excess"]) if r3k.height else float("nan")

        tb = g.filter(pl.col("tb_label").is_not_null())
        tb_top = tb.filter(pl.col("eval_rank") <= k)
        tb_rest = tb.filter(pl.col("eval_rank") > k)
        p_top = (
            _mean_or_nan(tb_top["tb_label"] == 1) if tb_top.height else float("nan")
        )
        p_rest = (
            _mean_or_nan(tb_rest["tb_label"] == 1) if tb_rest.height else float("nan")
        )
        p_all = _mean_or_nan(tb["tb_label"] == 1) if tb.height else float("nan")

        if not (
            np.isfinite(spread)
            and np.isfinite(cost_spread)
        ):
            continue

        rows.append(
            {
                "date": bar,
                "date_only": g["date_only"][0],
                "n_names": g.height,
                "spread": spread,
                "cost_spread": cost_spread,
                "mean_12": mean_12,
                "mean_3k": mean_3k,
                "mono_diff": mean_12 - mean_3k,
                "p_tb_top": p_top,
                "p_tb_rest": p_rest,
                "p_tb_all": p_all,
                "h5": p_top - p_rest,
                "n_tb_top": tb_top.height,
                "n_tb_rest": tb_rest.height,
            }
        )
    schema = {
        "date": pl.Datetime,
        "date_only": pl.Date,
        "n_names": pl.Int64,
        "spread": pl.Float64,
        "cost_spread": pl.Float64,
        "mean_12": pl.Float64,
        "mean_3k": pl.Float64,
        "mono_diff": pl.Float64,
        "p_tb_top": pl.Float64,
        "p_tb_rest": pl.Float64,
        "p_tb_all": pl.Float64,
        "h5": pl.Float64,
        "n_tb_top": pl.Int64,
        "n_tb_rest": pl.Int64,
    }
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema=schema)


def universe_parity_precondition(panel: pl.DataFrame, direction: str) -> MetricResult:
    """Binary: panel non-empty under the same sleeve mask as production predict."""
    n_bars = panel.select(pl.col("date").n_unique()).item() if panel.height else 0
    n_sessions = (
        panel.select(pl.col("date_only").n_unique()).item() if panel.height else 0
    )
    ok = panel.height > 0 and n_sessions > 0
    return MetricResult(
        "universe",
        direction,
        float(n_bars),
        None,
        None,
        int(panel.height),
        ok,
        f"sessions={n_sessions} bars={n_bars}",
    )


def h10_null_leakage(
    panel: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """
    Within-bar score shuffle → mean IC ≈ 0.

    FAIL if null IC CI lower bound > 0 (spurious skill) or |point| > H10_NULL_ABS_MAX.
    """
    if panel.height == 0:
        return MetricResult("H10", direction, None, None, None, 0, False, "empty")

    null_ics = []
    sessions = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < MIN_NAMES_PER_BAR:
            continue
        scores = g["eval_score"].to_numpy().copy()
        rng.shuffle(scores)
        ic, _ = spearmanr(scores, g["adj_excess"].to_numpy())
        if ic != ic:
            continue
        null_ics.append(float(ic))
        sessions.append(g["date_only"][0])

    n = len(null_ics)
    if n < MIN_SESSIONS:
        return MetricResult("H10", direction, None, None, None, n, False, "thin")

    values = np.asarray(null_ics, dtype=float)
    # Map sessions to integer ids for bootstrap.
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    ok = (ci_lo <= 0.0) and (abs(point) <= H10_NULL_ABS_MAX)
    return MetricResult(
        "H10",
        direction,
        point,
        ci_lo,
        ci_hi,
        n,
        ok,
        f"|null|<={H10_NULL_ABS_MAX}",
    )


def h1_spearman_ic(
    panel: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """Per-bar cross-sectional Spearman IC; session-block CI LB > 0 gates."""
    ic_df = per_bar_ic(panel)
    n = ic_df.height
    n_sessions = ic_df.select(pl.col("date_only").n_unique()).item() if n else 0
    min_bars = min_bars_for(direction)

    if n < min_bars or n_sessions < MIN_SESSIONS:
        return MetricResult(
            "H1",
            direction,
            None,
            None,
            None,
            n,
            False,
            f"thin bars={n} sess={n_sessions}",
        )

    values = ic_df["ic"].to_numpy()
    sessions = ic_df["date_only"].to_list()
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    return MetricResult(
        "H1",
        direction,
        point,
        ci_lo,
        ci_hi,
        n,
        ci_lo > 0.0,
        f"sess={n_sessions}",
    )


def h2_topk_spread(
    bar_stats: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """Top-K vs Rest raw adj_excess spread; CI LB > 0 gates."""
    n = bar_stats.height
    n_sessions = (
        bar_stats.select(pl.col("date_only").n_unique()).item() if n else 0
    )
    min_bars = min_bars_for(direction)
    k = k_for(direction)

    if n < min_bars or n_sessions < MIN_SESSIONS:
        return MetricResult(
            "H2",
            direction,
            None,
            None,
            None,
            n,
            False,
            f"thin K={k}",
        )

    values = bar_stats["spread"].to_numpy()
    sessions = bar_stats["date_only"].to_list()
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    return MetricResult(
        "H2",
        direction,
        point,
        ci_lo,
        ci_hi,
        n,
        ci_lo > 0.0,
        f"K={k} sess={n_sessions}",
    )


def h3_rank_monotonicity(
    bar_stats: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> MetricResult:
    """
    Rank 1–2 vs 3–K mean adj_excess.

    FAIL only on significant inversion: CI(diff) entirely below 0.
    """
    finite = bar_stats.filter(pl.col("mono_diff").is_finite())
    n = finite.height
    n_sessions = finite.select(pl.col("date_only").n_unique()).item() if n else 0
    min_bars = min_bars_for(direction)
    k = k_for(direction)

    if n < min_bars or n_sessions < MIN_SESSIONS:
        return MetricResult(
            "H3",
            direction,
            None,
            None,
            None,
            n,
            False,
            f"thin K={k}",
        )

    values = finite["mono_diff"].to_numpy()
    sessions = finite["date_only"].to_list()
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    # Significant inversion ⇒ CI entirely negative.
    inverted = ci_hi < 0.0
    mean_12 = float(finite["mean_12"].mean())
    mean_3k = float(finite["mean_3k"].mean())
    return MetricResult(
        "H3",
        direction,
        point,
        ci_lo,
        ci_hi,
        n,
        not inverted,
        f"m12={mean_12:.4f} m3k={mean_3k:.4f}",
    )


def h4_cost_netted_spread(bar_stats: pl.DataFrame, direction: str) -> MetricResult:
    """Diagnostic companion: Top-K cost-netted vs Rest (flat 30 bps)."""
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


def h5_stock_tb_bridge(
    bar_stats: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """StockTB+1 Top-K vs Rest (gated) + Top-K vs sleeve-average (diagnostic)."""
    finite = bar_stats.filter(
        pl.col("h5").is_finite()
        & (pl.col("n_tb_top") > 0)
        & (pl.col("n_tb_rest") > 0)
    )
    n = finite.height
    n_sessions = finite.select(pl.col("date_only").n_unique()).item() if n else 0
    min_bars = min_bars_for(direction)
    k = k_for(direction)
    results: list[MetricResult] = []

    if n < min_bars or n_sessions < MIN_SESSIONS:
        results.append(
            MetricResult(
                "H5",
                direction,
                None,
                None,
                None,
                n,
                False,
                f"thin K={k}",
            )
        )
        return results

    values = finite["h5"].to_numpy()
    sessions = finite["date_only"].to_list()
    sess_list = list(dict.fromkeys(sessions))
    sess_idx = {d: i for i, d in enumerate(sess_list)}
    session_ids = np.array([sess_idx[d] for d in sessions], dtype=int)
    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    p_top = float(finite["p_tb_top"].mean())
    p_rest = float(finite["p_tb_rest"].mean())
    results.append(
        MetricResult(
            "H5",
            direction,
            point,
            ci_lo,
            ci_hi,
            n,
            ci_lo > 0.0,
            f"p_top={p_top:.3f} p_rest={p_rest:.3f} K={k}",
        )
    )

    # Diagnostic: Top-K vs sleeve-average (Gemini marginal-value framing).
    vs_avg = finite.with_columns(
        h5_avg=pl.col("p_tb_top") - pl.col("p_tb_all")
    )
    avg_vals = vs_avg["h5_avg"].to_numpy()
    avg_point = float(avg_vals.mean())
    p_all = float(finite["p_tb_all"].mean())
    results.append(
        MetricResult(
            "H5avg",
            direction,
            avg_point,
            None,
            None,
            n,
            None,
            f"p_top={p_top:.3f} p_all={p_all:.3f}",
        )
    )
    return results


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


__all__ = [
    "H_BARS",
    "N_BOOT",
    "MIN_SESSIONS",
    "MIN_BARS",
    "MIN_BARS_LONG",
    "MIN_BARS_SHORT",
    "MIN_NAMES_PER_BAR",
    "H10_NULL_ABS_MAX",
    "CIRCUIT_RANGE_EPS",
    "K_SWEEP",
    "APPLY_S1_SHORT",
    "APPLY_L1_LONG",
    "K_LONG",
    "K_SHORT",
    "MetricResult",
    "format_report",
    "session_block_mean_ci",
    "min_bars_for",
    "k_for",
    "side_sign",
    "annotate_hygiene_flags",
    "eligible_expr",
    "prepare_eval_panel",
    "per_bar_ic",
    "per_bar_topk_stats",
    "universe_parity_precondition",
    "h10_null_leakage",
    "h1_spearman_ic",
    "h2_topk_spread",
    "h3_rank_monotonicity",
    "h4_cost_netted_spread",
    "h5_stock_tb_bridge",
    "h6_coverage",
    "h7_hygiene_diagnostics",
    "h9_calibration_diagnostics",
    "h9_k_sweep",
]
