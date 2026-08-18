"""M5P-b unit tests — pooled K5, c_eff EV, admit-power declaration, vertical-only."""

from __future__ import annotations

import numpy as np

from src.horizon.fresh.friction import ARCHIVE_C_STAR, BPS, C_STAR
from src.horizon.fresh.gates import (
    declare_admit_power,
    k5_economics,
    k5_pooled,
    path_ev_net,
)
from src.horizon.fresh.stage_c import expected_ev_net
from src.labels.fresh_barrier import (
    MIS_VERTICAL_ONLY_LONG_GEOMETRY,
    MIS_VERTICAL_ONLY_SHORT_GEOMETRY,
    MIS_WIDE_LONG_GEOMETRY,
)


def test_expected_ev_net_accepts_row_level_c_eff() -> None:
    flat = expected_ev_net(0.4, 0.4, 0.2, 0.02, 0.01, cost=C_STAR)
    cheap = expected_ev_net(0.4, 0.4, 0.2, 0.02, 0.01, cost=0.001)
    assert float(cheap) > float(flat)

    costs = np.array([0.001, 0.002, 0.003])
    ev = expected_ev_net(
        np.full(3, 0.4),
        np.full(3, 0.4),
        np.full(3, 0.2),
        np.full(3, 0.02),
        np.full(3, 0.01),
        cost=costs,
    )
    assert ev.shape == (3,)
    assert ev[0] > ev[2]


def test_path_ev_net_scalar_and_array_cost() -> None:
    path = np.array([0.01, -0.005, 0.0])
    flat = path_ev_net(path, C_STAR)
    assert np.allclose(flat, path - C_STAR)
    ceff = np.array([0.001, 0.002, 0.0015])
    row = path_ev_net(path, ceff)
    assert np.allclose(row, path - ceff)
    # Stress companion at archive 30 is a +10 bps haircut vs c*.
    stress = path_ev_net(path, ARCHIVE_C_STAR)
    assert np.allclose(stress, flat - (ARCHIVE_C_STAR - C_STAR))


def test_k5_pooled_requires_sign_and_pooled_lb() -> None:
    rng = np.random.default_rng(0)
    # Eight folds, all positive; pooled mass is clearly above zero.
    fold_points = {f"R{y}": 0.002 for y in range(2017, 2025)}
    n = 2000
    ev = rng.normal(0.002, 0.01, size=n)
    sess = np.repeat(np.arange(200), 10)
    ok = k5_pooled(fold_points, ev, sess, n_boot=50, seed=0)
    assert ok.passed
    assert ok.verdict == "PASS"

    # Same pooled mass but only 3/8 folds positive → sign FAIL.
    weak_sign = {f"R{y}": (0.002 if y < 2020 else -0.001) for y in range(2017, 2025)}
    bad_sign = k5_pooled(weak_sign, ev, sess, n_boot=50, seed=0)
    assert not bad_sign.passed
    assert "sign=3/8" in bad_sign.note

    # All folds positive but pooled mean negative → pooled_LB FAIL.
    neg = rng.normal(-0.003, 0.01, size=n)
    bad_pool = k5_pooled(fold_points, neg, sess, n_boot=50, seed=0)
    assert not bad_pool.passed


def test_k5_pooled_haircut_shifts_ci_by_delta_c() -> None:
    """Constant haircut is a location shift: c=5 CI = c=3 CI − 2 bps (same seed)."""
    rng = np.random.default_rng(0)
    n = 3000
    path = rng.normal(0.005, 0.01, size=n)
    sess = np.repeat(np.arange(300), 10)
    fold_points_3 = {f"R{y}": 0.002 for y in range(2017, 2023)}
    delta = 2.0 / BPS
    fold_points_5 = {k: v - delta for k, v in fold_points_3.items()}
    p3 = k5_pooled(
        fold_points_3,
        path_ev_net(path, 3.0 / BPS),
        sess,
        n_boot=80,
        seed=0,
        min_positive=5,
        min_folds=6,
    )
    p5 = k5_pooled(
        fold_points_5,
        path_ev_net(path, 5.0 / BPS),
        sess,
        n_boot=80,
        seed=0,
        min_positive=5,
        min_folds=6,
    )
    assert np.isclose(p3.value - p5.value, delta)
    assert np.isclose(p3.ci_lo - p5.ci_lo, delta)
    assert np.isclose(p3.ci_hi - p5.ci_hi, delta)


def test_k5_economics_is_report_only() -> None:
    """Per-fold K5 must not claim authority PASS after Rev 3."""
    rng = np.random.default_rng(1)
    ev = rng.normal(0.005, 0.01, size=400)
    sess = np.repeat(np.arange(40), 10)
    g = k5_economics(ev, sess, fold="A", n_boot=50, seed=0)
    assert g.passed is False
    assert "report_only" in g.note
    assert g.mde is not None and g.mde > 0


def test_declare_admit_power_scales_with_n() -> None:
    sparse = declare_admit_power(50, 40)
    dense = declare_admit_power(800, 200)
    assert sparse.expected_mde > dense.expected_mde
    assert sparse.expected_mde_bps > 5.0
    assert "n_eff" in sparse.note


def test_vertical_only_geometry_is_named_and_wider_than_mis_wide() -> None:
    v = MIS_VERTICAL_ONLY_LONG_GEOMETRY
    w = MIS_WIDE_LONG_GEOMETRY
    assert v.mis_vertical and "vertical_only" in v.name
    assert v.sl_floor > w.sl_floor
    assert v.tp_floor > w.tp_floor
    assert MIS_VERTICAL_ONLY_SHORT_GEOMETRY.mis_vertical
    assert MIS_VERTICAL_ONLY_SHORT_GEOMETRY.sl_floor == v.sl_floor
