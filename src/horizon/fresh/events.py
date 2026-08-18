"""Stage C event clock — Long primary rules (sparse decision set).

Fresh path must not call production ``predict_horizon_gbm`` for its decision set.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import polars as pl

from src.features.core import vwap as vwap_expr
from src.horizon.session import long_entry_ok_expr
from src.utils.eval_common import BAR_MINUTES

_ORB_BAR_ENDS = (dt.time(9, 45), dt.time(10, 0))
_AFTER_ORB = dt.time(10, 0)


@dataclass(frozen=True)
class EventRule:
    rule_id: str
    description: str
    causality: str


LONG_EVENT_RULES: tuple[EventRule, ...] = (
    EventRule(
        "orb_break_vol",
        "ORB high break with volume > 20-bar median",
        "ORB high/volume from prior bars only; signal on close of break bar",
    ),
    EventRule(
        "vwap_reclaim",
        "Close reclaims VWAP after ≥2 bars below",
        "VWAP cumulates within session; prior bars below counted causally",
    ),
    EventRule(
        "prior_day_high",
        "Close breaks prior session high",
        "Prior-day high from completed prior session only",
    ),
    EventRule(
        "range_expand_2x",
        "Bar range > 2× TOD median range",
        "TOD median uses shift(1) history only",
    ),
)


def _session_vwap(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.sort(["symbol", "date"])
        .with_columns(date_only=pl.col("date").dt.date())
        .with_columns(
            _vwap=vwap_expr().over(["symbol", "date_only"]),
        )
    )


def build_long_event_panel(bars: pl.DataFrame) -> pl.DataFrame:
    """
    Emit Long event rows only (not every bar).

    Columns: event_id, symbol, date, clock, side, rule_id (+ OHLCV passthrough).
    Idempotent pure transform.
    """
    df = bars.sort(["symbol", "date"]).with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
        _rng=(pl.col("high") - pl.col("low")) / pl.col("close"),
    )
    df = _session_vwap(df)

    # ORB: first two 15m bars after bleed (09:45, 10:00 bar-ends) define ORB high.
    orb = (
        df.filter(pl.col("time_only").is_in(list(_ORB_BAR_ENDS)))
        .group_by(["symbol", "date_only"])
        .agg(orb_high=pl.col("high").max(), orb_vol=pl.col("volume").sum())
    )
    prior_high = (
        df.group_by(["symbol", "date_only"])
        .agg(day_high=pl.col("high").max())
        .sort(["symbol", "date_only"])
        .with_columns(prior_day_high=pl.col("day_high").shift(1).over("symbol"))
        .drop("day_high")
    )
    df = (
        df.join(orb, on=["symbol", "date_only"], how="left")
        .join(prior_high, on=["symbol", "date_only"], how="left")
        .with_columns(
            vol_med=pl.col("volume")
            .shift(1)
            .rolling_median(20, min_samples=5)
            .over("symbol"),
            tod_med=pl.col("_rng")
            .shift(1)
            .rolling_median(60, min_samples=10)
            .over(["symbol", "time_only"]),
            below_vwap=(pl.col("close") < pl.col("_vwap")).cast(pl.Int8),
        )
        .with_columns(
            below_streak=pl.col("below_vwap")
            .shift(1)
            .rolling_sum(2, min_samples=2)
            .over(["symbol", "date_only"]),
        )
    )

    # Entry window: MIS-safe Long entries only.
    df = df.with_columns(entry_ok=long_entry_ok_expr())

    events: list[pl.DataFrame] = []

    orb_break = df.filter(
        pl.col("entry_ok")
        & (pl.col("time_only") > _AFTER_ORB)
        & (pl.col("close") > pl.col("orb_high"))
        & (pl.col("volume") > pl.col("vol_med"))
        & pl.col("orb_high").is_not_null()
    ).with_columns(rule_id=pl.lit("orb_break_vol"))
    events.append(orb_break)

    vwap_reclaim = df.filter(
        pl.col("entry_ok")
        & (pl.col("below_streak") >= 2)
        & (pl.col("close") >= pl.col("_vwap"))
    ).with_columns(rule_id=pl.lit("vwap_reclaim"))
    events.append(vwap_reclaim)

    pdh = df.filter(
        pl.col("entry_ok")
        & pl.col("prior_day_high").is_not_null()
        & (pl.col("close") > pl.col("prior_day_high"))
    ).with_columns(rule_id=pl.lit("prior_day_high"))
    events.append(pdh)

    expand = df.filter(
        pl.col("entry_ok")
        & pl.col("tod_med").is_not_null()
        & (pl.col("_rng") > 2.0 * pl.col("tod_med"))
    ).with_columns(rule_id=pl.lit("range_expand_2x"))
    events.append(expand)

    out = pl.concat(events, how="diagonal_relaxed")
    if out.height == 0:
        return out
    return (
        out.sort(["symbol", "date", "rule_id"])
        .with_columns(
            side=pl.lit("long"),
            clock=pl.col("date"),
            event_id=pl.concat_str(
                [
                    pl.col("symbol"),
                    pl.col("date").dt.strftime("%Y%m%d%H%M"),
                    pl.col("rule_id"),
                ],
                separator="|",
            ),
        )
        .unique(subset=["event_id"], keep="first")
    )


def transition_events(events: pl.DataFrame, *, first_cross_only: bool = False) -> pl.DataFrame:
    """
    Keep bars where a rule *turns on*, dropping restatements of a live condition.

    ``build_long_event_panel`` re-emits a persisting condition on every later bar
    (a name that broke its prior-day high at 10:15 is still above it at 14:30).
    Those restatements are session state, not decisions: they dilute the pool,
    duplicate near-identical feature rows, and reintroduce the bar clock.

    Default keeps every false→true transition, so a genuine break / fade /
    re-break sequence still contributes three decisions. ``first_cross_only``
    keeps just the session's first firing per rule.
    """
    if events.height == 0:
        return events
    keys = ["symbol", "date_only", "rule_id"]
    df = events.sort(["symbol", "rule_id", "date"]).with_columns(
        date_only=pl.col("date").dt.date()
    )
    if first_cross_only:
        return df.filter(pl.int_range(pl.len()).over(keys) == 0)
    gap_bars = (
        pl.col("date") - pl.col("date").shift(1).over(keys)
    ).dt.total_minutes() > BAR_MINUTES
    return df.filter(gap_bars.fill_null(True))


def collapse_to_bar(events: pl.DataFrame) -> pl.DataFrame:
    """
    One row per ``(symbol, bar)`` with multi-hot rule flags.

    Four separate rows per bar (one per rule) that differ only in a one-hot are
    near-duplicates to a GBDT: it can only learn per-rule base rates, and the
    duplicated labels inflate N without adding information.
    """
    if events.height == 0:
        return events
    flags = [
        (pl.col("rule_id") == r.rule_id).any().cast(pl.Float64).alias(f"rule_{r.rule_id}")
        for r in LONG_EVENT_RULES
    ]
    keys = ["symbol", "date"]
    agg = (
        events.group_by(keys)
        .agg(*flags, n_rules=pl.len(), rule_id=pl.col("rule_id").sort().str.join("+"))
        .sort(keys)
    )
    passthrough = events.unique(subset=keys, keep="first").drop(["rule_id", "event_id"])
    return agg.join(passthrough, on=keys, how="inner").with_columns(
        event_id=pl.concat_str(
            [pl.col("symbol"), pl.col("date").dt.strftime("%Y%m%d%H%M")], separator="|"
        ),
    )


def rule_dictionary() -> str:
    lines = ["Long event rule dictionary (M4)", "=" * 36]
    for r in LONG_EVENT_RULES:
        lines.append(f"- {r.rule_id}: {r.description}")
        lines.append(f"  causality: {r.causality}")
    return "\n".join(lines)
