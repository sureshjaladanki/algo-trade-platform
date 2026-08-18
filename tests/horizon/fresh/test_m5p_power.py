"""M5P unit tests — rolling folds, purge, three-way K4."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.horizon.fresh.folds import (
    DEFAULT_PURGE_CALENDAR_DAYS,
    FOLDS,
    ROLLING_FOLDS,
    apply_purge_cutoff,
    apply_purge_date_filter,
    apply_purge_to_train_end,
    fold_spec,
)
from src.horizon.fresh.friction import C_STAR
from src.horizon.fresh.gates import K4Verdict, k4_three_way, mde_from_ci


def test_rolling_folds_at_least_six_with_purge() -> None:
    assert len(ROLLING_FOLDS) >= 6
    for spec in ROLLING_FOLDS.values():
        assert spec.purge_calendar_days == DEFAULT_PURGE_CALENDAR_DAYS
        assert spec.purge_calendar_days > 0


def test_legacy_folds_ab_still_present() -> None:
    assert set(FOLDS) == {"A", "B"}
    assert fold_spec("A").purge_calendar_days == 0


def test_apply_purge_pulls_train_end_back() -> None:
    assert apply_purge_cutoff(2017, 5) == "2017-12-26"
    assert apply_purge_to_train_end("2017", 5) == "2017-12-26"
    assert apply_purge_to_train_end("2017-12-31", 0) == "2017-12-31"


def test_k4_three_way_pre_registered() -> None:
    assert k4_three_way(0.01, 0.001, 0.02) == K4Verdict.PASS
    assert k4_three_way(-0.01, -0.02, C_STAR * 0.5) == K4Verdict.FAIL
    assert k4_three_way(0.0, -0.01, C_STAR * 1.5) == K4Verdict.INCONCLUSIVE


def test_mde_from_ci_half_width() -> None:
    assert abs(mde_from_ci(-0.002, 0.002) - 0.002) < 1e-12


def test_apply_purge_date_filter_drops_embargo_window() -> None:
    rows = [
        dt.datetime(2017, 12, d, 10, 15) for d in (20, 26, 27, 28, 29, 30, 31)
    ]
    df = pl.DataFrame({"date": rows, "x": list(range(len(rows)))})
    out = apply_purge_date_filter(df, 2017, 5)
    kept = [d.date() for d in out["date"].to_list()]
    assert dt.date(2017, 12, 26) in kept
    assert dt.date(2017, 12, 27) not in kept
    assert dt.date(2017, 12, 31) not in kept
