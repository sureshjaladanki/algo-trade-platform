"""M4R candidate primary rules — Long + Short, reversion + continuation.

Extends the M5 Long event clock with the pre-registered reversion set from
``rule_registry``. Causality: ORB / prior-day / VWAP / gap levels use only
completed prior bars or prior sessions.
"""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.features.core import vwap as vwap_expr
from src.horizon.fresh.rule_registry import RULE_REGISTRY
from src.horizon.session import long_entry_ok_expr, short_entry_ok_expr
from src.utils.eval_common import BAR_MINUTES

_ORB_BAR_ENDS = (dt.time(9, 45), dt.time(10, 0))
_AFTER_ORB = dt.time(10, 0)


def _prepare(bars: pl.DataFrame) -> pl.DataFrame:
    df = bars.sort(["symbol", "date"]).with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
        _rng=(pl.col("high") - pl.col("low")) / pl.col("close"),
    )
    df = (
        df.with_columns(date_only=pl.col("date").dt.date())
        .with_columns(_vwap=vwap_expr().over(["symbol", "date_only"]))
    )
    orb = (
        df.filter(pl.col("time_only").is_in(list(_ORB_BAR_ENDS)))
        .group_by(["symbol", "date_only"])
        .agg(
            orb_high=pl.col("high").max(),
            orb_low=pl.col("low").min(),
            orb_vol=pl.col("volume").sum(),
        )
    )
    prior = (
        df.group_by(["symbol", "date_only"])
        .agg(
            day_high=pl.col("high").max(),
            day_low=pl.col("low").min(),
            day_close=pl.col("close").last(),
        )
        .sort(["symbol", "date_only"])
        .with_columns(
            prior_day_high=pl.col("day_high").shift(1).over("symbol"),
            prior_day_low=pl.col("day_low").shift(1).over("symbol"),
            prior_day_close=pl.col("day_close").shift(1).over("symbol"),
        )
        .drop(["day_high", "day_low", "day_close"])
    )
    open_px = (
        df.sort(["symbol", "date"])
        .group_by(["symbol", "date_only"])
        .agg(session_open=pl.col("open").first())
    )
    return (
        df.join(orb, on=["symbol", "date_only"], how="left")
        .join(prior, on=["symbol", "date_only"], how="left")
        .join(open_px, on=["symbol", "date_only"], how="left")
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
            above_vwap=(pl.col("close") > pl.col("_vwap")).cast(pl.Int8),
            long_ok=long_entry_ok_expr(),
            short_ok=short_entry_ok_expr(),
        )
        .with_columns(
            below_streak=pl.col("below_vwap")
            .shift(1)
            .rolling_sum(2, min_samples=2)
            .over(["symbol", "date_only"]),
            above_streak=pl.col("above_vwap")
            .shift(1)
            .rolling_sum(2, min_samples=2)
            .over(["symbol", "date_only"]),
            # Prior bar relative to ORB / PDH for reject / fade causality.
            prev_low=pl.col("low").shift(1).over(["symbol", "date_only"]),
            prev_high=pl.col("high").shift(1).over(["symbol", "date_only"]),
            prev_close=pl.col("close").shift(1).over(["symbol", "date_only"]),
        )
    )


def build_candidate_event_panel(bars: pl.DataFrame) -> pl.DataFrame:
    """Emit all registered-rule events (Long + Short). Idempotent pure transform."""
    df = _prepare(bars)
    chunks: list[pl.DataFrame] = []

    chunks.append(
        df.filter(
            pl.col("long_ok")
            & (pl.col("time_only") > _AFTER_ORB)
            & (pl.col("close") > pl.col("orb_high"))
            & (pl.col("volume") > pl.col("vol_med"))
            & pl.col("orb_high").is_not_null()
        ).with_columns(rule_id=pl.lit("orb_break_vol"), side=pl.lit("long"))
    )
    chunks.append(
        df.filter(
            pl.col("long_ok")
            & (pl.col("below_streak") >= 2)
            & (pl.col("close") >= pl.col("_vwap"))
        ).with_columns(rule_id=pl.lit("vwap_reclaim"), side=pl.lit("long"))
    )
    chunks.append(
        df.filter(
            pl.col("short_ok")
            & (pl.col("above_streak") >= 2)
            & (pl.col("close") <= pl.col("_vwap"))
        ).with_columns(rule_id=pl.lit("vwap_loss"), side=pl.lit("short"))
    )
    chunks.append(
        df.filter(
            pl.col("long_ok")
            & pl.col("prior_day_high").is_not_null()
            & (pl.col("close") > pl.col("prior_day_high"))
        ).with_columns(rule_id=pl.lit("prior_day_high"), side=pl.lit("long"))
    )
    chunks.append(
        df.filter(
            pl.col("long_ok")
            & pl.col("tod_med").is_not_null()
            & (pl.col("_rng") > 2.0 * pl.col("tod_med"))
        ).with_columns(rule_id=pl.lit("range_expand_2x"), side=pl.lit("long"))
    )
    # ORB fade: broke ORB extreme on prior bar, close back inside.
    chunks.append(
        df.filter(
            pl.col("long_ok")
            & (pl.col("time_only") > _AFTER_ORB)
            & pl.col("orb_low").is_not_null()
            & (pl.col("prev_low") < pl.col("orb_low"))
            & (pl.col("close") >= pl.col("orb_low"))
            & (pl.col("close") <= pl.col("orb_high"))
        ).with_columns(rule_id=pl.lit("orb_fade_long"), side=pl.lit("long"))
    )
    chunks.append(
        df.filter(
            pl.col("short_ok")
            & (pl.col("time_only") > _AFTER_ORB)
            & pl.col("orb_high").is_not_null()
            & (pl.col("prev_high") > pl.col("orb_high"))
            & (pl.col("close") <= pl.col("orb_high"))
            & (pl.col("close") >= pl.col("orb_low"))
        ).with_columns(rule_id=pl.lit("orb_fade_short"), side=pl.lit("short"))
    )
    # Prior-day reject: touched level prior bar, close back inside.
    chunks.append(
        df.filter(
            pl.col("short_ok")
            & pl.col("prior_day_high").is_not_null()
            & (pl.col("prev_high") >= pl.col("prior_day_high"))
            & (pl.col("close") < pl.col("prior_day_high"))
        ).with_columns(rule_id=pl.lit("prior_day_high_reject"), side=pl.lit("short"))
    )
    chunks.append(
        df.filter(
            pl.col("long_ok")
            & pl.col("prior_day_low").is_not_null()
            & (pl.col("prev_low") <= pl.col("prior_day_low"))
            & (pl.col("close") > pl.col("prior_day_low"))
        ).with_columns(rule_id=pl.lit("prior_day_low_reject"), side=pl.lit("long"))
    )
    # Gap fill: open gapped vs prior close; close fills back to prior close.
    chunks.append(
        df.filter(
            pl.col("long_ok")
            & pl.col("prior_day_close").is_not_null()
            & (pl.col("session_open") < pl.col("prior_day_close"))
            & (pl.col("prev_close") < pl.col("prior_day_close"))
            & (pl.col("close") >= pl.col("prior_day_close"))
        ).with_columns(rule_id=pl.lit("gap_fill_long"), side=pl.lit("long"))
    )
    chunks.append(
        df.filter(
            pl.col("short_ok")
            & pl.col("prior_day_close").is_not_null()
            & (pl.col("session_open") > pl.col("prior_day_close"))
            & (pl.col("prev_close") > pl.col("prior_day_close"))
            & (pl.col("close") <= pl.col("prior_day_close"))
        ).with_columns(rule_id=pl.lit("gap_fill_short"), side=pl.lit("short"))
    )

    out = pl.concat([c for c in chunks if c.height], how="diagonal_relaxed")
    if out.height == 0:
        return out
    known = {r.rule_id for r in RULE_REGISTRY}
    out = out.filter(pl.col("rule_id").is_in(list(known)))
    return (
        out.sort(["symbol", "date", "rule_id"])
        .with_columns(
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


def transition_candidate_events(
    events: pl.DataFrame, *, first_cross_only: bool = False
) -> pl.DataFrame:
    """Drop restatements (false→true only), same spirit as ``transition_events``."""
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
