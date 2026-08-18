"""M4R registry + candidate-event causality smoke tests."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.horizon.fresh.candidate_events import build_candidate_event_panel
from src.horizon.fresh.rule_registry import RULE_REGISTRY, get_rule, rules_for, sleeve_id


def test_registry_has_both_sides_and_reversion() -> None:
    assert any(r.side == "short" for r in RULE_REGISTRY)
    assert any(r.family == "reversion" for r in RULE_REGISTRY)
    assert get_rule("vwap_reclaim").side == "long"
    assert sleeve_id("reversion", "long") == "long_reversion"
    assert len(rules_for(family="reversion", side="short")) >= 1


def test_candidate_events_no_lookahead_on_prior_day() -> None:
    """Prior-day high must come from a completed prior session only."""
    rows = []
    for day_offset, hi in ((0, 100.0), (1, 105.0)):
        day = dt.date(2018, 1, 2) + dt.timedelta(days=day_offset)
        for h, m in ((10, 15), (10, 30), (11, 0)):
            rows.append(
                {
                    "symbol": "A",
                    "date": dt.datetime.combine(day, dt.time(h, m)),
                    "open": 100.0,
                    "high": hi,
                    "low": 99.0,
                    "close": 100.5 if (day_offset == 1 and h == 10 and m == 30) else 100.0,
                    "volume": 2_000.0,
                }
            )
    # Day-1 10:30 close 100.5 cannot break prior high 100 unless prior session exists.
    # Day-2 with high 105: break of prior 100 is allowed at close > 100.
    bars = pl.DataFrame(rows)
    # Need ORB bars too — add 09:45/10:00 on each day.
    extra = []
    for day_offset in (0, 1):
        day = dt.date(2018, 1, 2) + dt.timedelta(days=day_offset)
        for h, m in ((9, 45), (10, 0)):
            extra.append(
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
    bars = pl.concat([bars, pl.DataFrame(extra)]).sort("date")
    ev = build_candidate_event_panel(bars)
    pdh = ev.filter(pl.col("rule_id") == "prior_day_high")
    # Only day 2 can fire (prior high from day 1).
    assert pdh.height >= 1
    assert all(d.date() == dt.date(2018, 1, 3) for d in pdh["date"].to_list())
