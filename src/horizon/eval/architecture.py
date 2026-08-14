"""Short architecture Phase 1 — complementarity / listwise / coarse-universe (0 peeks)."""

from __future__ import annotations

from typing import Any

import lightgbm as lgb
import numpy as np
import polars as pl
from scipy.stats import spearmanr

from src.horizon.eval.bar_stats import per_bar_topk_stats
from src.horizon.eval.constants import (
    K_SHORT,
    MIN_BARS_SHORT,
    MIN_NAMES_PER_BAR,
    MetricResult,
)
from src.horizon.eval.panel import prepare_eval_panel
from src.horizon.horizon_model import (
    DEFAULT_EMBARGO_DAYS,
    SHORT_FEATURES,
    SHORT_PARAMS,
    GBMHorizonModel,
    episode_balanced_weights,
    get_purged_cv_splits,
    sleeve_sample_diagnostics,
)
from src.pipelines.horizon_pipeline import SLEEVES, _fit_sleeve_mask, _path_ev_target
from src.utils.eval_common import MIN_SESSIONS

# Numeric Phase-1 cuts (architecture charter — locked).
A1_JACCARD_MAX = 0.40
A1_TB_ONLY_LIFT = 0.020
A1_H5_PROXY_MAX = 0.0
A2_MEAN_ELIGIBLE_MIN = 50.0
A2_NDCG_LIFT_MIN = 0.030
A3_H5_DELTA_MIN = 0.020
A3_MIN_BARS = MIN_BARS_SHORT
A3_MIN_SESS = MIN_SESSIONS
NDCG_LABEL_GAIN = (0.0, 1.0, 3.0)
RANK_MIN_GROUP = 2
PROBE_SEED = 42

# Closed O1 family reused as a *diagnostic* TB-probe only (not a peek / not defaults).
_PROBE_PARAMS = {
    **{k: v for k, v in SHORT_PARAMS.items() if k not in ("objective", "alpha", "metric")},
    "objective": "lambdarank",
    "metric": "ndcg",
    "importance_type": "gain",
}


def prepare_short_sleeve(
    df: pl.DataFrame, features: list[str] | None = None
) -> tuple[pl.DataFrame, list[str]]:
    cfg = SLEEVES["short"]
    feat_list = list(features) if features is not None else list(SHORT_FEATURES)
    drop_cols = feat_list + ["path_ev_y"]
    sleeve = (
        df.filter(_fit_sleeve_mask(cfg) & pl.col(cfg.eligible_col))
        .with_columns(_path_ev_target(cfg))
        .drop_nulls(subset=drop_cols)
        .filter(pl.col("path_ev_y").is_finite())
    )
    if "date_only" not in sleeve.columns:
        sleeve = sleeve.with_columns(date_only=pl.col("date").dt.date())
    return sleeve, feat_list


def last_purged_split(
    sleeve_df: pl.DataFrame,
    calendar_df: pl.DataFrame,
    cv_kwargs: dict[str, Any] | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame] | None:
    if "date_only" not in calendar_df.columns:
        calendar_df = calendar_df.with_columns(date_only=pl.col("date").dt.date())
    calendar_dates = (
        calendar_df.select("date_only").unique().sort("date_only").to_series().to_list()
    )
    splits = get_purged_cv_splits(
        sleeve_df, calendar_dates=calendar_dates, **(cv_kwargs or {})
    )
    if not splits:
        return None
    return splits[-1]


def fit_short_last_fold_path_ev(
    train_df: pl.DataFrame,
) -> tuple[GBMHorizonModel | None, pl.DataFrame | None, pl.DataFrame | None, dict]:
    """Last purged fold only — Phase 1 val authorize; not a holdout peek."""
    sleeve, feat_list = prepare_short_sleeve(train_df)
    diagnostics = sleeve_sample_diagnostics(sleeve)
    if sleeve.height == 0:
        return None, None, None, {"diagnostics": diagnostics}
    split = last_purged_split(sleeve, train_df)
    if split is None:
        return None, None, None, {"diagnostics": diagnostics, "n_splits": 0}
    fold_train, fold_val, fold_test = split
    if min(fold_train.height, fold_val.height) == 0:
        return None, None, None, {"diagnostics": diagnostics, "n_splits": 0}

    model = GBMHorizonModel(direction="short")
    val_ic = model.fit(
        X_train=fold_train,
        y_train=fold_train["path_ev_y"],
        X_val=fold_val,
        y_val=fold_val["path_ev_y"],
        features=feat_list,
        train_weight=episode_balanced_weights(fold_train),
    )
    stats = {
        "diagnostics": diagnostics,
        "n_splits": 1,
        "val_ic_ev": val_ic,
        "train_bars": fold_train.height,
        "val_bars": fold_val.height,
        "embargo_days": DEFAULT_EMBARGO_DAYS,
    }
    return model, fold_train, fold_val, stats


def _tb_grade_expr() -> pl.Expr:
    """TP=2 / TO=1 / SL=0 from StockTB label."""
    return (
        pl.when(pl.col("tb_label_short") == 1)
        .then(2)
        .when(pl.col("tb_label_short") == 0)
        .then(1)
        .when(pl.col("tb_label_short") == -1)
        .then(0)
        .otherwise(None)
        .cast(pl.Int32)
        .alias("tb_grade")
    )


def _sort_rank_groups(df: pl.DataFrame) -> tuple[pl.DataFrame, np.ndarray]:
    ordered = df.sort("date")
    groups = (
        ordered.group_by("date", maintain_order=True)
        .len()
        .get_column("len")
        .to_numpy()
    )
    return ordered, groups.astype(np.int32)


def fit_tb_probe_lambdarank(
    fold_train: pl.DataFrame,
    fold_val: pl.DataFrame,
    features: list[str],
) -> tuple[lgb.LGBMRanker | None, float]:
    """
    Closed-O1-family TB-probe for complementarity Jaccard / IC_tb only.

    Not a peek. Forbid remounting this ranker on holdout.
    """
    train = fold_train.with_columns(_tb_grade_expr()).drop_nulls(
        subset=features + ["tb_grade"]
    )
    val = fold_val.with_columns(_tb_grade_expr()).drop_nulls(
        subset=features + ["tb_grade"]
    )
    train, group_train = _sort_rank_groups(train)
    val, group_val = _sort_rank_groups(val)
    keep_tr = group_train >= RANK_MIN_GROUP
    keep_va = group_val >= RANK_MIN_GROUP
    if not keep_tr.any() or not keep_va.any():
        return None, float("nan")

    train_dates = train.select("date").unique(maintain_order=True).to_series().to_list()
    val_dates = val.select("date").unique(maintain_order=True).to_series().to_list()
    train_keep = [d for d, ok in zip(train_dates, keep_tr) if ok]
    val_keep = [d for d, ok in zip(val_dates, keep_va) if ok]
    train = train.filter(pl.col("date").is_in(train_keep))
    val = val.filter(pl.col("date").is_in(val_keep))
    train, group_train = _sort_rank_groups(train)
    val, group_val = _sort_rank_groups(val)

    ranker = lgb.LGBMRanker(**_PROBE_PARAMS)
    X_train = train.select(features).to_numpy()
    y_train = train["tb_grade"].to_numpy()
    X_val = val.select(features).to_numpy()
    y_val = val["tb_grade"].to_numpy()
    ranker.fit(
        X_train,
        y_train,
        group=group_train,
        sample_weight=episode_balanced_weights(train),
        eval_X=X_val,
        eval_y=y_val,
        eval_group=[group_val],
        eval_at=[3],
        callbacks=[lgb.early_stopping(stopping_rounds=40, verbose=False)],
    )
    raw_val = ranker.predict(X_val)
    ic, _ = spearmanr(raw_val, (val["tb_label_short"] == 1).to_numpy())
    ic_tb = float(ic) if ic == ic else 0.0
    return ranker, ic_tb


def _rerank(panel: pl.DataFrame, score_col: str) -> pl.DataFrame:
    return panel.with_columns(
        eval_rank=pl.col(score_col)
        .rank(method="ordinal", descending=True)
        .over("date")
    )


def h5_h2_proxy(panel: pl.DataFrame) -> tuple[float, float, int, int]:
    """Point Top−Rest TB=+1 (H5-proxy) and adj_excess spread (H2-proxy)."""
    stats = per_bar_topk_stats(panel, K_SHORT)
    finite = stats.filter(
        pl.col("h5").is_finite() & (pl.col("n_tb_top") > 0) & (pl.col("n_tb_rest") > 0)
    )
    n_bars = finite.height
    n_sess = finite.select(pl.col("date_only").n_unique()).item() if n_bars else 0
    h5 = float(finite["h5"].mean()) if n_bars else float("nan")
    h2 = float(finite["spread"].mean()) if n_bars else float("nan")
    return h5, h2, n_bars, n_sess


def _gain(grade: int) -> float:
    if grade < 0 or grade >= len(NDCG_LABEL_GAIN):
        return 0.0
    return NDCG_LABEL_GAIN[grade]


def ndcg_at_k(grades: np.ndarray, k: int = K_SHORT) -> float:
    k = min(k, grades.size)
    if k == 0:
        return 0.0
    dcg = sum(_gain(int(g)) / np.log2(i + 2) for i, g in enumerate(grades[:k]))
    ideal = np.sort(grades)[::-1]
    idcg = sum(_gain(int(g)) / np.log2(i + 2) for i, g in enumerate(ideal[:k]))
    return float(dcg / idcg) if idcg > 0 else 0.0


def path_ev_ndcg_vs_null(
    panel: pl.DataFrame, seed: int = PROBE_SEED
) -> tuple[float, float, float]:
    """Mean NDCG@3 of path-EV rank vs one shuffled null per bar (grades TP=2/TO=1/SL=0)."""
    rng = np.random.default_rng(seed)
    ev_scores: list[float] = []
    null_scores: list[float] = []
    for _, g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, K_SHORT + 1):
            continue
        graded = g.filter(pl.col("tb_label").is_not_null())
        if graded.height < K_SHORT:
            continue
        ordered = graded.sort("eval_rank")
        grades = (
            pl.when(pl.col("tb_label") == 1)
            .then(2)
            .when(pl.col("tb_label") == 0)
            .then(1)
            .otherwise(0)
            .cast(pl.Int32)
        )
        ev_grades = ordered.select(grades.alias("g"))["g"].to_numpy()
        ev_scores.append(ndcg_at_k(ev_grades, K_SHORT))
        shuffled = ev_grades.copy()
        rng.shuffle(shuffled)
        null_scores.append(ndcg_at_k(shuffled, K_SHORT))
    if not ev_scores:
        return float("nan"), float("nan"), float("nan")
    ev_mean = float(np.mean(ev_scores))
    null_mean = float(np.mean(null_scores))
    return ev_mean, null_mean, ev_mean - null_mean


def complementarity(
    ev_panel: pl.DataFrame, probe_score: np.ndarray
) -> dict[str, float]:
    """Val Top-K Jaccard + TB=+1 hit rates in EV-only / TB-only / both / neither."""
    k = K_SHORT
    panel = ev_panel.with_columns(probe_score=pl.Series(probe_score)).with_columns(
        probe_rank=pl.col("probe_score")
        .rank(method="ordinal", descending=True)
        .over("date")
    )
    jaccards: list[float] = []
    n_ev_only = n_tb_only = n_both = n_neither = 0
    hit_ev_only = hit_tb_only = hit_both = hit_neither = 0
    for _, g in panel.group_by("date", maintain_order=True):
        if g.height < max(MIN_NAMES_PER_BAR, k + 1):
            continue
        ev_top = set(g.filter(pl.col("eval_rank") <= k)["symbol"].to_list())
        tb_top = set(g.filter(pl.col("probe_rank") <= k)["symbol"].to_list())
        union = ev_top | tb_top
        if not union:
            continue
        jaccards.append(len(ev_top & tb_top) / len(union))
        labeled = g.filter(pl.col("tb_label").is_not_null())
        for row in labeled.iter_rows(named=True):
            sym = row["symbol"]
            hit = int(row["tb_label"] == 1)
            in_ev = sym in ev_top
            in_tb = sym in tb_top
            if in_ev and in_tb:
                n_both += 1
                hit_both += hit
            elif in_ev:
                n_ev_only += 1
                hit_ev_only += hit
            elif in_tb:
                n_tb_only += 1
                hit_tb_only += hit
            else:
                n_neither += 1
                hit_neither += hit

    def _rate(hits: int, n: int) -> float:
        return hits / n if n else float("nan")

    probe_ranked = _rerank(panel.rename({"eval_score": "ev_score"}), "probe_score")
    probe_h5, _, _, _ = h5_h2_proxy(
        probe_ranked.with_columns(eval_score=pl.col("probe_score"))
    )
    ev_h5, ev_h2, n_bars, n_sess = h5_h2_proxy(ev_panel)
    return {
        "jaccard": float(np.mean(jaccards)) if jaccards else float("nan"),
        "hit_ev_only": _rate(hit_ev_only, n_ev_only),
        "hit_tb_only": _rate(hit_tb_only, n_tb_only),
        "hit_both": _rate(hit_both, n_both),
        "hit_neither": _rate(hit_neither, n_neither),
        "n_ev_only": float(n_ev_only),
        "n_tb_only": float(n_tb_only),
        "n_both": float(n_both),
        "n_neither": float(n_neither),
        "ev_h5_proxy": ev_h5,
        "ev_h2_proxy": ev_h2,
        "probe_h5_proxy": probe_h5,
        "n_bars": float(n_bars),
        "n_sess": float(n_sess),
    }


def listwise_geometry(panel: pl.DataFrame) -> dict[str, float]:
    per_bar = panel.group_by("date").agg(n=pl.len())
    mean_n = float(per_bar["n"].mean()) if per_bar.height else float("nan")
    n_tp = panel.filter(pl.col("tb_label") == 1).height
    n_to = panel.filter(pl.col("tb_label") == 0).height
    n_sl = panel.filter(pl.col("tb_label") == -1).height
    ndcg_ev, ndcg_null, ndcg_lift = path_ev_ndcg_vs_null(panel)
    return {
        "mean_eligible": mean_n,
        "n_tp": float(n_tp),
        "n_to": float(n_to),
        "n_sl": float(n_sl),
        "grade_mass_ok": float(n_tp > 0 and n_to > 0 and n_sl > 0),
        "ndcg_ev": ndcg_ev,
        "ndcg_null": ndcg_null,
        "ndcg_lift": ndcg_lift,
    }


def apply_adv_p50_mask(panel: pl.DataFrame, cutoff: float) -> pl.DataFrame:
    return panel.filter(
        pl.col("adv_rank_20d").is_finite() & (pl.col("adv_rank_20d") >= cutoff)
    )


def train_adv_p50_cutoff(fold_train: pl.DataFrame) -> float:
    finite = fold_train.filter(pl.col("adv_rank_20d").is_finite())
    if finite.height == 0:
        return 0.5
    return float(finite.select(pl.col("adv_rank_20d").quantile(0.5)).item())


def masked_proxies(
    panel: pl.DataFrame, masked: pl.DataFrame, baseline_h5: float
) -> dict[str, float]:
    reranked = _rerank(masked, "eval_score")
    h5, h2, n_bars, n_sess = h5_h2_proxy(reranked)
    return {
        "h5_proxy": h5,
        "h2_proxy": h2,
        "h5_delta": h5 - baseline_h5 if np.isfinite(h5) and np.isfinite(baseline_h5) else float("nan"),
        "n_bars": float(n_bars),
        "n_sess": float(n_sess),
    }


def holdout_min_n(panel: pl.DataFrame) -> tuple[int, int, bool]:
    stats = per_bar_topk_stats(panel, K_SHORT)
    finite = stats.filter(
        pl.col("h5").is_finite() & (pl.col("n_tb_top") > 0) & (pl.col("n_tb_rest") > 0)
    )
    n_bars = finite.height
    n_sess = finite.select(pl.col("date_only").n_unique()).item() if n_bars else 0
    clear = n_bars >= A3_MIN_BARS and n_sess >= A3_MIN_SESS
    return n_bars, n_sess, clear


def adv_tercile_stress(panel: pl.DataFrame) -> dict[str, dict[str, float]]:
    """Val H5/H2-proxy when ranking inside each ADV tercile."""
    out: dict[str, dict[str, float]] = {}
    if "adv_rank_20d" not in panel.columns or panel.height == 0:
        return out
    buckets = panel.with_columns(
        adv_bucket=pl.when(pl.col("adv_rank_20d") <= 1.0 / 3.0)
        .then(pl.lit("lo"))
        .when(pl.col("adv_rank_20d") <= 2.0 / 3.0)
        .then(pl.lit("mid"))
        .otherwise(pl.lit("hi"))
    )
    for bucket in ("lo", "mid", "hi"):
        slice_df = buckets.filter(pl.col("adv_bucket") == bucket)
        reranked = _rerank(slice_df, "eval_score")
        h5, h2, n_bars, n_sess = h5_h2_proxy(reranked)
        out[bucket] = {
            "h5_proxy": h5,
            "h2_proxy": h2,
            "n_bars": float(n_bars),
            "n_sess": float(n_sess),
        }
    return out


def _finite_le(value: float, cap: float) -> bool:
    return np.isfinite(value) and value <= cap


def _finite_lt(value: float, cap: float) -> bool:
    return np.isfinite(value) and value < cap


def _finite_ge(value: float, floor: float) -> bool:
    return np.isfinite(value) and value >= floor


def _finite_gt(value: float, floor: float) -> bool:
    return np.isfinite(value) and value > floor


def authorize_levers(
    fold_rows: dict[str, dict[str, Any]],
    holdout_h5_fail: dict[str, bool],
) -> dict[str, Any]:
    """
    Dual-fold numeric gate. ``fold_rows`` keyed A/B with Phase-1 diagnostics.
    Tie-break if multiple authorize: A1 → A2 → A3.
    """
    folds = [f for f in ("A", "B") if f in fold_rows]
    a1_ok = True
    a2_ok = True
    mask_clear = {"nifty50": True, "adv_p50": True}

    for fold in folds:
        row = fold_rows[fold]
        a1_ok = (
            a1_ok
            and _finite_lt(row["jaccard"], A1_JACCARD_MAX)
            and _finite_ge(
                row["hit_tb_only"] - row["hit_ev_only"], A1_TB_ONLY_LIFT
            )
            and _finite_le(row["ev_h5_proxy"], A1_H5_PROXY_MAX)
            and _finite_le(row["probe_h5_proxy"], A1_H5_PROXY_MAX)
        )
        a2_ok = (
            a2_ok
            and _finite_ge(row["mean_eligible"], A2_MEAN_ELIGIBLE_MIN)
            and bool(row["grade_mass_ok"])
            and _finite_ge(row["ndcg_lift"], A2_NDCG_LIFT_MIN)
            and bool(holdout_h5_fail.get(fold, True))
        )
        for mask in ("nifty50", "adv_p50"):
            m = row["masks"][mask]
            mask_clear[mask] = (
                mask_clear[mask]
                and _finite_ge(m["h5_delta"], A3_H5_DELTA_MIN)
                and _finite_gt(m["h2_proxy"], 0.0)
                and bool(m["holdout_min_n_clear"])
            )

    authorized: list[str] = []
    if a1_ok and folds:
        authorized.append("A1")
    if a2_ok and folds:
        authorized.append("A2")

    chosen_mask = None
    a3_ok = False
    if mask_clear["nifty50"] or mask_clear["adv_p50"]:
        if mask_clear["nifty50"] and mask_clear["adv_p50"]:
            mean_delta = {}
            for mask in ("nifty50", "adv_p50"):
                mean_delta[mask] = float(
                    np.mean([fold_rows[f]["masks"][mask]["h5_delta"] for f in folds])
                )
            if mean_delta["adv_p50"] > mean_delta["nifty50"]:
                chosen_mask = "adv_p50"
            else:
                chosen_mask = "nifty50"  # tie → PIT Nifty-50
        elif mask_clear["nifty50"]:
            chosen_mask = "nifty50"
        else:
            chosen_mask = "adv_p50"
        a3_ok = True
        authorized.append("A3")

    hard_stop = not authorized
    peek1 = authorized[0] if authorized else None
    peek2 = authorized[1] if len(authorized) > 1 else None
    return {
        "authorized": authorized,
        "a1": a1_ok and bool(folds),
        "a2": a2_ok and bool(folds),
        "a3": a3_ok,
        "a3_mask": chosen_mask,
        "mask_clear": mask_clear,
        "hard_stop": hard_stop,
        "peek1": peek1,
        "peek2": peek2,
        "folds": folds,
    }


def reprint_holdout_h5_fail(metrics: list[MetricResult]) -> bool:
    for m in metrics:
        if m.name == "H5" and m.side == "short":
            return m.gate_pass is False
    return True


def score_val_panel(
    fold_val: pl.DataFrame, model: GBMHorizonModel
) -> pl.DataFrame:
    scored = fold_val.with_columns(
        horizon_score=pl.Series(model.predict(fold_val)),
        horizon_direction=pl.lit("short"),
    )
    return prepare_eval_panel(scored, "short")


# LightGBM has no YetiRank; rank_xendcg is the locked approx-NDCG objective (not lambdarank).
A2_PARAMS = {
    **{k: v for k, v in SHORT_PARAMS.items() if k not in ("objective", "alpha", "metric")},
    "objective": "rank_xendcg",
    "metric": "ndcg",
    "label_gain": [0, 1, 3],
    "importance_type": "gain",
}


class A2ListwiseShort:
    """True listwise Short ranker (A2 peek). Rank by NDCG@3; higher raw = more TP."""

    direction = "short"

    def __init__(self) -> None:
        self.features = list(SHORT_FEATURES)
        self.ranker = lgb.LGBMRanker(**A2_PARAMS)
        self.is_fitted = False

    def fit(self, fold_train: pl.DataFrame, fold_val: pl.DataFrame) -> float:
        train = fold_train.with_columns(_tb_grade_expr()).drop_nulls(
            subset=self.features + ["tb_grade"]
        )
        val = fold_val.with_columns(_tb_grade_expr()).drop_nulls(
            subset=self.features + ["tb_grade"]
        )
        train, group_train = _sort_rank_groups(train)
        val, group_val = _sort_rank_groups(val)
        keep_tr = group_train >= RANK_MIN_GROUP
        keep_va = group_val >= RANK_MIN_GROUP
        if not keep_tr.any() or not keep_va.any():
            raise ValueError("A2 listwise: empty rank groups")
        train_dates = train.select("date").unique(maintain_order=True).to_series().to_list()
        val_dates = val.select("date").unique(maintain_order=True).to_series().to_list()
        train = train.filter(
            pl.col("date").is_in([d for d, ok in zip(train_dates, keep_tr) if ok])
        )
        val = val.filter(
            pl.col("date").is_in([d for d, ok in zip(val_dates, keep_va) if ok])
        )
        train, group_train = _sort_rank_groups(train)
        val, group_val = _sort_rank_groups(val)
        X_train = train.select(self.features).to_numpy()
        y_train = train["tb_grade"].to_numpy()
        X_val = val.select(self.features).to_numpy()
        y_val = val["tb_grade"].to_numpy()
        self.ranker.fit(
            X_train,
            y_train,
            group=group_train,
            sample_weight=episode_balanced_weights(train),
            eval_X=X_val,
            eval_y=y_val,
            eval_group=[group_val],
            eval_at=[3],
            callbacks=[lgb.early_stopping(stopping_rounds=40, verbose=False)],
        )
        self.is_fitted = True
        raw = self.ranker.predict(X_val)
        ic, _ = spearmanr(raw, (val["tb_label_short"] == 1).to_numpy())
        return float(ic) if ic == ic else 0.0

    def predict(self, X: pl.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("A2 listwise must be fitted before prediction.")
        raw = self.ranker.predict(X.select(self.features).to_numpy())
        # Short eval_score = -horizon_score; negate so higher NDCG score ranks first.
        return -np.asarray(raw, dtype=float)


def fit_short_a2_listwise(
    train_df: pl.DataFrame,
    cv_kwargs: dict[str, Any] | None = None,
) -> tuple[A2ListwiseShort | None, dict]:
    """Walk-forward A2 listwise; return last-fold model (same cadence as path-EV peek)."""
    sleeve, _feats = prepare_short_sleeve(train_df)
    sleeve = sleeve.with_columns(_tb_grade_expr()).drop_nulls(subset=["tb_grade"])
    diagnostics = sleeve_sample_diagnostics(sleeve)
    if sleeve.height == 0:
        return None, {"diagnostics": diagnostics}
    if "date_only" not in train_df.columns:
        train_df = train_df.with_columns(date_only=pl.col("date").dt.date())
    calendar_dates = (
        train_df.select("date_only").unique().sort("date_only").to_series().to_list()
    )
    models: list[A2ListwiseShort] = []
    val_ics: list[float] = []
    for fold_train, fold_val, fold_test in get_purged_cv_splits(
        sleeve, calendar_dates=calendar_dates, **(cv_kwargs or {})
    ):
        if min(fold_train.height, fold_val.height) == 0:
            continue
        model = A2ListwiseShort()
        val_ic = model.fit(fold_train, fold_val)
        val_ics.append(val_ic)
        models.append(model)
    if not models:
        return None, {"diagnostics": diagnostics, "n_splits": 0}
    mean_val = sum(val_ics) / len(val_ics)
    print(
        f"A2 listwise mean val IC_tb={mean_val:.4f} ({len(models)} folds) "
        f"objective=rank_xendcg label_gain=[0,1,3]"
    )
    return models[-1], {
        "mean_ic_tb": mean_val,
        "diagnostics": diagnostics,
        "n_splits": len(models),
        "objective": "rank_xendcg",
        "label_gain": list(NDCG_LABEL_GAIN),
    }


def metric_map(metrics: list[MetricResult]) -> dict[str, MetricResult]:
    return {m.name: m for m in metrics if m.side == "short"}


def peek_h5_clear(metrics: list[MetricResult]) -> bool:
    h5 = metric_map(metrics).get("H5")
    return bool(h5 is not None and h5.gate_pass is True)


def peek_no_h123_regression(
    peek: list[MetricResult], baseline: list[MetricResult]
) -> tuple[bool, str]:
    """Keep H1/H2/H3 PASS if baseline passed. Fail if a companion gate flips PASS->FAIL."""
    p = metric_map(peek)
    b = metric_map(baseline)
    notes: list[str] = []
    ok = True
    for name in ("H1", "H2", "H3"):
        base_pass = b[name].gate_pass is True if name in b else False
        peek_pass = p[name].gate_pass is True if name in p else False
        if base_pass and not peek_pass:
            ok = False
            notes.append(f"{name} PASS->FAIL")
        elif name in p:
            notes.append(f"{name}={'PASS' if peek_pass else 'FAIL'}")
    return ok, "; ".join(notes)
