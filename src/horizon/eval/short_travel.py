"""Short travel / ranking Step 0 — Top−Rest MFE, anti-selection, gated C1/C2 ρ."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from src.horizon.eval.constants import (
    MIN_NAMES_PER_BAR,
    MetricResult,
    k_for,
    min_bars_for,
    session_block_mean_ci,
)
from src.horizon.eval.panel import prepare_eval_panel
from src.horizon.eval.path_density import (
    adv_tercile_mfe_diagnostics,
    path_density_diagnostics,
)
from src.horizon.horizon_model import (
    L1_TRAVEL_FEATURE,
    SHORT_FEATURES,
    SHORT_S1B_C1,
    SHORT_S1B_C2,
    SHORT_S1B_CANDIDATES,
)
from src.labels.triple_barrier import TP_FLOOR_SHORT
from src.utils.eval_common import MIN_SESSIONS

# Charter locks (× Short TP floor units unless noted).
ANTI_SELECTION_GAP = 0.05  # Top ≤ Rest − 0.05×TP
RANK_TIER_GAP = 0.10  # rank-1 ≤ mean(2–3) − 0.10×TP
FEATURE_TRAVEL_RHO_MIN = 0.10
NONDUP_CORR_MAX = 0.70
ABS_MFE_HARDSTOP_FRAC = 0.70  # Top Abs MFE < 0.70×TP both folds → geometry stop
K2_MIN_TRADES = 150
SHORT_TP_BPS = TP_FLOOR_SHORT * 1e4  # 50

# Reject-list columns for S1b non-duplication (path-room may be absent).
_NONDUP_REJECT_COLS = (
    "stock_r_15",
    L1_TRAVEL_FEATURE,
    "tp_room_atr_short",
    "tp_room_atr_long",
    "sl_room_atr",
)

_EXTENSION_COLS = (
    "bounce_risk_zscore",
    "stock_r_15",
    "pct_from_52w_high",
    "downside_acceleration",
)


def _mean_or_nan(series: pl.Series) -> float:
    m = series.mean()
    return float(m) if m is not None else float("nan")


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


def attach_short_s1b_candidates(
    horizon_df: pl.DataFrame,
    lookback_days: int = 60,
) -> pl.DataFrame:
    """
    Eval/Step-0 attach for pre-registered S1b candidates (off SHORT_FEATURES).

    C1: causal same-clock mean of prior Short MFE / 50 bps floor.
    C2: causal z of (distance-to-session-low / TOD rv_15_mean).
    Also attaches Long L1 column when possible for non-duplication checks.
    """
    out = horizon_df
    if "date_only" not in out.columns:
        out = out.with_columns(date_only=pl.col("date").dt.date())
    if "time_only" not in out.columns:
        out = out.with_columns(time_only=pl.col("date").dt.time())

    min_periods = max(10, lookback_days // 4)

    # C1 — Short travel-adequacy (mfe_frac_short already / TP_FLOOR_SHORT=50bps).
    if SHORT_S1B_C1 not in out.columns:
        if "mfe_frac_short" not in out.columns:
            raise ValueError("attach_short_s1b_candidates requires mfe_frac_short")
        out = (
            out.sort(["symbol", "time_only", "date_only"])
            .with_columns(
                **{
                    SHORT_S1B_C1: pl.col("mfe_frac_short")
                    .shift(1)
                    .rolling_mean(window_size=lookback_days, min_samples=min_periods)
                    .over(["symbol", "time_only"])
                }
            )
            .sort(["symbol", "date"])
        )

    # Long L1 companion for non-duplication (not a Short default).
    if L1_TRAVEL_FEATURE not in out.columns and "mfe_frac_long" in out.columns:
        out = (
            out.sort(["symbol", "time_only", "date_only"])
            .with_columns(
                **{
                    L1_TRAVEL_FEATURE: pl.col("mfe_frac_long")
                    .shift(1)
                    .rolling_mean(window_size=lookback_days, min_samples=min_periods)
                    .over(["symbol", "time_only"])
                }
            )
            .sort(["symbol", "date"])
        )

    # C2 — unfinished downside room vs TOD rv (no path-room / barrier floors).
    if SHORT_S1B_C2 not in out.columns:
        for col in ("low", "close", "rv_15_mean"):
            if col not in out.columns:
                raise ValueError(f"attach_short_s1b_candidates requires {col}")
        out = (
            out.sort(["symbol", "date"])
            .with_columns(
                _session_low=pl.col("low").cum_min().over(["symbol", "date_only"]),
            )
            .with_columns(
                _downside_room=(pl.col("close") - pl.col("_session_low"))
                / pl.col("close"),
            )
            .with_columns(
                _room_rv=pl.col("_downside_room") / pl.col("rv_15_mean"),
            )
            .sort(["symbol", "time_only", "date_only"])
            .with_columns(
                _room_mean=pl.col("_room_rv")
                .shift(1)
                .rolling_mean(window_size=lookback_days, min_samples=min_periods)
                .over(["symbol", "time_only"]),
                _room_std=pl.col("_room_rv")
                .shift(1)
                .rolling_std(window_size=lookback_days, min_samples=min_periods)
                .over(["symbol", "time_only"]),
            )
            .with_columns(
                **{
                    SHORT_S1B_C2: (pl.col("_room_rv") - pl.col("_room_mean"))
                    / pl.col("_room_std")
                }
            )
            .drop(
                [
                    "_session_low",
                    "_downside_room",
                    "_room_rv",
                    "_room_mean",
                    "_room_std",
                ]
            )
            .sort(["symbol", "date"])
        )

    return out


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 30:
        return float("nan")
    rho, _ = spearmanr(x, y)
    return float(rho) if rho is not None and np.isfinite(rho) else float("nan")


def _feature_travel_rho(
    panel: pl.DataFrame,
    feature: str,
    target_col: str,
) -> tuple[float, int]:
    if feature not in panel.columns or target_col not in panel.columns:
        return float("nan"), 0
    ok = panel.filter(pl.col(feature).is_finite() & pl.col(target_col).is_finite())
    if ok.height < 30:
        return float("nan"), ok.height
    rho = _spearman(ok[feature].to_numpy(), ok[target_col].to_numpy())
    return rho, ok.height


def _nondup_pass(train_df: pl.DataFrame, candidate: str) -> tuple[bool, str]:
    if candidate not in train_df.columns:
        return False, "missing candidate"
    present = [c for c in _NONDUP_REJECT_COLS if c in train_df.columns]
    if not present:
        return True, "no reject cols present"
    notes = []
    ok = True
    for col in present:
        pair = train_df.filter(pl.col(candidate).is_finite() & pl.col(col).is_finite())
        if pair.height < 30:
            notes.append(f"{col}=thin")
            continue
        rho = _spearman(pair[candidate].to_numpy(), pair[col].to_numpy())
        notes.append(f"{col}={rho:.3f}")
        if np.isfinite(rho) and abs(rho) >= NONDUP_CORR_MAX:
            ok = False
    return ok, " ".join(notes)


def _per_bar_short_travel(panel: pl.DataFrame, k: int) -> pl.DataFrame:
    """Per-bar Top/Rest MFE + rank-1 vs ranks 2–3 + extension Top−Rest."""
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

        r1 = mfe_ok.filter(pl.col("eval_rank") == 1)
        r23 = mfe_ok.filter((pl.col("eval_rank") >= 2) & (pl.col("eval_rank") <= 3))
        tb_r1 = tb.filter(pl.col("eval_rank") == 1)
        tb_r23 = tb.filter((pl.col("eval_rank") >= 2) & (pl.col("eval_rank") <= 3))

        mfe_bps_ok = g.filter(pl.col("mfe_bps").is_finite()) if "mfe_bps" in g.columns else None
        top_bps = (
            mfe_bps_ok.filter(pl.col("eval_rank") <= k) if mfe_bps_ok is not None else None
        )
        rest_bps = (
            mfe_bps_ok.filter(pl.col("eval_rank") > k) if mfe_bps_ok is not None else None
        )

        row: dict = {
            "date": bar,
            "date_only": g["date_only"][0],
            "n_names": g.height,
            "mfe_top": _mean_or_nan(mfe_top["mfe_frac"]),
            "mfe_rest": _mean_or_nan(mfe_rest["mfe_frac"]),
            "mfe_spread": _mean_or_nan(mfe_top["mfe_frac"])
            - _mean_or_nan(mfe_rest["mfe_frac"]),
            "mfe_bps_top": (
                _mean_or_nan(top_bps["mfe_bps"]) if top_bps is not None else float("nan")
            ),
            "mfe_bps_rest": (
                _mean_or_nan(rest_bps["mfe_bps"])
                if rest_bps is not None
                else float("nan")
            ),
            "p_ge50_top": (
                float((top_bps["mfe_bps"] >= SHORT_TP_BPS).mean())
                if top_bps is not None and top_bps.height
                else float("nan")
            ),
            "p_tp_top": _mean_or_nan(tb_top["tb_label"] == 1),
            "p_sl_top": _mean_or_nan(tb_top["tb_label"] == -1),
            "p_to_top": _mean_or_nan(tb_top["tb_label"] == 0),
            "p_tp_rest": _mean_or_nan(tb_rest["tb_label"] == 1),
            "p_sl_rest": _mean_or_nan(tb_rest["tb_label"] == -1),
            "p_to_rest": _mean_or_nan(tb_rest["tb_label"] == 0),
            "tp_spread": _mean_or_nan(tb_top["tb_label"] == 1)
            - _mean_or_nan(tb_rest["tb_label"] == 1),
            "mfe_r1": _mean_or_nan(r1["mfe_frac"]) if r1.height else float("nan"),
            "mfe_r23": _mean_or_nan(r23["mfe_frac"]) if r23.height else float("nan"),
            "p_tp_r1": (
                _mean_or_nan(tb_r1["tb_label"] == 1) if tb_r1.height else float("nan")
            ),
            "p_tp_r23": (
                _mean_or_nan(tb_r23["tb_label"] == 1) if tb_r23.height else float("nan")
            ),
            "n_top_k2": g.filter(pl.col("eval_rank") <= 2).height,
        }
        for col in _EXTENSION_COLS:
            if col not in g.columns:
                row[f"ext_{col}"] = float("nan")
                continue
            ok = g.filter(pl.col(col).is_finite())
            top_e = ok.filter(pl.col("eval_rank") <= k)
            rest_e = ok.filter(pl.col("eval_rank") > k)
            if top_e.height == 0 or rest_e.height == 0:
                row[f"ext_{col}"] = float("nan")
            else:
                row[f"ext_{col}"] = _mean_or_nan(top_e[col]) - _mean_or_nan(rest_e[col])
        rows.append(row)

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def short_travel_diagnostics(
    scored: pl.DataFrame,
    train_df: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """
    Short-primary Step 0 readout (Long may call path_density companion separately).

    Emits SEP reconfirm, anti-selection, Abs MFE, exit mix, rank-tier, extension
    Top−Rest, gated C1/C2 ρ + non-duplication, report-only SHORT_FEATURES ρ,
    ADV, and K=2 trade count.
    """
    if direction != "short":
        return path_density_diagnostics(scored, direction, n_boot, rng)

    panel = prepare_eval_panel(scored, direction)
    k = k_for(direction)
    metrics: list[MetricResult] = []

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

    bar_stats = _per_bar_short_travel(panel, k)

    # --- SEP reconfirm (same CI rule as path-density) ---
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
    mean_mfe_top = (
        float(bar_stats["mfe_top"].mean()) if bar_stats.height else float("nan")
    )
    mean_mfe_rest = (
        float(bar_stats["mfe_rest"].mean()) if bar_stats.height else float("nan")
    )
    metrics.append(
        MetricResult(
            "MFEabs",
            direction,
            mean_mfe_top,
            None,
            None,
            bar_stats.height,
            None,
            f"top={mean_mfe_top:.3f} rest={mean_mfe_rest:.3f}",
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

    # --- Anti-selection: Top ≤ Rest − 0.05×TP ---
    anti_gap = mean_mfe_top - mean_mfe_rest
    anti_fire = bool(np.isfinite(anti_gap) and anti_gap <= -ANTI_SELECTION_GAP)
    metrics.append(
        MetricResult(
            "ANTI",
            direction,
            anti_gap,
            None,
            None,
            bar_stats.height,
            anti_fire,
            (
                f"Top-Rest={anti_gap:.3f}; cut<=-{ANTI_SELECTION_GAP:.2f} "
                f"{'FIRE' if anti_fire else 'no'}"
            ),
        )
    )

    # --- Abs MFE bps + P(≥50) ---
    mean_bps_top = (
        float(bar_stats["mfe_bps_top"].mean()) if bar_stats.height else float("nan")
    )
    mean_bps_rest = (
        float(bar_stats["mfe_bps_rest"].mean()) if bar_stats.height else float("nan")
    )
    p_ge50 = (
        float(bar_stats["p_ge50_top"].mean()) if bar_stats.height else float("nan")
    )
    metrics.append(
        MetricResult(
            "MFEbps",
            direction,
            mean_bps_top,
            None,
            None,
            bar_stats.height,
            None,
            (
                f"top={mean_bps_top:.2f} rest={mean_bps_rest:.2f} bps "
                f"P(>=50)={p_ge50:.3f} floor={SHORT_TP_BPS:.0f}"
            ),
        )
    )
    geom_stop = bool(
        np.isfinite(mean_bps_top) and mean_bps_top < ABS_MFE_HARDSTOP_FRAC * SHORT_TP_BPS
    )
    metrics.append(
        MetricResult(
            "GEOMSTOP",
            direction,
            mean_bps_top / SHORT_TP_BPS if np.isfinite(mean_bps_top) else None,
            None,
            None,
            bar_stats.height,
            geom_stop,
            (
                f"Top Abs MFE {mean_bps_top:.1f}bps / {SHORT_TP_BPS:.0f} "
                f"< {ABS_MFE_HARDSTOP_FRAC:.2f}x -> {'FIRE' if geom_stop else 'ok'}"
            ),
        )
    )

    # --- Rank tier: rank-1 vs mean(2–3) ---
    tier = bar_stats.filter(pl.col("mfe_r1").is_finite() & pl.col("mfe_r23").is_finite())
    if tier.height:
        gap = float((tier["mfe_r1"] - tier["mfe_r23"]).mean())
        sk_gap_fire = gap <= -RANK_TIER_GAP
        metrics.append(
            MetricResult(
                "RANKtier",
                direction,
                gap,
                None,
                None,
                tier.height,
                sk_gap_fire,
                (
                    f"r1={float(tier['mfe_r1'].mean()):.3f} "
                    f"r23={float(tier['mfe_r23'].mean()):.3f} "
                    f"tp_r1={float(tier['p_tp_r1'].mean()):.3f} "
                    f"tp_r23={float(tier['p_tp_r23'].mean()):.3f} "
                    f"cut<=-{RANK_TIER_GAP:.2f} {'FIRE' if sk_gap_fire else 'no'}"
                ),
            )
        )
    else:
        sk_gap_fire = False
        metrics.append(
            MetricResult(
                "RANKtier", direction, None, None, None, 0, False, "empty tier"
            )
        )

    k2_trades = int(bar_stats["n_top_k2"].sum()) if bar_stats.height else 0
    k2_ok = k2_trades >= K2_MIN_TRADES
    metrics.append(
        MetricResult(
            "K2n",
            direction,
            float(k2_trades),
            None,
            None,
            bar_stats.height,
            k2_ok,
            f"holdout Top-K=2 trades={k2_trades} min={K2_MIN_TRADES}",
        )
    )
    sk_fire = bool(sk_gap_fire and k2_ok)
    metrics.append(
        MetricResult(
            "SKcut",
            direction,
            1.0 if sk_fire else 0.0,
            None,
            None,
            bar_stats.height,
            sk_fire,
            (
                "rank-tier gap + K2 min-N -> S-K authorized"
                if sk_fire
                else "S-K numeric cut not met"
            ),
        )
    )

    # --- Extension / bounce Top−Rest ---
    for col in _EXTENSION_COLS:
        ext_col = f"ext_{col}"
        if bar_stats.height == 0 or ext_col not in bar_stats.columns:
            metrics.append(
                MetricResult(
                    f"EXT_{col[:8]}",
                    direction,
                    None,
                    None,
                    None,
                    0,
                    None,
                    "missing",
                )
            )
            continue
        val = float(bar_stats[ext_col].mean())
        metrics.append(
            MetricResult(
                f"EXT_{col[:8]}",
                direction,
                val,
                None,
                None,
                bar_stats.height,
                None,
                f"Top-Rest mean {col}",
            )
        )

    # --- Gated C1/C2 feature→travel ---
    for cand in SHORT_S1B_CANDIDATES:
        rho, n_rho = _feature_travel_rho(panel, cand, "mfe_bps")
        nondup_ok, nondup_note = _nondup_pass(train_df, cand)
        rho_ok = bool(np.isfinite(rho) and abs(rho) >= FEATURE_TRAVEL_RHO_MIN)
        clear = rho_ok and nondup_ok
        tag = "C1" if cand == SHORT_S1B_C1 else "C2"
        metrics.append(
            MetricResult(
                f"RHO_{tag}",
                direction,
                rho if np.isfinite(rho) else None,
                None,
                None,
                n_rho,
                clear,
                (
                    f"|rho| vs AbsMFE; nondup={'pass' if nondup_ok else 'FAIL'} "
                    f"({nondup_note}); "
                    f"bar |rho|>={FEATURE_TRAVEL_RHO_MIN:.2f} "
                    f"{'CLEAR' if clear else 'no'}"
                ),
            )
        )

    # --- Report-only SHORT_FEATURES ρ vs Abs MFE / StockTB ---
    for feat in SHORT_FEATURES:
        rho_mfe, n_m = _feature_travel_rho(panel, feat, "mfe_bps")
        rho_tb, n_t = _feature_travel_rho(panel, feat, "tb_label")
        metrics.append(
            MetricResult(
                f"rF_{feat[:10]}",
                direction,
                rho_mfe if np.isfinite(rho_mfe) else None,
                None,
                None,
                n_m,
                None,
                (
                    f"{feat} holdout rho_MFE={rho_mfe:.3f} rho_TB={rho_tb:.3f} "
                    f"n={n_m}/{n_t} (report-only)"
                ),
            )
        )

    metrics.extend(adv_tercile_mfe_diagnostics(panel, direction))
    return metrics


def evaluate_short_travel(
    scored: pl.DataFrame,
    train_df: pl.DataFrame,
    directions: list[str],
    n_boot: int,
    seed: int,
) -> list[MetricResult]:
    """Run Step 0 diagnostics; Short gets full travel suite, Long = path-density."""
    rng = np.random.default_rng(seed)
    metrics: list[MetricResult] = []
    for direction in directions:
        metrics.extend(
            short_travel_diagnostics(scored, train_df, direction, n_boot, rng)
        )
    return metrics


def summarize_hard_gate(fold_metrics: dict[str, list[MetricResult]]) -> dict:
    """
    Cross-fold hard-stop + implication (Short only).

    Returns a decision dict used by the CLI summary / stop-memo.
    """
    folds = sorted(fold_metrics.keys())

    def _vals(name: str) -> list[MetricResult]:
        out = []
        for f in folds:
            out.extend(
                m
                for m in fold_metrics[f]
                if m.name == name and m.side == "short"
            )
        return out

    sep = _vals("SEP")
    anti = _vals("ANTI")
    geom = _vals("GEOMSTOP")
    sk = _vals("SKcut")
    rho_c1 = _vals("RHO_C1")
    rho_c2 = _vals("RHO_C2")

    sep_fail_all = bool(sep) and all(not m.gate_pass for m in sep)
    anti_both = bool(anti) and len(anti) >= 2 and all(bool(m.gate_pass) for m in anti)
    anti_any = any(bool(m.gate_pass) for m in anti)
    geom_both = bool(geom) and len(geom) >= 2 and all(bool(m.gate_pass) for m in geom)
    sk_both = bool(sk) and len(sk) >= 2 and all(bool(m.gate_pass) for m in sk)

    def _rho_sign_consistent(ms: list[MetricResult]) -> bool:
        if len(ms) < 2:
            return False
        vals = [m.value for m in ms if m.value is not None and np.isfinite(m.value)]
        if len(vals) < 2:
            return False
        if not all(abs(v) >= FEATURE_TRAVEL_RHO_MIN for v in vals):
            return False
        # Sign-consistent and non-duplication already baked into gate_pass.
        signs = [np.sign(v) for v in vals]
        return all(s == signs[0] and s != 0 for s in signs) and all(
            bool(m.gate_pass) for m in ms
        )

    c1_clear = _rho_sign_consistent(rho_c1)
    c2_clear = _rho_sign_consistent(rho_c2)

    # Hard-stop OR cuts.
    hard_stop = False
    hard_reasons: list[str] = []
    if geom_both:
        hard_stop = True
        hard_reasons.append("Abs Top-K MFE < 0.70×TP both folds (geometry)")

    novel_signal = anti_both or c1_clear or c2_clear or sk_both
    if sep_fail_all and not anti_any and not c1_clear and not c2_clear and not sk_both:
        hard_stop = True
        hard_reasons.append(
            "SEP FAIL + no anti-selection + no C1/C2 ρ + no S-K (nothing novel)"
        )

    authorized: list[str] = []
    if not hard_stop:
        if anti_both:
            authorized.append("S1a")
        if c1_clear or c2_clear:
            # Higher |ρ| wins if both clear.
            if c1_clear and c2_clear:
                m1 = np.mean([abs(m.value) for m in rho_c1 if m.value is not None])
                m2 = np.mean([abs(m.value) for m in rho_c2 if m.value is not None])
                authorized.append("S1b_C1" if m1 >= m2 else "S1b_C2")
            elif c1_clear:
                authorized.append("S1b_C1")
            else:
                authorized.append("S1b_C2")
        if sk_both:
            authorized.append("S-K")
        # Tie-break order S1a → S1b → S-K already preserved by append order.

    return {
        "folds": folds,
        "hard_stop": hard_stop,
        "hard_reasons": hard_reasons,
        "novel_signal": novel_signal,
        "authorized": authorized,
        "sep_fail_all": sep_fail_all,
        "anti_both": anti_both,
        "c1_clear": c1_clear,
        "c2_clear": c2_clear,
        "sk_both": sk_both,
        "geom_both": geom_both,
        "rho_c1": [m.value for m in rho_c1],
        "rho_c2": [m.value for m in rho_c2],
        "anti_gaps": [m.value for m in anti],
        "sk_gates": [bool(m.gate_pass) for m in sk],
    }
