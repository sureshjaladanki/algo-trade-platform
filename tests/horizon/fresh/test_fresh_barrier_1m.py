"""M5R-b — 1m first-hit resolution and symmetric penetration (blueprint §9.1)."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.labels.fresh_barrier import (
    MIS_WIDE_LONG_GEOMETRY,
    calculate_fresh_long_labels,
    dual_touch_share,
    resolve_fresh_long_first_hit_1m,
)
from src.labels.triple_barrier import TP_PENETRATION


def _session_with_history(*, dual_hi: float, dual_lo: float) -> pl.DataFrame:
    """60 prior sessions of quiet TOD bars so atr_pct is finite, then one dual day."""
    rows: list[dict] = []
    for d in range(1, 62):
        day = dt.date(2018, 1, 2) + dt.timedelta(days=d)
        if day.weekday() >= 5:
            continue
        for h, m in ((10, 15), (10, 30), (10, 45), (11, 0)):
            rows.append(
                {
                    "symbol": "A",
                    "date": dt.datetime.combine(day, dt.time(h, m)),
                    "open": 100.0,
                    "high": 100.2,
                    "low": 99.8,
                    "close": 100.0,
                    "volume": 1_000.0,
                }
            )
    # Probe day: decision 10:15, then a dual-touch 10:30 bar.
    day = dt.date(2018, 4, 2)
    for h, m, hi, lo, close in (
        (10, 15, 100.2, 99.8, 100.0),
        (10, 30, dual_hi, dual_lo, 100.0),
        (10, 45, 100.1, 99.9, 100.0),
        (11, 0, 100.1, 99.9, 100.0),
    ):
        rows.append(
            {
                "symbol": "A",
                "date": dt.datetime.combine(day, dt.time(h, m)),
                "open": 100.0,
                "high": hi,
                "low": lo,
                "close": close,
                "volume": 1_000.0,
            }
        )
    return pl.DataFrame(rows)


def test_dual_touch_15m_flagged_and_breaks_to_sl() -> None:
    """Same 15m bar touching both barriers → SL + dual_touch_15m."""
    stock = _session_with_history(dual_hi=103.5, dual_lo=96.5)
    labeled = calculate_fresh_long_labels(
        stock, None, MIS_WIDE_LONG_GEOMETRY, tp_penetration=0.0, sl_penetration=0.0
    )
    decision = labeled.filter(
        (pl.col("date").dt.date() == dt.date(2018, 4, 2))
        & (pl.col("date").dt.time() == dt.time(10, 15))
        & pl.col("tb_label").is_not_null()
    )
    assert decision.height == 1
    assert decision["tb_label"][0] == -1
    assert bool(decision["dual_touch_15m"][0]) is True
    stats = dual_touch_share(decision)
    assert stats["n_dual"] == 1
    assert stats["dual_touch_share"] == 1.0


def test_symmetric_penetration_blocks_exact_sl_touch() -> None:
    """Symmetric 2 bps penetration: exact SL touch is not a stop."""
    day = dt.date(2018, 1, 2)
    decision = pl.DataFrame(
        {
            "symbol": ["A"],
            "date": [dt.datetime.combine(day, dt.time(10, 15))],
            "entry_px": [100.0],
            "tp_w": [0.02],
            "sl_w": [0.01],
        }
    )
    bars_1m = pl.DataFrame(
        {
            "symbol": ["A", "A"],
            "date": [
                dt.datetime.combine(day, dt.time(10, 16)),
                dt.datetime.combine(day, dt.time(10, 17)),
            ],
            "high": [100.05, 100.05],
            "low": [99.0, 99.0],  # exact −100 bps
            "close": [99.5, 99.5],
        }
    )
    # SL trigger at 100*(1-0.01-0.0002)=98.98 → 99.0 does not stop.
    sym = resolve_fresh_long_first_hit_1m(
        decision, bars_1m, penetration=TP_PENETRATION, max_hold_minutes=30
    )
    assert sym["tb_label"][0] == 0

    touch = resolve_fresh_long_first_hit_1m(
        decision, bars_1m, penetration=0.0, max_hold_minutes=30
    )
    assert touch["tb_label"][0] == -1


def test_1m_resolves_intra_bar_order() -> None:
    """Within one 15m window, earlier 1m TP beats a later 1m SL."""
    day = dt.date(2018, 1, 2)
    decision = pl.DataFrame(
        {
            "symbol": ["A"],
            "date": [dt.datetime.combine(day, dt.time(10, 15))],
            "entry_px": [100.0],
            "tp_w": [0.02],
            "sl_w": [0.01],
        }
    )
    bars_1m = pl.DataFrame(
        {
            "symbol": ["A"] * 4,
            "date": [
                dt.datetime.combine(day, dt.time(10, 16)),
                dt.datetime.combine(day, dt.time(10, 17)),
                dt.datetime.combine(day, dt.time(10, 18)),
                dt.datetime.combine(day, dt.time(10, 19)),
            ],
            "high": [100.1, 102.5, 100.0, 100.0],
            "low": [99.9, 100.0, 98.5, 99.0],
            "close": [100.0, 102.0, 99.0, 99.5],
        }
    )
    out = resolve_fresh_long_first_hit_1m(decision, bars_1m, penetration=0.0)
    assert out["tb_label"][0] == 1
    assert out["path_ret"][0] == 0.02
    assert bool(out["dual_touch_1m"][0]) is False
