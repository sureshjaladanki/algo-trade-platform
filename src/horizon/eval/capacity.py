"""AUDIT-ONLY (fresh M0 quarantine) — Short capacity Phase 1.

See docs/archive/horizon-fresh-quarantine-index.md.
"""

from __future__ import annotations

from typing import Any

import lightgbm as lgb
import numpy as np
import polars as pl
from scipy.stats import spearmanr

from src.horizon.eval.architecture import (
    h5_h2_proxy,
    last_purged_split,
    metric_map,
    peek_h5_clear,
    prepare_short_sleeve,
    reprint_holdout_h5_fail,
    score_val_panel,
)
from src.horizon.eval.bar_stats import per_bar_topk_stats
from src.horizon.eval.constants import K_SHORT, MIN_BARS_SHORT, MetricResult
from src.horizon.horizon_model import (
    LONG_FEATURES,
    SHORT_FEATURES,
    SHORT_PARAMS,
    GBMHorizonModel,
    episode_balanced_weights,
    get_purged_cv_splits,
    sleeve_sample_diagnostics,
)
from src.pipelines.horizon_pipeline import SLEEVES, _fit_sleeve_mask, _path_ev_target

# Phase-1 cuts (capacity charter — locked).
U1_RATIO_MAX = 0.60
U1_REL_MULT = 1.25
U1_GAP_MAX = 0.05
U1_H5_DELTA_MIN = 0.010
U2_RATIO_MAX = 0.55
U2_H5_DELTA_MIN = 0.015
R1_GAP_MIN = 0.08
R1_H5_DELTA_MIN = 0.010

# MUST_FIX (dual-judge 2026-08-15).
MIN_VAL_BARS = MIN_BARS_SHORT  # 150
MIN_VAL_SESS = 10
STABILITY_SEEDS = (42, 7)
N_BOOT_DELTA = 200
MCS_BASE = 400
MCS_LONG = 300

PARAM_SLICES: dict[str, dict[str, float | int]] = {
    "U1": {"min_child_samples": 300},
    "U2": {"min_child_samples": 200},
    "R1": {"min_child_samples": 500, "reg_lambda": 10.0},
}


def prepare_long_sleeve(df: pl.DataFrame) -> tuple[pl.DataFrame, list[str]]:
    cfg = SLEEVES["long"]
    feat_list = list(LONG_FEATURES)
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


def _make_short_model(
    overrides: dict[str, float | int] | None = None,
    seed: int = 42,
) -> GBMHorizonModel:
    model = GBMHorizonModel(direction="short")
    params = {**model.params, **(overrides or {}), "random_state": seed}
    model.params = params
    model.model = lgb.LGBMRegressor(**params)
    return model


def _spearman(y_hat: np.ndarray, y: np.ndarray) -> float:
    ic, _ = spearmanr(y_hat, y)
    return float(ic) if np.isfinite(ic) else 0.0


def fit_short_path_ev_slice(
    fold_train: pl.DataFrame,
    fold_val: pl.DataFrame,
    overrides: dict[str, float | int] | None = None,
    seed: int = 42,
) -> tuple[GBMHorizonModel, dict[str, float]]:
    """Single last-fold fit under a locked param slice (Phase 1 val authorize)."""
    feat_list = list(SHORT_FEATURES)
    model = _make_short_model(overrides, seed=seed)
    model.fit(
        X_train=fold_train,
        y_train=fold_train["path_ev_y"],
        X_val=fold_val,
        y_val=fold_val["path_ev_y"],
        features=feat_list,
        train_weight=episode_balanced_weights(fold_train),
    )
    X_tr = fold_train.select(feat_list).to_numpy()
    X_va = fold_val.select(feat_list).to_numpy()
    y_tr = fold_train["path_ev_y"].to_numpy()
    y_va = fold_val["path_ev_y"].to_numpy()
    # Fit gap uses calibrated scores (same score surface as H5-proxy).
    ic_train = _spearman(model.predict(fold_train), y_tr)
    ic_val = _spearman(model.predict(fold_val), y_va)
    # Raw booster IC kept for report only.
    ic_train_raw = _spearman(model.model.predict(X_tr), y_tr)
    ic_val_raw = _spearman(model.model.predict(X_va), y_va)
    stats = {
        "ic_train": ic_train,
        "ic_val": ic_val,
        "gap": ic_train - ic_val,
        "ic_train_raw": ic_train_raw,
        "ic_val_raw": ic_val_raw,
    }
    return model, stats


def fit_short_walkforward_slice(
    train_df: pl.DataFrame,
    overrides: dict[str, float | int] | None = None,
    seed: int = 42,
) -> tuple[GBMHorizonModel | None, dict[str, Any]]:
    """Full purged walk-forward Short fit under a param slice (peek path)."""
    sleeve, feat_list = prepare_short_sleeve(train_df)
    diagnostics = sleeve_sample_diagnostics(sleeve)
    if sleeve.height == 0:
        return None, {"diagnostics": diagnostics, "n_splits": 0}
    if "date_only" not in train_df.columns:
        train_df = train_df.with_columns(date_only=pl.col("date").dt.date())
    calendar_dates = (
        train_df.select("date_only").unique().sort("date_only").to_series().to_list()
    )
    models: list[GBMHorizonModel] = []
    val_ics: list[float] = []
    for fold_train, fold_val, fold_test in get_purged_cv_splits(
        sleeve, calendar_dates=calendar_dates
    ):
        if min(fold_train.height, fold_val.height) == 0:
            continue
        model = _make_short_model(overrides, seed=seed)
        val_ic = model.fit(
            X_train=fold_train,
            y_train=fold_train["path_ev_y"],
            X_val=fold_val,
            y_val=fold_val["path_ev_y"],
            features=feat_list,
            train_weight=episode_balanced_weights(fold_train),
        )
        val_ics.append(val_ic)
        models.append(model)
    if not models:
        return None, {"diagnostics": diagnostics, "n_splits": 0}
    return models[-1], {
        "mean_ic": float(np.mean(val_ics)),
        "diagnostics": diagnostics,
        "n_splits": len(models),
        "overrides": dict(overrides or {}),
        "seed": seed,
    }


def bars_in_date_window(sleeve: pl.DataFrame, window: pl.DataFrame) -> int:
    d0 = window.select(pl.col("date_only").min()).item()
    d1 = window.select(pl.col("date_only").max()).item()
    return sleeve.filter(
        (pl.col("date_only") >= d0) & (pl.col("date_only") <= d1)
    ).height


def leaf_occupancy_report(model: GBMHorizonModel, fold_train: pl.DataFrame) -> dict:
    """Mean / P10 train samples per leaf (report-only; skip if booster unavailable)."""
    booster = getattr(model.model, "booster_", None)
    if booster is None:
        return {"skipped": True, "note": "booster_ unavailable"}
    X = fold_train.select(list(SHORT_FEATURES)).to_numpy()
    leaf_idx = booster.predict(X, pred_leaf=True)
    if leaf_idx.ndim == 1:
        leaf_idx = leaf_idx.reshape(-1, 1)
    # Use last tree only — cheap occupancy snapshot.
    last = leaf_idx[:, -1]
    _, counts = np.unique(last, return_counts=True)
    return {
        "skipped": False,
        "n_leaves_used": int(counts.size),
        "mean_samples": float(counts.mean()),
        "p10_samples": float(np.quantile(counts, 0.10)),
    }


def bootstrap_h5_delta_ci(
    panel_base: pl.DataFrame,
    panel_alt: pl.DataFrame,
    n_boot: int = N_BOOT_DELTA,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Session-block bootstrap of mean(H5_alt − H5_base); returns (point, lo, hi)."""
    s0 = per_bar_topk_stats(panel_base, K_SHORT).select(
        ["date", "date_only", pl.col("h5").alias("h5_0")]
    )
    s1 = per_bar_topk_stats(panel_alt, K_SHORT).select(
        ["date", pl.col("h5").alias("h5_1")]
    )
    joined = s0.join(s1, on="date", how="inner").filter(
        pl.col("h5_0").is_finite() & pl.col("h5_1").is_finite()
    )
    if joined.height == 0:
        return float("nan"), float("nan"), float("nan")
    delta = (joined["h5_1"] - joined["h5_0"]).to_numpy()
    point = float(delta.mean())
    sessions = joined["date_only"].to_numpy()
    uniq = np.unique(sessions)
    rng = np.random.default_rng(seed)
    boots: list[float] = []
    for _ in range(n_boot):
        draw = rng.choice(uniq, size=uniq.size, replace=True)
        mask = np.isin(sessions, draw)
        if not mask.any():
            continue
        boots.append(float(delta[mask].mean()))
    if not boots:
        return point, float("nan"), float("nan")
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return point, float(lo), float(hi)


def _finite_le(value: float, cap: float) -> bool:
    return np.isfinite(value) and value <= cap


def _finite_ge(value: float, floor: float) -> bool:
    return np.isfinite(value) and value >= floor


def _finite_gt(value: float, floor: float) -> bool:
    return np.isfinite(value) and value > floor


def val_min_n_clear(n_bars: int, n_sess: int) -> bool:
    return n_bars >= MIN_VAL_BARS and n_sess >= MIN_VAL_SESS


def robustness_clear(
    delta_point: float,
    delta_cut: float,
    boot_lo: float,
    seed7_delta: float | None,
) -> tuple[bool, str]:
    """
    MUST_FIX: point estimate alone is forbidden.

    Pass if point ≥ cut AND (bootstrap CI LB > 0 OR two-seed also ≥ cut).
    """
    if not _finite_ge(delta_point, delta_cut):
        return False, "point_fail"
    boot_ok = np.isfinite(boot_lo) and boot_lo > 0.0
    seed_ok = seed7_delta is not None and _finite_ge(seed7_delta, delta_cut)
    if boot_ok:
        return True, "bootstrap_lb>0"
    if seed_ok:
        return True, "two_seed"
    return False, "robustness_fail"


def run_phase1_fold_diagnostics(
    train_df: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """
    Last-fold Short capacity diagnosis (0 peeks).

    Returns fold_train, fold_val, diagnostics dict for authorize().
    """
    short_sleeve, _ = prepare_short_sleeve(train_df)
    long_sleeve, _ = prepare_long_sleeve(train_df)
    short_diag = sleeve_sample_diagnostics(short_sleeve)
    long_diag = sleeve_sample_diagnostics(long_sleeve)
    split = last_purged_split(short_sleeve, train_df)
    if split is None:
        raise RuntimeError("capacity Phase 1: no purged split for Short sleeve")
    fold_train, fold_val, _fold_test = split
    if min(fold_train.height, fold_val.height) == 0:
        raise RuntimeError("capacity Phase 1: empty last-fold train/val")

    n_s = fold_train.height
    n_l = bars_in_date_window(long_sleeve, fold_train)
    ratio = n_s / n_l if n_l > 0 else float("nan")
    rel400 = MCS_BASE / n_s if n_s else float("nan")
    rel300_l = MCS_LONG / n_l if n_l else float("nan")
    rel300_s = 300 / n_s if n_s else float("nan")
    rel200_s = 200 / n_s if n_s else float("nan")

    slice_stats: dict[str, dict[str, Any]] = {}
    # Baseline + U/R at seed 42.
    for name, overrides in (
        ("base", None),
        ("U1", PARAM_SLICES["U1"]),
        ("U2", PARAM_SLICES["U2"]),
        ("R1", PARAM_SLICES["R1"]),
    ):
        model, fit = fit_short_path_ev_slice(fold_train, fold_val, overrides, seed=42)
        panel = score_val_panel(fold_val, model)
        h5, h2, n_bars, n_sess = h5_h2_proxy(panel)
        leaf = leaf_occupancy_report(model, fold_train) if name == "base" else None
        slice_stats[name] = {
            **fit,
            "h5": h5,
            "h2": h2,
            "val_bars_proxy": n_bars,
            "val_sess_proxy": n_sess,
            "panel": panel,
            "model": model,
            "leaf": leaf,
            "params": dict(SHORT_PARAMS if overrides is None else {**SHORT_PARAMS, **overrides}),
        }

    base = slice_stats["base"]
    # Bootstrap deltas vs baseline (seed-42 panels).
    for name in ("U1", "U2", "R1"):
        point, lo, hi = bootstrap_h5_delta_ci(base["panel"], slice_stats[name]["panel"])
        slice_stats[name]["delta_h5"] = point
        slice_stats[name]["delta_h5_lo"] = lo
        slice_stats[name]["delta_h5_hi"] = hi

    # Two-seed only when point estimate clears its cut (or near for R1 gap lane).
    for name, cut in (("U1", U1_H5_DELTA_MIN), ("U2", U2_H5_DELTA_MIN), ("R1", R1_H5_DELTA_MIN)):
        need = _finite_ge(slice_stats[name]["delta_h5"], cut) or (
            name == "R1" and _finite_ge(base["gap"], R1_GAP_MIN)
        )
        if not need:
            slice_stats[name]["seed7_delta"] = None
            continue
        model7, _ = fit_short_path_ev_slice(
            fold_train, fold_val, PARAM_SLICES[name], seed=7
        )
        panel7 = score_val_panel(fold_val, model7)
        h5_7, h2_7, _, _ = h5_h2_proxy(panel7)
        slice_stats[name]["seed7_h5"] = h5_7
        slice_stats[name]["seed7_h2"] = h2_7
        slice_stats[name]["seed7_delta"] = (
            h5_7 - base["h5"]
            if np.isfinite(h5_7) and np.isfinite(base["h5"])
            else float("nan")
        )

    val_diag = sleeve_sample_diagnostics(fold_val)
    out = {
        "n_train_short": n_s,
        "n_train_long": n_l,
        "ratio": ratio,
        "rel400": rel400,
        "rel300_l": rel300_l,
        "rel300_s": rel300_s,
        "rel200_s": rel200_s,
        "rel_vs_long": rel400 / rel300_l if rel300_l and np.isfinite(rel300_l) else float("nan"),
        "gap": base["gap"],
        "h5v0": base["h5"],
        "h2v0": base["h2"],
        "val_bars": fold_val.height,
        "val_sess": val_diag["sessions"],
        "val_min_n_clear": val_min_n_clear(fold_val.height, val_diag["sessions"]),
        "short_diag": short_diag,
        "long_diag": long_diag,
        "leaf": base["leaf"],
        "slices": {k: {kk: vv for kk, vv in v.items() if kk not in ("panel", "model")}
                   for k, v in slice_stats.items()},
        # Keep panels for peek companion only if needed — drop heavy objects for authorize.
        "_panels": {k: v["panel"] for k, v in slice_stats.items()},
        "_models": {k: v["model"] for k, v in slice_stats.items()},
    }
    # Flatten proxy fields used by authorize.
    for name in ("U1", "U2", "R1"):
        s = slice_stats[name]
        out[f"h5v_{name}"] = s["h5"]
        out[f"h2v_{name}"] = s["h2"]
        out[f"delta_{name}"] = s["delta_h5"]
        out[f"delta_{name}_lo"] = s["delta_h5_lo"]
        out[f"delta_{name}_hi"] = s["delta_h5_hi"]
        out[f"seed7_delta_{name}"] = s.get("seed7_delta")
        out[f"gap_{name}"] = s["gap"]
    return fold_train, fold_val, out


def authorize_capacity_levers(fold_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Dual-fold numeric gate with MUST_FIX robustness. Tie-break U1 → U2 → R1."""
    folds = [f for f in ("A", "B") if f in fold_rows]
    if len(folds) < 2:
        return {
            "authorized": [],
            "hard_stop": True,
            "peek1": None,
            "peek2": None,
            "u1": False,
            "u2": False,
            "r1": False,
            "notes": ["need both folds A and B"],
            "folds": folds,
        }

    def both(pred) -> bool:
        return all(pred(fold_rows[f]) for f in folds)

    val_n_ok = both(lambda r: bool(r["val_min_n_clear"]))

    u1_mass = both(
        lambda r: _finite_le(r["ratio"], U1_RATIO_MAX)
        and _finite_ge(r["rel400"], U1_REL_MULT * r["rel300_l"])
        and _finite_le(r["gap"], U1_GAP_MAX)
    )
    u1_point = both(
        lambda r: _finite_ge(r["delta_U1"], U1_H5_DELTA_MIN)
        and _finite_gt(r["h2v_U1"], 0.0)
    )
    u1_robust = both(
        lambda r: robustness_clear(
            r["delta_U1"],
            U1_H5_DELTA_MIN,
            r["delta_U1_lo"],
            r.get("seed7_delta_U1"),
        )[0]
    )
    u1_ok = val_n_ok and u1_mass and u1_point and u1_robust

    # U1 fail solely on +0.010 cut?
    u1_fail_only_delta = (
        val_n_ok
        and u1_mass
        and both(lambda r: _finite_gt(r["h2v_U1"], 0.0))
        and not both(lambda r: _finite_ge(r["delta_U1"], U1_H5_DELTA_MIN))
    )

    u2_alt = both(
        lambda r: _finite_le(r["ratio"], U2_RATIO_MAX)
        and _finite_ge(r["delta_U2"], U2_H5_DELTA_MIN)
        and _finite_gt(r["h2v_U2"], 0.0)
    )
    u2_robust = both(
        lambda r: robustness_clear(
            r["delta_U2"],
            U2_H5_DELTA_MIN,
            r["delta_U2_lo"],
            r.get("seed7_delta_U2"),
        )[0]
    )
    u2_numeric = (u1_ok or u2_alt) and u2_robust and val_n_ok
    # Peek eligibility: U1 authorized OR U1 fails solely on delta while U2 clears.
    u2_peek_ok = u2_numeric and (
        u1_ok or (u1_fail_only_delta and u2_alt and u2_robust)
    )

    r1_gap_lane = both(lambda r: _finite_ge(r["gap"], R1_GAP_MIN))
    r1_delta_lane = both(
        lambda r: _finite_ge(r["delta_R1"], R1_H5_DELTA_MIN)
        and _finite_gt(r["h2v_R1"], 0.0)
    )
    r1_robust = both(
        lambda r: robustness_clear(
            r["delta_R1"],
            R1_H5_DELTA_MIN,
            r["delta_R1_lo"],
            r.get("seed7_delta_R1"),
        )[0]
    )
    # Gap lane can authorize without H5 delta robustness; delta lane needs it.
    r1_ok = val_n_ok and (
        r1_gap_lane or (r1_delta_lane and r1_robust)
    )

    authorized: list[str] = []
    if u1_ok:
        authorized.append("U1")
    if u2_peek_ok:
        authorized.append("U2")
    if r1_ok:
        authorized.append("R1")

    return {
        "authorized": authorized,
        "hard_stop": not authorized,
        "peek1": authorized[0] if authorized else None,
        "peek2": authorized[1] if len(authorized) > 1 else None,
        "u1": u1_ok,
        "u2": u2_peek_ok,
        "r1": r1_ok,
        "u1_mass": u1_mass,
        "u1_point": u1_point,
        "u1_robust": u1_robust,
        "u1_fail_only_delta": u1_fail_only_delta,
        "u2_alt": u2_alt,
        "u2_robust": u2_robust,
        "r1_gap_lane": r1_gap_lane,
        "r1_delta_lane": r1_delta_lane,
        "r1_robust": r1_robust,
        "val_n_ok": val_n_ok,
        "folds": folds,
    }


def peek_no_h123_regression(
    peek: list[MetricResult], baseline: list[MetricResult]
) -> tuple[bool, str]:
    """Keep H1/H2/H3 PASS if baseline passed."""
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


__all__ = [
    "MIN_VAL_BARS",
    "MIN_VAL_SESS",
    "PARAM_SLICES",
    "R1_GAP_MIN",
    "R1_H5_DELTA_MIN",
    "U1_GAP_MAX",
    "U1_H5_DELTA_MIN",
    "U1_RATIO_MAX",
    "U1_REL_MULT",
    "U2_H5_DELTA_MIN",
    "U2_RATIO_MAX",
    "authorize_capacity_levers",
    "fit_short_walkforward_slice",
    "metric_map",
    "peek_h5_clear",
    "peek_no_h123_regression",
    "reprint_holdout_h5_fail",
    "run_phase1_fold_diagnostics",
]
