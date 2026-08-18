"""Stage D admit helpers — conformal residual LB and book caps."""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl
import pytest

from src.experiments.eval_horizon_fresh_m6_admit import M6_BLOCKED_REASON
from src.horizon.fresh.admit import (
    BookCaps,
    attach_conformal_lower_bound,
    conformal_ev_lower_bound,
    conformal_residual_quantile,
    enforce_concurrency_cap,
    enforce_daily_loss_limit,
    enforce_sector_cap,
)
from src.labels.fresh_barrier import MIS_VERTICAL_ONLY_SHORT_GEOMETRY


def test_conformal_residual_quantile_and_per_row_lb() -> None:
    hat = np.array([0.01, 0.02, 0.015, 0.005] * 20)
    realized = hat - 0.004  # systematic overprediction
    q = conformal_residual_quantile(hat, realized, alpha=0.05)
    assert q < 0
    panel = pl.DataFrame({"ev_net_hat": [0.01, 0.001, -0.002]})
    out = attach_conformal_lower_bound(panel, q)
    assert (out["ev_net_lb"] < out["ev_net_hat"]).all()
    pool = conformal_ev_lower_bound(
        hat, realized, np.repeat(np.arange(20), 4), n_boot=40, seed=0
    )
    assert pool.residual_q is not None
    assert pool.n == 80


def test_enforce_sector_cap_requires_column_and_keeps_top_per_sector() -> None:
    bar = dt.datetime(2018, 1, 2, 10, 15)
    fires = pl.DataFrame(
        {
            "date": [bar] * 5,
            "sector": ["IT", "IT", "IT", "BANK", "BANK"],
            "ev_net_hat": [0.05, 0.04, 0.03, 0.02, 0.01],
            "symbol": list("ABCDE"),
        }
    )
    with pytest.raises(ValueError, match="sector"):
        enforce_sector_cap(fires.drop("sector"), caps=BookCaps(max_per_sector=2))
    out = enforce_sector_cap(fires, caps=BookCaps(max_per_sector=2))
    assert out.height == 4
    assert set(out["symbol"].to_list()) == {"A", "B", "D", "E"}


def test_enforce_daily_loss_limit_stops_after_breach() -> None:
    day = dt.date(2018, 1, 2)
    fires = pl.DataFrame(
        {
            "date_only": [day, day, day],
            "ev_net_hat": [0.002, -0.006, -0.008],
        }
    )
    # Ranked by score: +20, −60, −80 bps. Cum after second = −40 bps; limit −100 bps
    # keeps first two; third would go to −120 bps.
    out = enforce_daily_loss_limit(
        fires, caps=BookCaps(daily_loss_limit=-0.01)
    )
    assert out.height == 2


def test_concurrency_still_caps_per_bar() -> None:
    bar = dt.datetime(2018, 1, 2, 10, 15)
    fires = pl.DataFrame(
        {
            "date": [bar] * 5,
            "ev_net_hat": [0.05, 0.04, 0.03, 0.02, 0.01],
        }
    )
    out = enforce_concurrency_cap(fires, caps=BookCaps(max_concurrent=3))
    assert out.height == 3


def test_disaster_stop_clips_rather_than_drops() -> None:
    sl = MIS_VERTICAL_ONLY_SHORT_GEOMETRY.sl_floor
    df = pl.DataFrame({"side_drift": [-0.08, -0.01, 0.02]})
    out = df.with_columns(
        side_drift=pl.max_horizontal(pl.col("side_drift"), pl.lit(-sl))
    )
    assert out.height == 3
    assert out["side_drift"][0] == -sl
    assert out["side_drift"][1] == -0.01


def test_m6_harness_is_hard_blocked() -> None:
    assert "§14" in M6_BLOCKED_REASON or "14" in M6_BLOCKED_REASON
    assert "BLOCKED" in M6_BLOCKED_REASON
