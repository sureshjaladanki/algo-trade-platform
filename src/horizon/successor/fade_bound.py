"""P2 C0 helpers — vertical-only side-drift with disaster clip (not drop)."""

from __future__ import annotations

import polars as pl

from src.horizon.session import MIS_EXIT_BAR_END
from src.labels.fresh_barrier import MIS_VERTICAL_ONLY_SHORT_GEOMETRY

DISASTER_SL = MIS_VERTICAL_ONLY_SHORT_GEOMETRY.sl_floor
C0_HAIRCUTS_BPS: tuple[float, ...] = (3.0, 5.0, 8.0)
PRIMARY_RULE_ID = "prior_day_high_reject"
COMPANION_RULE_IDS: tuple[str, ...] = ("vwap_loss", "gap_fill_short")
S6_HORIZONS: tuple[int, ...] = (1, 2, 3, 5)
S6_AUTHORITY_HORIZON = 3
S6_HAIRCUTS_BPS: tuple[float, ...] = (6.0, 8.0, 12.0)
S6_HURDLE_BPS = 6.0


def attach_clipped_side_drift(
    events: pl.DataFrame,
    stock: pl.DataFrame,
    *,
    sl_floor: float = DISASTER_SL,
) -> pl.DataFrame:
    """
    Barrier-free return to MIS flatten, signed for the rule side.

    Paths worse than ``-sl_floor`` are **clipped**, not dropped (M4R-b review).
    """
    mis_close = (
        stock.with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
        )
        .filter(pl.col("time_only") <= MIS_EXIT_BAR_END)
        .sort(["symbol", "date"])
        .group_by(["symbol", "date_only"])
        .agg(mis_close=pl.col("close").last())
    )
    return (
        events.join(mis_close, on=["symbol", "date_only"], how="left")
        .with_columns(fwd_long=pl.col("mis_close") / pl.col("close") - 1.0)
        .with_columns(
            side_drift=pl.when(pl.col("side") == "long")
            .then(pl.col("fwd_long"))
            .otherwise(-pl.col("fwd_long"))
        )
        .with_columns(
            side_drift=pl.max_horizontal(pl.col("side_drift"), pl.lit(-sl_floor))
        )
    )


def attach_multiday_close_drift(
    events: pl.DataFrame,
    daily: pl.DataFrame,
    *,
    horizon_sessions: int,
    sl_floor: float = DISASTER_SL,
) -> pl.DataFrame:
    """
    Close-to-close Short drift from event-date close to T+h close.

    One row per ``(symbol, date_only, rule_id)``. Paths worse than
    ``-sl_floor`` are **clipped**, not dropped. Entry is the daily close,
    not the intraday event bar.
    """
    keyed = (
        events.sort(["symbol", "date"])
        .unique(subset=["symbol", "date_only", "rule_id"], keep="first")
    )
    fwd = (
        daily.sort(["symbol", "date"])
        .with_columns(
            entry_close=pl.col("close"),
            exit_close=pl.col("close").shift(-horizon_sessions).over("symbol"),
        )
        .select(["symbol", "date", "entry_close", "exit_close"])
    )
    return (
        keyed.join(
            fwd,
            left_on=["symbol", "date_only"],
            right_on=["symbol", "date"],
            how="left",
        )
        .filter(pl.col("entry_close").is_finite() & pl.col("exit_close").is_finite())
        .with_columns(fwd_long=pl.col("exit_close") / pl.col("entry_close") - 1.0)
        .with_columns(
            side_drift_raw=pl.when(pl.col("side") == "long")
            .then(pl.col("fwd_long"))
            .otherwise(-pl.col("fwd_long"))
        )
        .with_columns(
            side_drift=pl.max_horizontal(pl.col("side_drift_raw"), pl.lit(-sl_floor))
        )
    )
