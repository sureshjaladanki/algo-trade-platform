"""AUDIT-ONLY (fresh M0 quarantine) — Horizon admission Step 0.

See docs/archive/horizon-fresh-quarantine-index.md. Do not grow peeks on
production Top-K under fresh naming. Live gates remain in eval/__init__.py.
"""

from __future__ import annotations

from typing import Any

import lightgbm as lgb
import numpy as np
import polars as pl
from sklearn.calibration import calibration_curve

from src.horizon.eval.bar_stats import per_bar_topk_stats
from src.horizon.eval.constants import (
    MIN_NAMES_PER_BAR,
    MetricResult,
    k_for,
    min_bars_for,
)
from src.horizon.eval.diagnostics import h4_cost_netted_spread
from src.horizon.eval.gates import (
    h1_spearman_ic,
    h2_topk_spread,
    h3_rank_monotonicity,
    h5_stock_tb_bridge,
    h10_null_leakage,
    universe_parity_precondition,
)
from src.horizon.eval.panel import prepare_eval_panel
from src.horizon.eval.path_density import path_density_diagnostics
from src.horizon.horizon_model import (
    DEFAULT_EMBARGO_DAYS,
    LONG_FEATURES,
    LONG_PARAMS,
    episode_balanced_weights,
    get_purged_cv_splits,
)
from src.pipelines.horizon_pipeline import SLEEVES, _fit_sleeve_mask
from src.utils.eval_common import MIN_SESSIONS, session_block_mean_ci

# Report-only conviction candidates — lock ONE before Peek 1 (no A+B grid).
SCORE_FLOOR_QUANTS = (0.70, 0.80, 0.90)
DEFAULT_CONVICTION_QUANTILE = 0.80

# Multiclass TB head: SL=0, TO=1, TP=2 (relative veto; never absolute P(TP)>0.6 gate).
_TB_CLASS_SL = 0
_TB_CLASS_TO = 1
_TB_CLASS_TP = 2
_N_TB_CLASSES = 3
_VETO_SEED = 42
_ECE_BINS = 10

# A2 coverage kill-switch floors — pre-register from Step 0 before Peek 1.
# Conservative: half of baseline Top-K bar count, floored at harness mins.
A2_MIN_BARS_FRAC = 0.50
A2_MIN_SESS_FRAC = 0.50


def _mean_or_nan(series: pl.Series) -> float:
    m = series.mean()
    return float(m) if m is not None else float("nan")


def _tb_class_expr(tb_col: str = "tb_label_long") -> pl.Expr:
    return (
        pl.when(pl.col(tb_col) == -1)
        .then(_TB_CLASS_SL)
        .when(pl.col(tb_col) == 0)
        .then(_TB_CLASS_TO)
        .when(pl.col(tb_col) == 1)
        .then(_TB_CLASS_TP)
        .otherwise(None)
        .cast(pl.Int32)
        .alias("tb_class")
    )


def _multiclass_params() -> dict[str, Any]:
    base = {
        k: v
        for k, v in LONG_PARAMS.items()
        if k not in ("objective", "alpha", "metric")
    }
    return {
        **base,
        "objective": "multiclass",
        "num_class": _N_TB_CLASSES,
        "metric": "multi_logloss",
        "random_state": _VETO_SEED,
    }


def prepare_long_sleeve_tb(
    df: pl.DataFrame, features: list[str] | None = None
) -> tuple[pl.DataFrame, list[str]]:
    """Cascade-valid Long rows with TB class label for veto-head fit."""
    cfg = SLEEVES["long"]
    feat_list = list(features) if features is not None else list(LONG_FEATURES)
    drop_cols = feat_list + ["tb_class"]
    sleeve = (
        df.filter(_fit_sleeve_mask(cfg) & pl.col(cfg.eligible_col))
        .with_columns(_tb_class_expr("tb_label_long"))
        .drop_nulls(subset=drop_cols)
        .filter(pl.col("tb_class").is_in([_TB_CLASS_SL, _TB_CLASS_TO, _TB_CLASS_TP]))
    )
    if "date_only" not in sleeve.columns:
        sleeve = sleeve.with_columns(date_only=pl.col("date").dt.date())
    return sleeve, feat_list


def fit_veto_last_fold(
    train_df: pl.DataFrame,
) -> tuple[lgb.LGBMClassifier | None, pl.DataFrame | None, dict]:
    """
    Last purged fold multiclass TB head + same-fold path-EV ranks on val.

    Val carries p_sl/p_to/p_tp, veto_y, eval_rank for Top-K vs Rest separation.
    Not a peek; never trains the path-EV ranker on admission survivors.
    """
    from src.horizon.horizon_model import GBMHorizonModel
    from src.pipelines.horizon_pipeline import _path_ev_target

    sleeve, feat_list = prepare_long_sleeve_tb(train_df)
    if sleeve.height == 0:
        return None, None, {"n_splits": 0, "reason": "empty sleeve"}

    calendar_dates = (
        train_df.select("date_only").unique().sort("date_only").to_series().to_list()
        if "date_only" in train_df.columns
        else sleeve.select("date_only").unique().sort("date_only").to_series().to_list()
    )
    # Path-EV sleeve on same calendar (for ranks on val).
    cfg = SLEEVES["long"]
    path_sleeve = (
        train_df.filter(_fit_sleeve_mask(cfg) & pl.col(cfg.eligible_col))
        .with_columns(_path_ev_target(cfg))
        .drop_nulls(subset=feat_list + ["path_ev_y"])
        .filter(pl.col("path_ev_y").is_finite())
    )
    if "date_only" not in path_sleeve.columns:
        path_sleeve = path_sleeve.with_columns(date_only=pl.col("date").dt.date())

    splits = get_purged_cv_splits(
        sleeve, calendar_dates=calendar_dates, embargo_days=DEFAULT_EMBARGO_DAYS
    )
    if not splits:
        return None, None, {"n_splits": 0, "reason": "no purged splits"}

    fold_train, fold_val, _fold_test = splits[-1]
    if min(fold_train.height, fold_val.height) == 0:
        return None, None, {"n_splits": 0, "reason": "empty last fold"}

    model = lgb.LGBMClassifier(**_multiclass_params())
    X_tr = fold_train.select(feat_list).to_numpy()
    y_tr = fold_train["tb_class"].to_numpy()
    X_va = fold_val.select(feat_list).to_numpy()
    y_va = fold_val["tb_class"].to_numpy()
    w_tr = episode_balanced_weights(fold_train)
    model.fit(
        X_tr,
        y_tr,
        sample_weight=w_tr,
        eval_X=X_va,
        eval_y=y_va,
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
    )

    proba = model.predict_proba(X_va)
    classes = list(model.classes_)
    col_map = {int(c): i for i, c in enumerate(classes)}
    p_sl = (
        proba[:, col_map[_TB_CLASS_SL]]
        if _TB_CLASS_SL in col_map
        else np.zeros(len(y_va))
    )
    p_to = (
        proba[:, col_map[_TB_CLASS_TO]]
        if _TB_CLASS_TO in col_map
        else np.zeros(len(y_va))
    )
    p_tp = (
        proba[:, col_map[_TB_CLASS_TP]]
        if _TB_CLASS_TP in col_map
        else np.zeros(len(y_va))
    )

    val = fold_val.with_columns(
        p_sl=pl.Series(p_sl),
        p_to=pl.Series(p_to),
        p_tp=pl.Series(p_tp),
        veto_y=pl.Series(y_va.astype(np.int32)),
    )

    # Same-window path-EV ranks so Top-K vs Rest is not a holdout peek.
    train_dates = fold_train["date_only"].unique().to_list()
    val_dates = fold_val["date_only"].unique().to_list()
    path_train = path_sleeve.filter(pl.col("date_only").is_in(train_dates))
    path_val = path_sleeve.filter(pl.col("date_only").is_in(val_dates))
    if min(path_train.height, path_val.height) > 0:
        path_model = GBMHorizonModel(direction="long")
        path_model.fit(
            X_train=path_train,
            y_train=path_train["path_ev_y"],
            X_val=path_val,
            y_val=path_val["path_ev_y"],
            features=feat_list,
            train_weight=episode_balanced_weights(path_train),
        )
        scores = path_model.predict(path_val)
        path_ranked = (
            path_val.with_columns(horizon_score=pl.Series(scores))
            .with_columns(
                eval_rank=pl.col("horizon_score")
                .rank(method="ordinal", descending=True)
                .over("date")
            )
            .select(["symbol", "date", "eval_rank", "horizon_score"])
        )
        val = val.join(path_ranked, on=["symbol", "date"], how="left")

    stats = {
        "n_splits": len(splits),
        "train_bars": fold_train.height,
        "val_bars": fold_val.height,
        "features": feat_list,
    }
    return model, val, stats


def _ece_binary(y_true: np.ndarray, probs: np.ndarray, n_bins: int = _ECE_BINS) -> float:
    """Expected calibration error for a binary event (here: TP class)."""
    if y_true.size == 0 or not np.isfinite(probs).all():
        return float("nan")
    # sklearn returns (fraction_of_positives, mean_predicted_value) per bin with samples.
    try:
        frac_pos, mean_pred = calibration_curve(
            y_true, probs, n_bins=n_bins, strategy="quantile"
        )
    except ValueError:
        return float("nan")
    # Weight bins equally among returned bins (quantile strategy → roughly equal mass).
    return float(np.mean(np.abs(frac_pos - mean_pred))) if len(frac_pos) else float("nan")


def per_bar_score_floors(panel: pl.DataFrame, k: int) -> pl.DataFrame:
    """Per-bar eligible score quantiles + Top-K mass below each candidate floor."""
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, k + 1):
            continue
        scores = g["eval_score"].to_numpy()
        if not np.isfinite(scores).all():
            continue
        top = g.filter(pl.col("eval_rank") <= k)
        if top.height == 0:
            continue
        top_scores = top["eval_score"].to_numpy()
        row: dict[str, Any] = {
            "date": bar,
            "date_only": g["date_only"][0],
            "n_names": g.height,
            "n_top": top.height,
            "score_p50": float(np.quantile(scores, 0.50)),
            "score_p70": float(np.quantile(scores, 0.70)),
            "score_p80": float(np.quantile(scores, 0.80)),
            "score_p90": float(np.quantile(scores, 0.90)),
        }
        for q in SCORE_FLOOR_QUANTS:
            floor = float(np.quantile(scores, q))
            frac_below = float(np.mean(top_scores < floor))
            tag = int(q * 100)
            row[f"floor_p{tag}"] = floor
            row[f"topk_below_p{tag}"] = frac_below
        rows.append(row)

    schema = {
        "date": pl.Datetime,
        "date_only": pl.Date,
        "n_names": pl.Int64,
        "n_top": pl.Int64,
        "score_p50": pl.Float64,
        "score_p70": pl.Float64,
        "score_p80": pl.Float64,
        "score_p90": pl.Float64,
        "floor_p70": pl.Float64,
        "topk_below_p70": pl.Float64,
        "floor_p80": pl.Float64,
        "topk_below_p80": pl.Float64,
        "floor_p90": pl.Float64,
        "topk_below_p90": pl.Float64,
    }
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema=schema)


def per_bar_rank_tier_refresh(panel: pl.DataFrame, k: int) -> pl.DataFrame:
    """Ranks 1–2 vs 3–K: MFE / exit-mix / TB+1 (path-density inversion refresh)."""
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, k + 1):
            continue
        mfe_ok = g.filter(pl.col("mfe_frac").is_finite())
        tb = g.filter(pl.col("tb_label").is_not_null())
        r12 = mfe_ok.filter(pl.col("eval_rank") <= 2)
        r3k = mfe_ok.filter((pl.col("eval_rank") >= 3) & (pl.col("eval_rank") <= k))
        tb12 = tb.filter(pl.col("eval_rank") <= 2)
        tb3k = tb.filter((pl.col("eval_rank") >= 3) & (pl.col("eval_rank") <= k))
        if min(r12.height, r3k.height, tb12.height, tb3k.height) == 0:
            continue
        rows.append(
            {
                "date": bar,
                "date_only": g["date_only"][0],
                "mfe_12": _mean_or_nan(r12["mfe_frac"]),
                "mfe_3k": _mean_or_nan(r3k["mfe_frac"]),
                "p_tp_12": _mean_or_nan(tb12["tb_label"] == 1),
                "p_tp_3k": _mean_or_nan(tb3k["tb_label"] == 1),
                "p_sl_12": _mean_or_nan(tb12["tb_label"] == -1),
                "p_sl_3k": _mean_or_nan(tb3k["tb_label"] == -1),
                "p_to_12": _mean_or_nan(tb12["tb_label"] == 0),
                "p_to_3k": _mean_or_nan(tb3k["tb_label"] == 0),
            }
        )
    schema = {
        "date": pl.Datetime,
        "date_only": pl.Date,
        "mfe_12": pl.Float64,
        "mfe_3k": pl.Float64,
        "p_tp_12": pl.Float64,
        "p_tp_3k": pl.Float64,
        "p_sl_12": pl.Float64,
        "p_sl_3k": pl.Float64,
        "p_to_12": pl.Float64,
        "p_to_3k": pl.Float64,
    }
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema=schema)


def apply_conviction_floor(
    panel: pl.DataFrame, quantile: float, k: int | None = None
) -> pl.DataFrame:
    """
    Inference-only admission: Top-K ∩ score ≥ per-bar eligible quantile floor.

    Adds ``admitted`` (bool), ``rejected_topk`` (in Top-K but below floor),
    and ``floor_score``. Does not retrain 2a.
    """
    k_eff = k_for("long") if k is None else k
    floors = (
        panel.group_by("date", maintain_order=True)
        .agg(
            floor_score=pl.col("eval_score").quantile(quantile),
        )
    )
    out = panel.join(floors, on="date", how="left")
    return out.with_columns(
        admitted=(pl.col("eval_rank") <= k_eff)
        & (pl.col("eval_score") >= pl.col("floor_score")),
        rejected_topk=(pl.col("eval_rank") <= k_eff)
        & (pl.col("eval_score") < pl.col("floor_score")),
    )


def per_bar_admission_contrast(panel: pl.DataFrame) -> pl.DataFrame:
    """Per-bar StockTB+1 admitted vs rejected-from-Top-K (A1 primary)."""
    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        adm = g.filter(pl.col("admitted") & pl.col("tb_label").is_not_null())
        rej = g.filter(pl.col("rejected_topk") & pl.col("tb_label").is_not_null())
        if adm.height == 0:
            continue
        p_adm = _mean_or_nan(adm["tb_label"] == 1)
        if rej.height == 0:
            # No reject mass this bar — skip contrast (cannot form A1 pair).
            continue
        p_rej = _mean_or_nan(rej["tb_label"] == 1)
        rest = g.filter((~pl.col("admitted")) & pl.col("tb_label").is_not_null())
        p_rest = _mean_or_nan(rest["tb_label"] == 1) if rest.height else float("nan")
        rows.append(
            {
                "date": bar,
                "date_only": g["date_only"][0],
                "n_admitted": adm.height,
                "n_rejected": rej.height,
                "p_tb_adm": p_adm,
                "p_tb_rej": p_rej,
                "a1": p_adm - p_rej,
                "h5_adm": p_adm - p_rest if np.isfinite(p_rest) else float("nan"),
                "p_tb_rest": p_rest,
            }
        )
    schema = {
        "date": pl.Datetime,
        "date_only": pl.Date,
        "n_admitted": pl.Int64,
        "n_rejected": pl.Int64,
        "p_tb_adm": pl.Float64,
        "p_tb_rej": pl.Float64,
        "a1": pl.Float64,
        "h5_adm": pl.Float64,
        "p_tb_rest": pl.Float64,
    }
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema=schema)


def _ci_on_col(
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
        name, direction, point, ci_lo, ci_hi, n, ci_lo > 0.0, note
    )


def score_floor_diagnostics(
    panel: pl.DataFrame, direction: str
) -> list[MetricResult]:
    """Report-only: eligible score quantiles + Top-K fraction below P70/P80/P90."""
    k = k_for(direction)
    floors = per_bar_score_floors(panel, k)
    if floors.height == 0:
        return [
            MetricResult(
                "SCOREq", direction, None, None, None, 0, None, "empty floor table"
            )
        ]
    metrics: list[MetricResult] = [
        MetricResult(
            "SCOREq",
            direction,
            float(floors["score_p80"].mean()),
            None,
            None,
            floors.height,
            None,
            (
                f"elig p50/p70/p80/p90="
                f"{float(floors['score_p50'].mean()):.4f}/"
                f"{float(floors['score_p70'].mean()):.4f}/"
                f"{float(floors['score_p80'].mean()):.4f}/"
                f"{float(floors['score_p90'].mean()):.4f}"
            ),
        )
    ]
    for q in SCORE_FLOOR_QUANTS:
        tag = int(q * 100)
        col = f"topk_below_p{tag}"
        metrics.append(
            MetricResult(
                f"FLOORp{tag}",
                direction,
                float(floors[col].mean()),
                None,
                None,
                floors.height,
                None,
                f"mean frac Top-K score < bar P{tag} (report-only; do not tune)",
            )
        )
    return metrics


def rank_tier_refresh_diagnostics(
    panel: pl.DataFrame, direction: str
) -> list[MetricResult]:
    """Ranks 1–2 vs 3–K MFE / TB+1 / exit mix — K-authorization input."""
    k = k_for(direction)
    tier = per_bar_rank_tier_refresh(panel, k)
    if tier.height == 0:
        return [
            MetricResult(
                "RANKtier", direction, None, None, None, 0, None, "empty tier table"
            )
        ]
    mfe_spread = float((tier["mfe_12"] - tier["mfe_3k"]).mean())
    tp_spread = float((tier["p_tp_12"] - tier["p_tp_3k"]).mean())
    # Sharp decay favoring narrower K only if ranks 1–2 beat 3–K on MFE (not inverted).
    k_implicated = mfe_spread > 0.05
    return [
        MetricResult(
            "RANKtier",
            direction,
            mfe_spread,
            None,
            None,
            tier.height,
            None,
            (
                f"mfe_12={float(tier['mfe_12'].mean()):.3f} "
                f"mfe_3k={float(tier['mfe_3k'].mean()):.3f} "
                f"tp_12={float(tier['p_tp_12'].mean()):.3f} "
                f"tp_3k={float(tier['p_tp_3k'].mean()):.3f} "
                f"sl_12/3k={float(tier['p_sl_12'].mean()):.3f}/"
                f"{float(tier['p_sl_3k'].mean()):.3f} "
                f"to_12/3k={float(tier['p_to_12'].mean()):.3f}/"
                f"{float(tier['p_to_3k'].mean()):.3f} "
                f"K_implicated={k_implicated}"
            ),
        ),
        MetricResult(
            "RANKtp",
            direction,
            tp_spread,
            None,
            None,
            tier.height,
            None,
            "tp_12 - tp_3k (report)",
        ),
        MetricResult(
            "Kimplic",
            direction,
            1.0 if k_implicated else 0.0,
            None,
            None,
            tier.height,
            k_implicated,
            (
                "mfe_12-mfe_3k > 0.05 → K shrink peek-eligible"
                if k_implicated
                else "no sharp post-rank-3 decay → K stays out of peek ladder"
            ),
        ),
    ]


def coverage_diagnostics(panel: pl.DataFrame, direction: str) -> list[MetricResult]:
    """Bars / sessions with ≥1 Top-K name under sleeve open."""
    k = k_for(direction)
    if panel.height == 0:
        return [
            MetricResult("COVtopk", direction, None, None, None, 0, None, "empty")
        ]
    per_bar = (
        panel.group_by(["date", "date_only"], maintain_order=True)
        .agg(
            n_elig=pl.len(),
            n_topk=(pl.col("eval_rank") <= k).sum(),
        )
        .filter(pl.col("n_topk") >= 1)
    )
    n_bars = per_bar.height
    n_sess = per_bar.select(pl.col("date_only").n_unique()).item() if n_bars else 0
    return [
        MetricResult(
            "COVtopk",
            direction,
            float(n_bars),
            None,
            None,
            int(panel.height),
            None,
            f"bars_with_topk={n_bars} sessions={n_sess} K={k}",
        ),
        MetricResult(
            "COVsess",
            direction,
            float(n_sess),
            None,
            None,
            n_bars,
            None,
            "sessions with ≥1 Top-K name",
        ),
    ]


def suggest_a2_floors(cov_bars: float, cov_sess: float) -> tuple[int, int]:
    """Pre-register A2 kill-switch mins from Step 0 coverage (before Peek 1)."""
    min_bars = max(min_bars_for("long"), int(cov_bars * A2_MIN_BARS_FRAC))
    min_sess = max(MIN_SESSIONS, int(cov_sess * A2_MIN_SESS_FRAC))
    return min_bars, min_sess


def veto_val_diagnostics(
    val_scored: pl.DataFrame | None,
    direction: str,
) -> list[MetricResult]:
    """
    OOF multiclass P(SL)/P(TO)/P(TP) Top-K vs Rest + P(TP) ECE on purged val.

    ``val_scored`` must carry eval_rank (from path-EV on same val rows) plus
    p_sl / p_to / p_tp / veto_y.
    """
    if val_scored is None or val_scored.height == 0:
        return [
            MetricResult(
                "VETOsep", direction, None, None, None, 0, None, "no veto val"
            )
        ]
    if "eval_rank" not in val_scored.columns:
        return [
            MetricResult(
                "VETOsep",
                direction,
                None,
                None,
                None,
                val_scored.height,
                None,
                "missing eval_rank on veto val",
            )
        ]
    k = k_for(direction)
    ranked = val_scored.filter(pl.col("eval_rank").is_not_null())
    top = ranked.filter(pl.col("eval_rank") <= k)
    rest = ranked.filter(pl.col("eval_rank") > k)
    if top.height == 0 or rest.height == 0:
        return [
            MetricResult(
                "VETOsep", direction, None, None, None, 0, None, "thin top/rest"
            )
        ]

    metrics: list[MetricResult] = []
    for name, col in (("VETOsl", "p_sl"), ("VETOto", "p_to"), ("VETOtp", "p_tp")):
        t = float(top[col].mean())
        r = float(rest[col].mean())
        metrics.append(
            MetricResult(
                name,
                direction,
                t - r,
                None,
                None,
                top.height + rest.height,
                None,
                f"top={t:.3f} rest={r:.3f}",
            )
        )

    y_tp = (val_scored["veto_y"].to_numpy() == _TB_CLASS_TP).astype(int)
    p_tp = val_scored["p_tp"].to_numpy()
    ece = _ece_binary(y_tp, p_tp)
    metrics.append(
        MetricResult(
            "VETOece",
            direction,
            ece,
            None,
            None,
            int(val_scored.height),
            None,
            f"P(TP) ECE bins={_ECE_BINS} (purged val; report-only)",
        )
    )
    return metrics


def admission_step0_diagnostics(
    scored: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
    veto_val: pl.DataFrame | None = None,
) -> list[MetricResult]:
    """Full Step 0 readout + baseline H5/H1/H2/H3 reprint for hard-gate."""
    panel = prepare_eval_panel(scored, direction)
    metrics: list[MetricResult] = [
        universe_parity_precondition(panel, direction),
        h10_null_leakage(panel, direction, n_boot, rng),
    ]
    metrics.extend(coverage_diagnostics(panel, direction))
    metrics.extend(score_floor_diagnostics(panel, direction))
    metrics.extend(rank_tier_refresh_diagnostics(panel, direction))
    metrics.extend(path_density_diagnostics(scored, direction, n_boot, rng))
    metrics.extend(veto_val_diagnostics(veto_val, direction))

    if panel.height == 0:
        for name in ("H1", "H3", "H2", "H5"):
            metrics.append(
                MetricResult(
                    name, direction, None, None, None, 0, False, "empty panel"
                )
            )
        return metrics

    metrics.append(h1_spearman_ic(panel, direction, n_boot, rng))
    bar_stats = per_bar_topk_stats(panel, k_for(direction))
    metrics.append(h3_rank_monotonicity(bar_stats, direction, n_boot, rng))
    metrics.append(h2_topk_spread(bar_stats, direction, n_boot, rng))
    metrics.append(h4_cost_netted_spread(bar_stats, direction))
    metrics.extend(h5_stock_tb_bridge(bar_stats, direction, n_boot, rng))

    # A2 floor suggestion from this fold's Top-K coverage.
    cov = next((m for m in metrics if m.name == "COVtopk"), None)
    sess = next((m for m in metrics if m.name == "COVsess"), None)
    if cov and cov.value is not None and sess and sess.value is not None:
        min_bars, min_sess = suggest_a2_floors(cov.value, sess.value)
        metrics.append(
            MetricResult(
                "A2sug",
                direction,
                float(min_bars),
                None,
                None,
                int(cov.value),
                None,
                f"suggest A2 min_bars={min_bars} min_sessions={min_sess} (lock before Peek 1)",
            )
        )
    return metrics


def evaluate_admission_step0(
    scored: pl.DataFrame,
    directions: list[str],
    n_boot: int,
    seed: int,
    veto_val_by_direction: dict[str, pl.DataFrame] | None = None,
) -> list[MetricResult]:
    """Run Step 0 admission diagnostics for requested sleeves."""
    rng = np.random.default_rng(seed)
    veto_map = veto_val_by_direction or {}
    metrics: list[MetricResult] = []
    for direction in directions:
        metrics.extend(
            admission_step0_diagnostics(
                scored,
                direction,
                n_boot,
                rng,
                veto_val=veto_map.get(direction),
            )
        )
    return metrics


def evaluate_conviction_peek(
    scored: pl.DataFrame,
    direction: str,
    quantile: float,
    n_boot: int,
    seed: int,
    a2_min_bars: int,
    a2_min_sessions: int,
) -> list[MetricResult]:
    """
    Peek 1 — conviction floor only (inference).

    Gates: H5/H1/H2/H3 on admitted-as-top book; A1 admitted vs rejected-Top-K;
    A2 coverage kill-switch.
    """
    rng = np.random.default_rng(seed)
    panel = prepare_eval_panel(scored, direction)
    metrics: list[MetricResult] = [
        universe_parity_precondition(panel, direction),
        h10_null_leakage(panel, direction, n_boot, rng),
    ]
    if panel.height == 0:
        return metrics

    admitted_panel = apply_conviction_floor(panel, quantile)
    contrast = per_bar_admission_contrast(admitted_panel)

    # Null-narrow detector: eligible-score floor never rejects Top-K (score-rank tautology).
    top_k = admitted_panel.filter(pl.col("eval_rank") <= k_for(direction))
    n_top = top_k.height
    n_rej = int(top_k.filter(pl.col("rejected_topk")).height) if n_top else 0
    null_narrow = n_top > 0 and n_rej == 0
    metrics.append(
        MetricResult(
            "NULLnarrow",
            direction,
            1.0 if null_narrow else float(n_rej) / float(n_top) if n_top else float("nan"),
            None,
            None,
            n_top,
            None,
            (
                "P-floor rejects 0 Top-K rows (score-rank tautology)"
                if null_narrow
                else f"rejected_topk_rows={n_rej}/{n_top}"
            ),
        )
    )

    # Coverage of admitted book.
    adm_bars = admitted_panel.filter(pl.col("admitted")).select("date").unique()
    n_adm_bars = adm_bars.height
    n_adm_sess = (
        admitted_panel.filter(pl.col("admitted"))
        .select(pl.col("date_only").n_unique())
        .item()
        if n_adm_bars
        else 0
    )
    a2_ok = n_adm_bars >= a2_min_bars and n_adm_sess >= a2_min_sessions
    metrics.append(
        MetricResult(
            "A2",
            direction,
            float(n_adm_bars),
            None,
            None,
            n_adm_bars,
            a2_ok,
            (
                f"admitted bars={n_adm_bars} sess={n_adm_sess} "
                f"floor={a2_min_bars}/{a2_min_sessions} q={quantile:.2f}"
            ),
        )
    )

    metrics.append(
        _ci_on_col(
            "A1",
            direction,
            contrast,
            "a1",
            n_boot,
            rng,
            f"admitted - rejected_TopK TB+1 q={quantile:.2f}",
        )
    )
    if contrast.height:
        metrics.append(
            MetricResult(
                "TBadm",
                direction,
                float(contrast["p_tb_adm"].mean()),
                None,
                None,
                contrast.height,
                None,
                (
                    f"adm={float(contrast['p_tb_adm'].mean()):.3f} "
                    f"rej={float(contrast['p_tb_rej'].mean()):.3f} "
                    f"mean_n_adm={float(contrast['n_admitted'].mean()):.2f}"
                ),
            )
        )

    # Rebuild bar_stats treating admitted names as the Top book for H2/H5 hold.
    # Rank non-admitted as Rest; admitted keep relative order via eval_rank.
    k = k_for(direction)
    ranked = admitted_panel.with_columns(
        eval_rank=pl.when(pl.col("admitted"))
        .then(pl.col("eval_rank"))
        .otherwise(pl.lit(k + 1))
    )
    # H1 uses full eligible panel scores (ranker unchanged).
    metrics.append(h1_spearman_ic(panel, direction, n_boot, rng))
    bar_stats = per_bar_topk_stats(ranked, k)
    metrics.append(h3_rank_monotonicity(bar_stats, direction, n_boot, rng))
    metrics.append(h2_topk_spread(bar_stats, direction, n_boot, rng))
    metrics.append(h4_cost_netted_spread(bar_stats, direction))
    metrics.extend(h5_stock_tb_bridge(bar_stats, direction, n_boot, rng))
    return metrics
