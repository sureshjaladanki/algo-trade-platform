"""Unit tests — M5R Stage C repairs: clock, event freshness, calibration, gates."""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl

from src.horizon.fresh.events import collapse_to_bar, transition_events
from src.horizon.fresh.gates import k3_calibration_ece, k4_martingale_residual
from src.horizon.fresh.opportunity import remaining_session_range
from src.horizon.fresh.stage_c import FreshHorizonModel, geometry_argmax


def _session_bars(day: dt.date, times: list[tuple[int, int]]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "symbol": ["A"] * len(times),
            "date": [dt.datetime.combine(day, dt.time(h, m)) for h, m in times],
            "high": [101.0] * len(times),
            "low": [99.0] * len(times),
            "close": [100.0] * len(times),
            "volume": [1000.0] * len(times),
        }
    )


def test_bars_to_mis_is_monotone_and_positive() -> None:
    """Regression: dt.hour() is Int8, so hour*60 wrapped and scrambled the clock."""
    bars = _session_bars(
        dt.date(2018, 1, 2), [(9, 30), (10, 45), (11, 0), (13, 0), (14, 45), (15, 15)]
    )
    out = remaining_session_range(bars).sort("date")
    btm = out["bars_to_mis"].to_list()
    assert btm == [23, 18, 17, 9, 2, 0]
    assert all(b >= 0 for b in btm)
    # Strictly decreasing through the session — the property the head relies on.
    assert btm == sorted(btm, reverse=True)


def test_transition_events_drops_restatements() -> None:
    """A condition that stays true must not re-emit on every later bar."""
    day = dt.date(2018, 1, 2)
    times = [(10, 15), (10, 30), (10, 45), (13, 0), (13, 15)]
    events = _session_bars(day, times).with_columns(rule_id=pl.lit("prior_day_high"))
    out = transition_events(events).sort("date")
    # Two runs (10:15–10:45 and 13:00–13:15) → two decisions.
    assert out.height == 2
    assert out["date"].dt.hour().to_list() == [10, 13]

    first_only = transition_events(events, first_cross_only=True)
    assert first_only.height == 1


def test_collapse_to_bar_gives_one_row_with_multi_hot() -> None:
    """Four rows per bar differing only in a one-hot are near-duplicates to a GBDT."""
    stamp = dt.datetime(2018, 1, 2, 10, 15)
    events = pl.DataFrame(
        {
            "symbol": ["A", "A"],
            "date": [stamp, stamp],
            "close": [100.0, 100.0],
            "rule_id": ["orb_break_vol", "prior_day_high"],
            "event_id": ["A|1", "A|2"],
        }
    )
    out = collapse_to_bar(events)
    assert out.height == 1
    assert out["n_rules"][0] == 2
    assert out["rule_orb_break_vol"][0] == 1.0
    assert out["rule_prior_day_high"][0] == 1.0
    assert out["rule_vwap_reclaim"][0] == 0.0


def test_calibration_moves_mean_toward_base_rate() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=(1200, 3))
    # TP rate depends on the first feature; SL otherwise. TO is rare.
    p = 1.0 / (1.0 + np.exp(-x[:, 0]))
    labels = np.where(rng.random(1200) < p, 1, -1)
    labels[rng.random(1200) < 0.05] = 0

    model = FreshHorizonModel(n_estimators=60).fit(x[:800], labels[:800])
    raw = model.predict_proba(x[800:])
    model.calibrate(x[600:800], labels[600:800])
    cal = model.predict_proba(x[800:])

    assert raw.shape == cal.shape == (400, 3)
    assert np.allclose(cal.sum(axis=1), 1.0)
    realized = float((labels[800:] == 1).mean())
    assert abs(cal[:, 2].mean() - realized) <= abs(raw[:, 2].mean() - realized) + 0.02


def test_k4_martingale_residual_centres_on_zero_for_a_martingale() -> None:
    """Under the driftless null E[path_ret]=0 at any geometry and any TO mass."""
    rng = np.random.default_rng(1)
    g, s = 0.02, 0.01
    p_tp = s / (g + s)
    hit = rng.random(4000) < p_tp
    path = np.where(hit, g, -s)
    sessions = np.repeat(np.arange(200), 20)
    res = k4_martingale_residual(path, sessions, fold="T", n_boot=100, seed=0)
    assert abs(res.value) < 2e-3
    assert res.passed is False  # zero edge must not clear a CI-LB>0 gate


def test_k3_ece_rewards_a_calibrated_head() -> None:
    rng = np.random.default_rng(2)
    p = rng.uniform(0.1, 0.6, size=3000)
    good = k3_calibration_ece(p, rng.binomial(1, p).astype(float), fold="T", n_boot=50)
    bad = k3_calibration_ece(
        p, rng.binomial(1, np.clip(p + 0.2, 0, 1)).astype(float), fold="T", n_boot=50
    )
    assert good.passed
    assert not bad.passed
    assert bad.value > good.value


def test_k3_ece_requires_max_gap_inside_null_band() -> None:
    """Blueprint §10.3: ECE ≤ 3 pp is not enough if max gap beats its null."""
    rng = np.random.default_rng(3)
    n = 2000
    p = np.full(n, 0.33)
    # Nine-tenths well calibrated; one decile systematically off by ~20 pp.
    y = rng.binomial(1, p).astype(float)
    p_hat = p.copy()
    p_hat[:200] = 0.55
    res = k3_calibration_ece(p_hat, y, fold="T", n_boot=80, seed=0)
    assert "max_gap_pp" in res.note
    # Either ECE or max-gap vs null must fail this constructed bias.
    assert not res.passed


def test_geometry_argmax_requires_geometry_conditional_probabilities() -> None:
    """Invariant probabilities always pick widest TP / tightest SL — the M5 defect."""
    flat = geometry_argmax(lambda _tm, _sm: (0.45, 0.35, 0.20), range_hat=0.03)
    g_flat, s_flat, _ = flat
    assert g_flat == 0.6 * 0.03  # max tp_mult
    assert s_flat == 0.2 * 0.03  # min sl_mult

    # A head that knows a wide target is less likely to be reached prefers a
    # narrower geometry, which is the whole point of passing multipliers in.
    def conditional(tm: float, sm: float) -> tuple[float, float, float]:
        return (0.62 - 0.7 * tm, 0.35 + 0.2 * sm, 0.03)

    g_cond, _s_cond, _ev = geometry_argmax(conditional, range_hat=0.03)
    assert g_cond < g_flat
