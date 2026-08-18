"""Causal HAR remaining-range — no look-ahead into session T."""

from __future__ import annotations

import datetime as dt
import math

import polars as pl

from src.horizon.m9.har_range import _PARKINSON_DENOM, attach_causal_har_remaining_range


def test_har_uses_prior_session_only() -> None:
    day1 = dt.date(2018, 1, 2)
    day2 = dt.date(2018, 1, 3)
    rows = []
    for day, hi, lo in ((day1, 110.0, 100.0), (day2, 200.0, 100.0)):
        for h, m in ((10, 0), (10, 15)):
            rows.append(
                {
                    "symbol": "^NSEI",
                    "date": dt.datetime.combine(day, dt.time(h, m)),
                    "date_only": day,
                    "open": 105.0,
                    "high": hi,
                    "low": lo,
                    "close": 105.0,
                    "bars_to_mis": 20,
                }
            )
    panel = attach_causal_har_remaining_range(pl.DataFrame(rows))
    d2 = panel.filter(pl.col("date_only") == day2)
    park_1d = math.sqrt(math.log(110.0 / 100.0) ** 2 / _PARKINSON_DENOM)
    # Session T must not see T's 200/100 range.
    assert d2["park_1d"].to_list()[0] == park_1d
    assert d2["range_har_1d"].to_list()[0] > 0
    park_same_day = math.sqrt(math.log(200.0 / 100.0) ** 2 / _PARKINSON_DENOM)
    assert d2["park_1d"].to_list()[0] < park_same_day
