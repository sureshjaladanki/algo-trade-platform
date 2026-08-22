"""A1 implied-minus-realized existence. Synthetic observations; no dump peek."""

from datetime import date

import pytest

from src.books.vrp_existence import (
    A1_HYPOTHESIZED,
    A1_N_PLAN,
    A1_SIGMA,
    COST_MULTIPLE,
    SUBPERIODS,
    THETA_TAIL_START,
    VrpObs,
    run_existence_screen,
    screen_declaration,
    sign_stable,
    theta_monthly_expiries,
)
from src.harness import print_mde, reset, run_declared


def setup_function() -> None:
    reset()


def _obs(*, raw: float, cost: float, day: date, used: bool = True) -> VrpObs:
    return VrpObs(
        trade_date=day,
        expiry=day,
        dte=37,
        delta_bucket="20-25",
        tenor="30-45",
        implied=raw + 15.0,
        realized=15.0,
        raw=raw,
        cost_vol=cost,
        net=raw - cost,
        used_spread_cost=used,
    )


def test_a1_mde_clears_at_planned_n() -> None:
    decl = screen_declaration(A1_N_PLAN)
    assert decl.sigma == A1_SIGMA
    assert decl.hypothesized_effect == A1_HYPOTHESIZED
    assert decl.mde == pytest.approx(2.8 * 150.0 / (175**0.5), rel=1e-4)
    assert decl.clears_gate
    n_2012_2023 = 144
    assert screen_declaration(n_2012_2023).clears_gate


def test_existence_requires_two_times_cost_and_sign() -> None:
    rows = [
        _obs(raw=6.0, cost=2.0, day=date(2012, 2, 1)),
        _obs(raw=6.0, cost=2.0, day=date(2015, 2, 1)),
        _obs(raw=6.0, cost=2.0, day=date(2017, 2, 1)),
        _obs(raw=6.0, cost=2.0, day=date(2020, 2, 1)),
        _obs(raw=6.0, cost=2.0, day=date(2022, 2, 1)),
    ]
    print_mde(screen_declaration(175))
    screen = run_declared(lambda: run_existence_screen(rows, [], n_expiries=5))
    assert screen.multiple == pytest.approx(COST_MULTIPLE * 1.5)
    assert screen.exceed_2x is True
    assert screen.sign_stable_net is True
    assert screen.passed is True
    assert screen.n_spread_cost == 5


def test_existence_fails_when_premium_at_cost() -> None:
    rows = [
        _obs(raw=2.0, cost=2.0, day=date(2012, 2, 1)),
        _obs(raw=2.0, cost=2.0, day=date(2015, 2, 1)),
        _obs(raw=2.0, cost=2.0, day=date(2017, 2, 1)),
        _obs(raw=2.0, cost=2.0, day=date(2020, 2, 1)),
        _obs(raw=2.0, cost=2.0, day=date(2022, 2, 1)),
    ]
    screen = run_existence_screen(rows, [], n_expiries=5)
    assert screen.multiple == pytest.approx(1.0)
    assert screen.exceed_2x is False
    assert screen.passed is False


def test_sign_stable_needs_four_of_five_net() -> None:
    rows = [
        (date(2012, 1, 1), date(2014, 5, 31), 1.0, 10),
        (date(2014, 6, 1), date(2016, 10, 31), 1.0, 10),
        (date(2016, 11, 1), date(2019, 3, 31), 1.0, 10),
        (date(2019, 4, 1), date(2021, 8, 31), -0.1, 10),
        (date(2021, 9, 1), date(2023, 12, 31), 1.0, 10),
    ]
    assert sign_stable(rows) is True
    rows[2] = (rows[2][0], rows[2][1], -1.0, 10)
    assert sign_stable(rows) is False


def test_theta_tail_completes_2012_present_not_a_new_spec() -> None:
    assert THETA_TAIL_START == date(2024, 1, 1)
    assert SUBPERIODS[-1] == (date(2021, 9, 1), date(2026, 12, 31))
    got = theta_monthly_expiries(
        [
            date(2023, 12, 15),
            date(2024, 1, 19),
            date(2024, 2, 16),
            date(2026, 9, 18),
        ],
        last_bar=date(2026, 8, 21),
    )
    assert date(2023, 12, 15) not in got
    assert got == [date(2024, 1, 19), date(2024, 2, 16)]
