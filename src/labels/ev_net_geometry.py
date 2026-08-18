"""Parameterized Long triple-barrier paths for Horizon EV-net Step 0 geometry probe."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import polars as pl

from src.horizon.session import MIS_EXIT_BAR_END, last_entry_for_horizon
from src.labels.triple_barrier import (
    BPS,
    ROUND_TRIP_COST,
    TOD_LOOKBACK_DAYS,
    TP_PENETRATION,
)
from src.regime.intraday import NSE_OPEN_BLEED_BAR

# Hard-stop cut (charter): dual-fold CI UB ≤ −10 bps → candidate infeasible.
HARD_STOP_EV_NET_UB_BPS = -10.0
HARD_STOP_EV_NET_UB = HARD_STOP_EV_NET_UB_BPS / BPS


@dataclass(frozen=True)
class LongGeometry:
    """One pre-registered Long barrier / vertical candidate (Step 0 ≤3)."""

    name: str
    horizon_bars: int
    tp_floor: float
    sl_floor: float
    tp_vol_mult: float
    sl_vol_mult: float


# Pre-registered Long candidates — free under EV-net rebuild; not production floors.
# Bias: reachable TP vs ~53–55 bps Top-K MFE cite; mild TP≥SL asymmetry; H near travel.
GEOMETRY_CANDIDATES: tuple[LongGeometry, ...] = (
    LongGeometry(
        name="G1_reach_h6",
        horizon_bars=6,
        tp_floor=2.0 * ROUND_TRIP_COST,  # 40 bps
        sl_floor=1.25 * ROUND_TRIP_COST,  # 25 bps
        tp_vol_mult=2.0,
        sl_vol_mult=1.0,
    ),
    LongGeometry(
        name="G2_early_h4",
        horizon_bars=4,
        tp_floor=1.75 * ROUND_TRIP_COST,  # 35 bps
        sl_floor=1.25 * ROUND_TRIP_COST,  # 25 bps
        tp_vol_mult=2.0,
        sl_vol_mult=1.0,
    ),
    LongGeometry(
        name="G3_mid_h5",
        horizon_bars=5,
        tp_floor=2.25 * ROUND_TRIP_COST,  # 45 bps
        sl_floor=1.25 * ROUND_TRIP_COST,  # 25 bps
        tp_vol_mult=2.25,
        sl_vol_mult=1.0,
    ),
)


def calculate_long_geometry_labels(
    stock_df: pl.DataFrame,
    geometry: LongGeometry,
    *,
    cost: float = ROUND_TRIP_COST,
    tp_penetration: float = TP_PENETRATION,
    mis_exit_bar_end: dt.time = MIS_EXIT_BAR_END,
    tod_lookback_days: int = TOD_LOOKBACK_DAYS,
) -> pl.DataFrame:
    """
    Long-only path labels under ``geometry``.

    Returns per-bar: event (+1 TP / −1 SL / 0 TO), path_ret, ev_net (= path_ret − cost),
    widths, MFE bps, eligibility, and MIS-safe entry ok for this H.
    Absolute path PnL (not Nifty-excess) — matches charter EV_net identity.
    """
    h_bars = geometry.horizon_bars
    long_last_entry = last_entry_for_horizon(h_bars, short=False)

    stock_df = stock_df.sort(["symbol", "date"])
    df = stock_df.with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
        entry_time=pl.col("date").dt.time(),
        range_pct=(
            (pl.col("high") - pl.col("low"))
            / pl.col("close").shift(1).over("symbol")
        ),
    )

    min_periods = max(10, tod_lookback_days // 4)
    df = (
        df.sort(["symbol", "time_only", "date_only"])
        .with_columns(
            rv_15_mean=pl.col("range_pct")
            .shift(1)
            .rolling_mean(window_size=tod_lookback_days, min_samples=min_periods)
            .over(["symbol", "time_only"]),
        )
        .sort(["symbol", "date"])
    )

    df = df.with_columns(
        atr_pct=pl.col("rv_15_mean"),
        entry_px=pl.col("close"),
    ).with_columns(
        tp_vol=geometry.tp_vol_mult * pl.col("atr_pct"),
        tp_w=pl.max_horizontal(
            geometry.tp_vol_mult * pl.col("atr_pct"),
            pl.lit(geometry.tp_floor),
        ),
        sl_w=pl.max_horizontal(
            geometry.sl_vol_mult * pl.col("atr_pct"),
            pl.lit(geometry.sl_floor),
        ),
    ).with_columns(
        tb_eligible=pl.col("tp_vol") >= geometry.tp_floor,
        entry_ok=(
            (pl.col("entry_time") > NSE_OPEN_BLEED_BAR)
            & (pl.col("entry_time") <= long_last_entry)
        ),
    )

    for h in range(1, h_bars + 1):
        df = df.with_columns(
            **{
                f"_hi_{h}": pl.col("high").shift(-h).over("symbol"),
                f"_lo_{h}": pl.col("low").shift(-h).over("symbol"),
                f"_c_{h}": pl.col("close").shift(-h).over("symbol"),
                f"_t_{h}": pl.col("date").shift(-h).dt.time().over("symbol"),
                f"_d_{h}": pl.col("date").shift(-h).dt.date().over("symbol"),
            }
        )

    df = df.with_columns(
        _exit_h=pl.lit(h_bars, dtype=pl.Int32),
        _event=pl.lit(0, dtype=pl.Int8),
    )

    for h in range(1, h_bars + 1):
        in_session = (
            (pl.col(f"_d_{h}") == pl.col("date_only"))
            & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
            & pl.col(f"_c_{h}").is_not_null()
        )
        long_tp = in_session & (
            pl.col(f"_hi_{h}")
            >= pl.col("entry_px") * (1.0 + pl.col("tp_w") + tp_penetration)
        )
        long_sl = in_session & (
            pl.col(f"_lo_{h}") <= pl.col("entry_px") * (1.0 - pl.col("sl_w"))
        )
        still = pl.col("_event") == 0
        # Same-bar TP+SL → SL first (conservative).
        df = df.with_columns(
            _event=pl.when(still & long_sl)
            .then(pl.lit(-1, dtype=pl.Int8))
            .when(still & long_tp)
            .then(pl.lit(1, dtype=pl.Int8))
            .otherwise(pl.col("_event")),
            _exit_h=pl.when(still & (long_sl | long_tp))
            .then(pl.lit(h, dtype=pl.Int32))
            .otherwise(pl.col("_exit_h")),
        )

    exit_close = pl.lit(None, dtype=pl.Float64)
    path_ok = pl.lit(False)
    mfe = pl.lit(None, dtype=pl.Float64)
    for h in range(1, h_bars + 1):
        in_session = (
            (pl.col(f"_d_{h}") == pl.col("date_only"))
            & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
            & pl.col(f"_c_{h}").is_not_null()
        )
        exit_close = (
            pl.when((pl.col("_exit_h") == h) & in_session)
            .then(pl.col(f"_c_{h}"))
            .otherwise(exit_close)
        )
        path_ok = pl.when((pl.col("_exit_h") == h) & in_session).then(True).otherwise(
            path_ok
        )
        fav = pl.col(f"_hi_{h}") / pl.col("entry_px") - 1.0
        new_peak = in_session & fav.is_not_null() & (mfe.is_null() | (fav > mfe))
        mfe = pl.when(new_peak).then(fav).otherwise(mfe)

    df = df.with_columns(
        _exit_close=exit_close,
        _ok=path_ok,
        _mfe=mfe,
    ).with_columns(
        path_ret=pl.when(pl.col("_event") == 1)
        .then(pl.col("tp_w"))
        .when(pl.col("_event") == -1)
        .then(-pl.col("sl_w"))
        .otherwise(pl.col("_exit_close") / pl.col("entry_px") - 1.0),
    ).with_columns(
        ev_net=pl.when(pl.col("_ok")).then(pl.col("path_ret") - cost).otherwise(None),
        tb_label=pl.when(pl.col("_ok")).then(pl.col("_event")).otherwise(None),
        mfe_bps=pl.when(pl.col("_ok")).then(pl.col("_mfe") * BPS).otherwise(None),
        tb_exit_h=pl.when(pl.col("_ok")).then(pl.col("_exit_h")).otherwise(None),
        geometry=pl.lit(geometry.name),
    )

    return df.select(
        [
            "symbol",
            "date",
            "date_only",
            "time_only",
            "geometry",
            "atr_pct",
            "tp_w",
            "sl_w",
            "tb_eligible",
            "entry_ok",
            "tb_label",
            "path_ret",
            "ev_net",
            "mfe_bps",
            "tb_exit_h",
        ]
    )
