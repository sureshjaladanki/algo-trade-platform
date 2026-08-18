"""M9 unit tests — implied range + incremental OLS."""

from __future__ import annotations

import numpy as np

from src.horizon.m9.implied_range import (
    DEFAULT_RANGE_KAPPA,
    implied_remaining_range,
    india_vix_to_daily_sigma,
)
from src.horizon.m9.v1_incremental import incremental_range_ols


def test_vix_to_sigma_and_remaining_range_monotone_in_time() -> None:
    sig = india_vix_to_daily_sigma(20.0)
    assert 0.01 < sig < 0.02  # ~20/sqrt(252)/100
    early = implied_remaining_range(20.0, 20, kappa=DEFAULT_RANGE_KAPPA)
    late = implied_remaining_range(20.0, 5, kappa=DEFAULT_RANGE_KAPPA)
    assert early > late > 0


def test_incremental_ols_detects_q50_signal() -> None:
    rng = np.random.default_rng(0)
    n = 2000
    implied = rng.uniform(0.01, 0.04, size=n)
    q50 = implied + rng.normal(0, 0.005, size=n)
    # Realized depends on both; q50 has positive incremental weight.
    y = 0.3 * implied + 0.5 * q50 + rng.normal(0, 0.002, size=n)
    res = incremental_range_ols(y, implied, q50)
    assert res.passed
    assert res.coef_q50 > 0

    # q50 is pure noise → should not pass.
    noise = rng.normal(0, 0.01, size=n)
    y2 = 0.8 * implied + rng.normal(0, 0.002, size=n)
    bad = incremental_range_ols(y2, implied, noise)
    assert not bad.passed or bad.coef_q50 <= 0 or bad.p_q50 >= 0.05


def test_nested_ols_q50_still_tested_when_har_present() -> None:
    rng = np.random.default_rng(1)
    n = 3000
    implied = rng.uniform(0.01, 0.04, size=n)
    har = implied + rng.normal(0, 0.002, size=n)
    q50 = 0.2 * implied + rng.normal(0, 0.01, size=n)
    y = 0.4 * implied + 0.4 * har + 0.5 * q50 + rng.normal(0, 0.002, size=n)
    res = incremental_range_ols(y, implied, q50, extra_controls=har)
    assert res.passed
    assert res.coef_q50 > 0
    assert len(res.coef_controls) == 1

    # q50 is HAR plus noise; y does not depend on that noise → no increment.
    y_abs = 0.5 * implied + 0.5 * har + rng.normal(0, 0.002, size=n)
    q_copy = har + rng.normal(0, 1e-6, size=n)
    absorbed = incremental_range_ols(y_abs, implied, q_copy, extra_controls=har)
    assert not absorbed.passed
