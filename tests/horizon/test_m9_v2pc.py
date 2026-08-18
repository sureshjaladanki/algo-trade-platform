"""V2p-c — train-locked short residual; selection does not see test realized."""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest

from src.horizon.m9.v2p_range import (
    V2P_POST_OPEN_MIN_TIME,
    first_post_open_clock,
    fit_v2pc_scale,
    select_v2pc_sessions,
    v2pc_paired_values,
)


def _clock_row(
    day: dt.date,
    *,
    q50: float,
    imp: float,
    realized: float,
    t: dt.time = dt.time(9, 45),
) -> dict:
    return {
        "date": dt.datetime.combine(day, t),
        "date_only": day,
        "time_only": t,
        "range_q50": q50,
        "range_imp_vix": imp,
        "remaining_range": realized,
    }


def test_first_post_open_clock_skips_bleed() -> None:
    d1 = dt.date(2018, 1, 2)
    panel = pl.DataFrame(
        [
            _clock_row(d1, q50=0.05, imp=0.02, realized=0.04, t=dt.time(9, 30)),
            _clock_row(d1, q50=0.03, imp=0.02, realized=0.03, t=dt.time(9, 45)),
        ]
    )
    clock = first_post_open_clock(panel)
    assert clock.height == 1
    assert clock["time_only"][0] == V2P_POST_OPEN_MIN_TIME
    assert clock["range_q50"][0] == pytest.approx(0.03)


def test_v2pc_selects_bottom_tercile_richest_implied() -> None:
    rows = []
    for i in range(9):
        # Head well below implied on the last third → those should select.
        q50 = 0.01 if i >= 6 else 0.04
        imp = 0.03
        realized = 0.02 + 0.001 * i
        rows.append(
            _clock_row(dt.date(2018, 1, 2 + i), q50=q50, imp=imp, realized=realized)
        )
    train = pl.DataFrame(rows)
    scale = fit_v2pc_scale(train)
    selected = select_v2pc_sessions(train, scale)
    rich = {dt.date(2018, 1, 8), dt.date(2018, 1, 9), dt.date(2018, 1, 10)}
    assert selected.height >= 2
    assert set(selected["date_only"].to_list()) <= rich
    assert selected["range_q50"].max() == pytest.approx(0.01)


def test_v2pc_selection_ignores_test_realized() -> None:
    train_rows = [
        _clock_row(dt.date(2018, 1, 2 + i), q50=0.02 + 0.002 * i, imp=0.03, realized=0.025)
        for i in range(9)
    ]
    scale = fit_v2pc_scale(pl.DataFrame(train_rows))
    test_a = pl.DataFrame(
        [
            _clock_row(dt.date(2019, 1, 2 + i), q50=0.01 if i < 3 else 0.04, imp=0.03, realized=0.99)
            for i in range(9)
        ]
    )
    test_b = test_a.with_columns(remaining_range=pl.lit(0.001))
    sel_a = select_v2pc_sessions(test_a, scale)
    sel_b = select_v2pc_sessions(test_b, scale)
    assert sel_a["date_only"].to_list() == sel_b["date_only"].to_list()
    assert sel_a.height == 3


def test_v2pc_paired_difference_is_incremental_to_unconditional() -> None:
    universe = pl.DataFrame(
        [
            _clock_row(dt.date(2018, 1, 2), q50=0.02, imp=0.04, realized=0.01),
            _clock_row(dt.date(2018, 1, 3), q50=0.02, imp=0.03, realized=0.02),
            _clock_row(dt.date(2018, 1, 4), q50=0.02, imp=0.05, realized=0.04),
        ]
    )
    selected = universe.head(1)
    y = v2pc_paired_values(selected, universe)
    # imp-R: 0.03, 0.01, 0.01 → all-mean 0.05/3; selected 0.03 − all-mean.
    mu_all = np.mean([0.03, 0.01, 0.01])
    assert y[0] == pytest.approx(0.03 - mu_all)
