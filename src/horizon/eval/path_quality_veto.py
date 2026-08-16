"""Path-quality veto Step 0 / Peek 1 — P(SL) relative admit overlay."""

from __future__ import annotations

from typing import Any

import lightgbm as lgb
import numpy as np
import polars as pl
from sklearn.metrics import roc_auc_score

from src.horizon.eval.admission import (
    A2_MIN_BARS_FRAC,
    _TB_CLASS_SL,
    _TB_CLASS_TO,
    _TB_CLASS_TP,
    _ece_binary,
    _multiclass_params,
    prepare_long_sleeve_tb,
    rank_tier_refresh_diagnostics,
    suggest_a2_floors,
    veto_val_diagnostics,
)
from src.horizon.eval.bar_stats import per_bar_topk_stats
from src.horizon.eval.constants import (
    MIN_NAMES_PER_BAR,
    MetricResult,
    k_for,
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
from src.horizon.horizon_model import episode_balanced_weights

# Charter locks — docs/archive/horizon-path-quality-veto-charter.md
DEFAULT_VETO_QUANTILE = 0.80  # worst 20% → P(SL) > eligible P80
REJECT_MASS_PROBE_QUANTS = (0.70, 0.80, 0.90)  # report 10/20/30% tails
NULL_LEVER_REJECT_MASS_MAX = 0.02  # < 2% both folds → STOP 0/2
MIN_REJECT_ROWS_FOR_POWER = 100  # per fold under locked cut
SPARSE_ELIGIBLE_MIN = 5  # skip veto when n_eligible < 5


def fit_veto_full_train(
    train_df: pl.DataFrame,
) -> tuple[lgb.LGBMClassifier | None, dict[str, Any]]:
    """Fit multiclass TB head on full train sleeve (holdout scoring; not a peek)."""
    sleeve, feat_list = prepare_long_sleeve_tb(train_df)
    if sleeve.height == 0:
        return None, {"reason": "empty sleeve"}

    dates = sleeve.select("date_only").unique().sort("date_only").to_series().to_list()
    if len(dates) < 10:
        return None, {"reason": "too few sessions"}
    cut = dates[int(0.9 * len(dates))]
    fold_train = sleeve.filter(pl.col("date_only") < cut)
    fold_val = sleeve.filter(pl.col("date_only") >= cut)
    if min(fold_train.height, fold_val.height) == 0:
        fold_train, fold_val = sleeve, sleeve.head(max(1, sleeve.height // 10))

    model = lgb.LGBMClassifier(**_multiclass_params())
    model.fit(
        fold_train.select(feat_list).to_numpy(),
        fold_train["tb_class"].to_numpy(),
        sample_weight=episode_balanced_weights(fold_train),
        eval_X=fold_val.select(feat_list).to_numpy(),
        eval_y=fold_val["tb_class"].to_numpy(),
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
    )
    return model, {
        "features": feat_list,
        "train_bars": fold_train.height,
        "val_bars": fold_val.height,
    }


def attach_veto_probs(
    df: pl.DataFrame, model: lgb.LGBMClassifier, features: list[str]
) -> pl.DataFrame:
    """Add p_sl / p_to / p_tp columns via multiclass predict_proba."""
    X = df.select(features).to_numpy()
    proba = model.predict_proba(X)
    classes = list(model.classes_)
    col_map = {int(c): i for i, c in enumerate(classes)}
    n = len(X)
    p_sl = (
        proba[:, col_map[_TB_CLASS_SL]]
        if _TB_CLASS_SL in col_map
        else np.zeros(n)
    )
    p_to = (
        proba[:, col_map[_TB_CLASS_TO]]
        if _TB_CLASS_TO in col_map
        else np.zeros(n)
    )
    p_tp = (
        proba[:, col_map[_TB_CLASS_TP]]
        if _TB_CLASS_TP in col_map
        else np.zeros(n)
    )
    return df.with_columns(
        p_sl=pl.Series(p_sl),
        p_to=pl.Series(p_to),
        p_tp=pl.Series(p_tp),
    )


def apply_psl_veto(
    panel: pl.DataFrame,
    quantile: float = DEFAULT_VETO_QUANTILE,
    k: int | None = None,
) -> pl.DataFrame:
    """
    Inference-only: veto Top-K names with P(SL) > per-bar eligible quantile.

    Strict inequality (ties at floor retained). Sparse bars (n < 5) skip veto.
    """
    k_eff = k_for("long") if k is None else k
    if "p_sl" not in panel.columns:
        raise ValueError("apply_psl_veto requires p_sl")

    rows = []
    for (bar,), g in panel.group_by("date", maintain_order=True):
        n = g.height
        if n < SPARSE_ELIGIBLE_MIN:
            out = g.with_columns(
                veto_floor=pl.lit(None, dtype=pl.Float64),
                vetoed=pl.lit(False),
                admitted=(pl.col("eval_rank") <= k_eff),
                rejected_topk=pl.lit(False),
                veto_skipped=pl.lit(True),
            )
        else:
            floor = float(np.quantile(g["p_sl"].to_numpy(), quantile))
            out = g.with_columns(
                veto_floor=pl.lit(floor),
                vetoed=pl.col("p_sl") > floor,
                veto_skipped=pl.lit(False),
            ).with_columns(
                admitted=(pl.col("eval_rank") <= k_eff) & (~pl.col("vetoed")),
                rejected_topk=(pl.col("eval_rank") <= k_eff) & pl.col("vetoed"),
            )
        rows.append(out)
    if not rows:
        return panel.with_columns(
            veto_floor=pl.lit(None, dtype=pl.Float64),
            vetoed=pl.lit(False),
            admitted=pl.lit(False),
            rejected_topk=pl.lit(False),
            veto_skipped=pl.lit(True),
        )
    return pl.concat(rows, how="vertical_relaxed")


def reject_mass_probe(
    panel: pl.DataFrame, direction: str = "long"
) -> list[MetricResult]:
    """Report Top-K fraction with P(SL) > eligible P70/P80/P90 (charter Step 0)."""
    k = k_for(direction)
    metrics: list[MetricResult] = []
    if panel.height == 0 or "p_sl" not in panel.columns:
        return [
            MetricResult(
                "REJmass", direction, None, None, None, 0, None, "missing p_sl"
            )
        ]

    for q in REJECT_MASS_PROBE_QUANTS:
        tag = int(q * 100)
        n_top = 0
        n_rej = 0
        for (_bar,), g in panel.group_by("date", maintain_order=True):
            if g.height < max(MIN_NAMES_PER_BAR, k + 1):
                continue
            top = g.filter(pl.col("eval_rank") <= k)
            if top.height == 0:
                continue
            floor = float(np.quantile(g["p_sl"].to_numpy(), q))
            n_top += top.height
            n_rej += int((top["p_sl"] > floor).sum())
        frac = float(n_rej) / float(n_top) if n_top else float("nan")
        metrics.append(
            MetricResult(
                f"REJp{tag}",
                direction,
                frac,
                None,
                None,
                n_top,
                None,
                f"Top-K rows with P(SL)>elig P{tag}: {n_rej}/{n_top}",
            )
        )
    return metrics


def projected_veto_coverage(
    panel: pl.DataFrame,
    quantile: float = DEFAULT_VETO_QUANTILE,
    direction: str = "long",
) -> list[MetricResult]:
    """Admitted bars/sessions under locked P(SL) cut + A2 floor suggestion."""
    vetoed = apply_psl_veto(panel, quantile=quantile)
    adm = vetoed.filter(pl.col("admitted"))
    n_bars = (
        adm.select(pl.col("date").n_unique()).item() if adm.height else 0
    )
    n_sess = (
        adm.select(pl.col("date_only").n_unique()).item() if adm.height else 0
    )
    n_rej_rows = int(vetoed.filter(pl.col("rejected_topk")).height)
    n_top_rows = int(
        vetoed.filter(pl.col("eval_rank") <= k_for(direction)).height
    )
    rej_frac = float(n_rej_rows) / float(n_top_rows) if n_top_rows else float("nan")
    min_bars, min_sess = suggest_a2_floors(float(n_bars), float(n_sess))
    null_fail = (
        np.isfinite(rej_frac) and rej_frac < NULL_LEVER_REJECT_MASS_MAX
    )
    power_ok = n_rej_rows >= MIN_REJECT_ROWS_FOR_POWER
    return [
        MetricResult(
            "ADMproj",
            direction,
            float(n_bars),
            None,
            None,
            n_top_rows,
            None,
            f"projected admitted bars={n_bars} sess={n_sess} q={quantile:.2f}",
        ),
        MetricResult(
            "REJlock",
            direction,
            rej_frac,
            None,
            None,
            n_rej_rows,
            None,
            f"locked-cut reject rows={n_rej_rows}/{n_top_rows}",
        ),
        MetricResult(
            "NULLlev",
            direction,
            rej_frac,
            None,
            None,
            n_top_rows,
            not null_fail,
            (
                f"reject_mass={rej_frac:.4f} "
                f"stop_if_both_folds<{NULL_LEVER_REJECT_MASS_MAX}"
            ),
        ),
        MetricResult(
            "POWERrej",
            direction,
            float(n_rej_rows),
            None,
            None,
            n_rej_rows,
            power_ok,
            f"min_reject_rows={MIN_REJECT_ROWS_FOR_POWER} (Peek 1 authorize)",
        ),
        MetricResult(
            "A2sug",
            direction,
            float(min_bars),
            None,
            None,
            int(n_bars),
            None,
            (
                f"suggest A2 min_bars={min_bars} min_sessions={min_sess} "
                f"(from veto projection; frac={A2_MIN_BARS_FRAC})"
            ),
        ),
    ]


def veto_holdout_calibration(
    panel: pl.DataFrame, direction: str = "long"
) -> list[MetricResult]:
    """Holdout P(SL) ECE + ROC-AUC vs realized SL (report-only companion)."""
    if panel.height == 0 or "p_sl" not in panel.columns:
        return [
            MetricResult(
                "VETOauc", direction, None, None, None, 0, None, "missing p_sl"
            )
        ]
    tb = panel.filter(pl.col("tb_label").is_not_null() & pl.col("p_sl").is_finite())
    if tb.height == 0:
        return [
            MetricResult(
                "VETOauc", direction, None, None, None, 0, None, "empty tb"
            )
        ]
    y_sl = (tb["tb_label"].to_numpy() == -1).astype(int)
    p_sl = tb["p_sl"].to_numpy()
    ece = _ece_binary(y_sl, p_sl)
    try:
        auc = float(roc_auc_score(y_sl, p_sl)) if y_sl.min() != y_sl.max() else float("nan")
    except ValueError:
        auc = float("nan")
    return [
        MetricResult(
            "VETOauc",
            direction,
            auc,
            None,
            None,
            tb.height,
            None,
            "P(SL) ROC-AUC holdout (report)",
        ),
        MetricResult(
            "VETOeceH",
            direction,
            ece,
            None,
            None,
            tb.height,
            None,
            "P(SL) ECE holdout (report)",
        ),
    ]


def path_quality_step0_diagnostics(
    scored: pl.DataFrame,
    direction: str,
    n_boot: int,
    rng: np.random.Generator,
    veto_val: pl.DataFrame | None,
    veto_model: lgb.LGBMClassifier | None,
    veto_features: list[str] | None,
) -> list[MetricResult]:
    """Step 0 readout for path-quality veto charter."""
    panel = prepare_eval_panel(scored, direction)
    metrics: list[MetricResult] = [
        universe_parity_precondition(panel, direction),
        h10_null_leakage(panel, direction, n_boot, rng),
    ]

    if panel.height == 0:
        for name in ("H1", "H3", "H2", "H5"):
            metrics.append(
                MetricResult(
                    name, direction, None, None, None, 0, False, "empty panel"
                )
            )
        return metrics

    # Attach holdout veto probs for reject-mass / projection.
    if veto_model is not None and veto_features is not None:
        # prepare_eval_panel may have dropped feature cols — join from scored.
        feat_cols = [c for c in veto_features if c in scored.columns]
        if len(feat_cols) == len(veto_features):
            keys = ["symbol", "date"]
            scored_feats = scored.select(keys + veto_features).unique(subset=keys)
            panel = panel.join(scored_feats, on=keys, how="left")
            panel = attach_veto_probs(panel, veto_model, veto_features)
            metrics.extend(reject_mass_probe(panel, direction))
            metrics.extend(projected_veto_coverage(panel, direction=direction))
            metrics.extend(veto_holdout_calibration(panel, direction))
        else:
            metrics.append(
                MetricResult(
                    "REJmass",
                    direction,
                    None,
                    None,
                    None,
                    0,
                    None,
                    "veto features missing on scored frame",
                )
            )
    else:
        metrics.append(
            MetricResult(
                "REJmass", direction, None, None, None, 0, None, "no veto model"
            )
        )

    metrics.extend(veto_val_diagnostics(veto_val, direction))
    # Enrich val ECE with AUC if veto_y present.
    if veto_val is not None and veto_val.height and "p_sl" in veto_val.columns:
        y_sl = (veto_val["veto_y"].to_numpy() == _TB_CLASS_SL).astype(int)
        p_sl = veto_val["p_sl"].to_numpy()
        try:
            auc = (
                float(roc_auc_score(y_sl, p_sl))
                if y_sl.min() != y_sl.max()
                else float("nan")
            )
        except ValueError:
            auc = float("nan")
        metrics.append(
            MetricResult(
                "VETOaucV",
                direction,
                auc,
                None,
                None,
                veto_val.height,
                None,
                "P(SL) ROC-AUC purged val (report)",
            )
        )

    metrics.extend(rank_tier_refresh_diagnostics(panel, direction))

    metrics.append(h1_spearman_ic(panel, direction, n_boot, rng))
    bar_stats = per_bar_topk_stats(panel, k_for(direction))
    metrics.append(h3_rank_monotonicity(bar_stats, direction, n_boot, rng))
    metrics.append(h2_topk_spread(bar_stats, direction, n_boot, rng))
    metrics.append(h4_cost_netted_spread(bar_stats, direction))
    metrics.extend(h5_stock_tb_bridge(bar_stats, direction, n_boot, rng))
    return metrics


def evaluate_path_quality_step0(
    scored: pl.DataFrame,
    n_boot: int,
    seed: int,
    veto_val: pl.DataFrame | None,
    veto_model: lgb.LGBMClassifier | None,
    veto_features: list[str] | None,
) -> list[MetricResult]:
    rng = np.random.default_rng(seed)
    return path_quality_step0_diagnostics(
        scored,
        "long",
        n_boot,
        rng,
        veto_val,
        veto_model,
        veto_features,
    )


def evaluate_psl_veto_peek(
    scored: pl.DataFrame,
    veto_model: lgb.LGBMClassifier,
    veto_features: list[str],
    quantile: float,
    n_boot: int,
    seed: int,
    a2_min_bars: int,
    a2_min_sessions: int,
) -> list[MetricResult]:
    """Peek 1 — P(SL) worst-quantile veto only."""
    rng = np.random.default_rng(seed)
    panel = prepare_eval_panel(scored, "long")
    metrics: list[MetricResult] = [
        universe_parity_precondition(panel, "long"),
        h10_null_leakage(panel, "long", n_boot, rng),
    ]
    if panel.height == 0:
        return metrics

    keys = ["symbol", "date"]
    scored_feats = scored.select(keys + veto_features).unique(subset=keys)
    panel = panel.join(scored_feats, on=keys, how="left")
    panel = attach_veto_probs(panel, veto_model, veto_features)
    admitted_panel = apply_psl_veto(panel, quantile=quantile)

    adm_bars = (
        admitted_panel.filter(pl.col("admitted"))
        .select(pl.col("date").n_unique())
        .item()
    )
    n_adm_sess = (
        admitted_panel.filter(pl.col("admitted"))
        .select(pl.col("date_only").n_unique())
        .item()
        if adm_bars
        else 0
    )
    a2_ok = adm_bars >= a2_min_bars and n_adm_sess >= a2_min_sessions
    metrics.append(
        MetricResult(
            "A2",
            "long",
            float(adm_bars),
            None,
            None,
            adm_bars,
            a2_ok,
            (
                f"admitted bars={adm_bars} sess={n_adm_sess} "
                f"floor={a2_min_bars}/{a2_min_sessions} q={quantile:.2f}"
            ),
        )
    )

    # A1 contrast.
    from src.horizon.eval.admission import per_bar_admission_contrast, _ci_on_col

    contrast = per_bar_admission_contrast(admitted_panel)
    metrics.append(
        _ci_on_col(
            "A1",
            "long",
            contrast,
            "a1",
            n_boot,
            rng,
            f"admitted - rejected_TopK TB+1 P(SL) q={quantile:.2f}",
        )
    )
    if contrast.height:
        metrics.append(
            MetricResult(
                "TBadm",
                "long",
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

    n_rej = int(admitted_panel.filter(pl.col("rejected_topk")).height)
    n_top = int(
        admitted_panel.filter(pl.col("eval_rank") <= k_for("long")).height
    )
    metrics.append(
        MetricResult(
            "NULLnarrow",
            "long",
            1.0 if n_rej == 0 else float(n_rej) / float(n_top) if n_top else float("nan"),
            None,
            None,
            n_top,
            None,
            f"rejected_topk_rows={n_rej}/{n_top}",
        )
    )

    metrics.append(h1_spearman_ic(panel, "long", n_boot, rng))
    k = k_for("long")
    ranked = admitted_panel.with_columns(
        eval_rank=pl.when(pl.col("admitted"))
        .then(pl.col("eval_rank"))
        .otherwise(pl.lit(k + 1))
    )
    bar_stats = per_bar_topk_stats(ranked, k)
    metrics.append(h3_rank_monotonicity(bar_stats, "long", n_boot, rng))
    metrics.append(h2_topk_spread(bar_stats, "long", n_boot, rng))
    metrics.append(h4_cost_netted_spread(bar_stats, "long"))
    metrics.extend(h5_stock_tb_bridge(bar_stats, "long", n_boot, rng))
    return metrics
