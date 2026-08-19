import numpy as np

from src.events.stats import (
    Interval,
    clip_disaster,
    fold_sign_pass,
    mde_bps,
    session_block_mean_ci,
    three_way_verdict,
)


def test_clip_disaster_keeps_the_row() -> None:
    out = clip_disaster(np.array([-800.0, 10.0, -100.0]))
    assert list(out) == [-500.0, 10.0, -100.0]


def test_mde_at_n4_is_half_n1() -> None:
    assert abs(mde_bps(600.0, 4) - mde_bps(600.0, 1) / 2.0) < 1e-9


def test_session_block_mean_matches_plain_mean() -> None:
    values = np.array([1.0, 3.0, 5.0])
    sessions = np.array([1, 2, 3])
    rng = np.random.default_rng(0)
    interval = session_block_mean_ci(values, sessions, n_boot=200, rng=rng)
    assert interval.point == 3.0
    assert interval.n == 3


def test_verdict_inconclusive_when_mde_covers_effect() -> None:
    interval = Interval(point=50.0, ci_low=10.0, ci_high=90.0, n=10, n_sessions=10)
    assert three_way_verdict(interval, mde=50.0, sign_ok=True) == "INCONCLUSIVE"


def test_verdict_pass_requires_ci_and_sign() -> None:
    interval = Interval(point=200.0, ci_low=20.0, ci_high=400.0, n=10, n_sessions=10)
    assert three_way_verdict(interval, mde=50.0, sign_ok=True) == "PASS"
    assert three_way_verdict(interval, mde=50.0, sign_ok=False) == "INCONCLUSIVE"


def test_verdict_fail_when_upper_bound_below_hurdle() -> None:
    interval = Interval(point=-80.0, ci_low=-120.0, ci_high=-10.0, n=10, n_sessions=10)
    assert three_way_verdict(interval, mde=20.0, sign_ok=False) == "FAIL"


def test_fold_sign_majority() -> None:
    ok, n_pos, n_el = fold_sign_pass(
        {"2018": 1.0, "2019": 2.0, "2020": -1.0},
        {"2018": 3, "2019": 4, "2020": 2},
    )
    assert ok is True
    assert n_pos == 2
    assert n_el == 3
