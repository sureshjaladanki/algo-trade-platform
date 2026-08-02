"""Triple-barrier path labels for Tier 2 meta-labeling / entry quality."""

import datetime as dt

import polars as pl

from src.horizon.session import (
    LONG_LAST_ENTRY,
    MIS_FLAT_BY,
    SHORT_LAST_ENTRY,
)

ROUND_TRIP_COST = 0.0030  # 30 bps
TP_FLOOR_LONG = 3 * ROUND_TRIP_COST  # 90 bps
SL_FLOOR = 1.5 * ROUND_TRIP_COST  # 45 bps
TP_FLOOR_SHORT = 2.5 * ROUND_TRIP_COST  # 75 bps
DEAD_ZONE = ROUND_TRIP_COST
# Barriers are not assumed to fill on an exact high/low touch: a take-profit must be
# penetrated by this much, while a stop triggers on touch (conservative both ways).
TP_PENETRATION = 0.0002  # 2 bps


def calculate_triple_barrier_labels(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    daily_stock_df: pl.DataFrame,
    horizon_bars: int = 4,
    cost: float = ROUND_TRIP_COST,
    tp_penetration: float = TP_PENETRATION,
    mis_flat_by: dt.time = MIS_FLAT_BY,
    long_last_entry: dt.time = LONG_LAST_ENTRY,
    short_last_entry: dt.time = SHORT_LAST_ENTRY,
) -> pl.DataFrame:
    """
    Hard vertical H=4, ATR-scaled TP/SL with cost floors, net-of-cost path labels.

    Long:  TP = max(2.5×ATR%, 90bps), SL = max(1.0×ATR%, 45bps)
    Short: TP = max(2.0×ATR%, 75bps), SL = max(0.9×ATR%, 45bps)

    Coding: +1 TP-first, -1 SL-first, 0 timeout. The ±cost dead zone applies to
    timeout resolutions only — a barrier hit keeps its sign.

    Barrier hits realize at the barrier price; timeouts realize at the bar `t+H`
    close. `tb_excess_ret_*` is net of `cost` and excess of Nifty over the same
    window (Nifty leg uses the exit bar close — finest resolution available at 15m).
    Entries whose vol-based TP cannot clear the cost floor are marked ineligible.
    """
    stock_df = stock_df.sort(["symbol", "datetime"])
    nifty_df = nifty_df.sort("datetime")
    daily_stock_df = daily_stock_df.sort(["symbol", "date"])

    daily = daily_stock_df.with_columns(
        tr=pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - pl.col("close").shift(1).over("symbol")).abs(),
            (pl.col("low") - pl.col("close").shift(1).over("symbol")).abs(),
        )
    ).with_columns(
        prev_atr14=(
            pl.col("tr")
            .rolling_mean(window_size=14)
            .over("symbol")
            .shift(1)
            .over("symbol")
        ),
    )

    df = (
        stock_df.with_columns(
            date_only=pl.col("datetime").dt.date(),
            entry_time=pl.col("datetime").dt.time(),
        )
        .join(
            daily.select(["symbol", "date", "prev_atr14"]),
            left_on=["symbol", "date_only"],
            right_on=["symbol", "date"],
            how="left",
        )
        .join(
            nifty_df.select(["datetime", pl.col("close").alias("nifty_close")]),
            on="datetime",
            how="left",
        )
    )

    df = df.with_columns(
        atr_pct=pl.col("prev_atr14") / pl.col("close"),
        entry_px=pl.col("close"),
        entry_nifty=pl.col("nifty_close"),
    ).with_columns(
        long_tp_vol=2.5 * pl.col("atr_pct"),
        short_tp_vol=2.0 * pl.col("atr_pct"),
        long_tp_w=pl.max_horizontal(2.5 * pl.col("atr_pct"), pl.lit(TP_FLOOR_LONG)),
        long_sl_w=pl.max_horizontal(1.0 * pl.col("atr_pct"), pl.lit(SL_FLOOR)),
        short_tp_w=pl.max_horizontal(2.0 * pl.col("atr_pct"), pl.lit(TP_FLOOR_SHORT)),
        short_sl_w=pl.max_horizontal(0.9 * pl.col("atr_pct"), pl.lit(SL_FLOOR)),
    ).with_columns(
        tb_eligible_long=pl.col("long_tp_vol") >= TP_FLOOR_LONG,
        tb_eligible_short=pl.col("short_tp_vol") >= TP_FLOOR_SHORT,
    )

    for h in range(1, horizon_bars + 1):
        df = df.with_columns(
            **{
                f"_hi_{h}": pl.col("high").shift(-h).over("symbol"),
                f"_lo_{h}": pl.col("low").shift(-h).over("symbol"),
                f"_c_{h}": pl.col("close").shift(-h).over("symbol"),
                f"_nc_{h}": pl.col("nifty_close").shift(-h).over("symbol"),
                f"_t_{h}": pl.col("datetime").shift(-h).dt.time().over("symbol"),
                f"_d_{h}": pl.col("datetime").shift(-h).dt.date().over("symbol"),
            }
        )

    df = df.with_columns(
        _long_exit_h=pl.lit(horizon_bars, dtype=pl.Int32),
        _short_exit_h=pl.lit(horizon_bars, dtype=pl.Int32),
        _long_event=pl.lit(0, dtype=pl.Int8),
        _short_event=pl.lit(0, dtype=pl.Int8),
    )

    for h in range(1, horizon_bars + 1):
        in_session = (
            (pl.col(f"_d_{h}") == pl.col("date_only"))
            & (pl.col(f"_t_{h}") <= mis_flat_by)
            & pl.col(f"_c_{h}").is_not_null()
        )
        long_tp = in_session & (
            pl.col(f"_hi_{h}")
            >= pl.col("entry_px") * (1.0 + pl.col("long_tp_w") + tp_penetration)
        )
        long_sl = in_session & (
            pl.col(f"_lo_{h}") <= pl.col("entry_px") * (1.0 - pl.col("long_sl_w"))
        )
        short_tp = in_session & (
            pl.col(f"_lo_{h}")
            <= pl.col("entry_px") * (1.0 - pl.col("short_tp_w") - tp_penetration)
        )
        short_sl = in_session & (
            pl.col(f"_hi_{h}") >= pl.col("entry_px") * (1.0 + pl.col("short_sl_w"))
        )

        still_long = pl.col("_long_event") == 0
        still_short = pl.col("_short_event") == 0
        # Same-bar TP+SL → SL first (conservative).
        df = df.with_columns(
            _long_event=pl.when(still_long & long_sl)
            .then(pl.lit(-1, dtype=pl.Int8))
            .when(still_long & long_tp)
            .then(pl.lit(1, dtype=pl.Int8))
            .otherwise(pl.col("_long_event")),
            _short_event=pl.when(still_short & short_sl)
            .then(pl.lit(-1, dtype=pl.Int8))
            .when(still_short & short_tp)
            .then(pl.lit(1, dtype=pl.Int8))
            .otherwise(pl.col("_short_event")),
            _long_exit_h=pl.when(still_long & (long_sl | long_tp))
            .then(pl.lit(h, dtype=pl.Int32))
            .otherwise(pl.col("_long_exit_h")),
            _short_exit_h=pl.when(still_short & (short_sl | short_tp))
            .then(pl.lit(h, dtype=pl.Int32))
            .otherwise(pl.col("_short_exit_h")),
        )

    def _exit_col(exit_h_col: str, value_prefix: str) -> pl.Expr:
        expr = pl.lit(None, dtype=pl.Float64)
        for h in range(1, horizon_bars + 1):
            in_session = (
                (pl.col(f"_d_{h}") == pl.col("date_only"))
                & (pl.col(f"_t_{h}") <= mis_flat_by)
                & pl.col(f"_c_{h}").is_not_null()
            )
            expr = (
                pl.when((pl.col(exit_h_col) == h) & in_session)
                .then(pl.col(f"{value_prefix}{h}"))
                .otherwise(expr)
            )
        return expr

    def _exit_ok(exit_h_col: str) -> pl.Expr:
        expr = pl.lit(False)
        for h in range(1, horizon_bars + 1):
            in_session = (
                (pl.col(f"_d_{h}") == pl.col("date_only"))
                & (pl.col(f"_t_{h}") <= mis_flat_by)
                & pl.col(f"_c_{h}").is_not_null()
            )
            expr = (
                pl.when((pl.col(exit_h_col) == h) & in_session)
                .then(True)
                .otherwise(expr)
            )
        return expr

    df = df.with_columns(
        _long_exit_close=_exit_col("_long_exit_h", "_c_"),
        _long_exit_nifty=_exit_col("_long_exit_h", "_nc_"),
        _short_exit_close=_exit_col("_short_exit_h", "_c_"),
        _short_exit_nifty=_exit_col("_short_exit_h", "_nc_"),
        _long_ok=_exit_ok("_long_exit_h"),
        _short_ok=_exit_ok("_short_exit_h"),
    ).with_columns(
        # Barrier hits realize at the barrier, not at the exit bar close.
        _long_path_ret=pl.when(pl.col("_long_event") == 1)
        .then(pl.col("long_tp_w"))
        .when(pl.col("_long_event") == -1)
        .then(-pl.col("long_sl_w"))
        .otherwise(pl.col("_long_exit_close") / pl.col("entry_px") - 1.0),
        # Stock-side move for the short sleeve: TP = price fell, SL = price rose.
        _short_path_ret=pl.when(pl.col("_short_event") == 1)
        .then(-pl.col("short_tp_w"))
        .when(pl.col("_short_event") == -1)
        .then(pl.col("short_sl_w"))
        .otherwise(pl.col("_short_exit_close") / pl.col("entry_px") - 1.0),
        _long_nifty_ret=pl.col("_long_exit_nifty") / pl.col("entry_nifty") - 1.0,
        _short_nifty_ret=pl.col("_short_exit_nifty") / pl.col("entry_nifty") - 1.0,
    )

    # Dead zone applies to timeouts only; a resolved barrier keeps its sign.
    long_label = (
        pl.when(~pl.col("_long_ok"))
        .then(None)
        .when(pl.col("_long_event") != 0)
        .then(pl.col("_long_event"))
        .when(pl.col("_long_path_ret").abs() <= DEAD_ZONE)
        .then(pl.lit(0, dtype=pl.Int8))
        .otherwise(pl.lit(0, dtype=pl.Int8))
    )
    short_label = (
        pl.when(~pl.col("_short_ok"))
        .then(None)
        .when(pl.col("_short_event") != 0)
        .then(pl.col("_short_event"))
        .when(pl.col("_short_path_ret").abs() <= DEAD_ZONE)
        .then(pl.lit(0, dtype=pl.Int8))
        .otherwise(pl.lit(0, dtype=pl.Int8))
    )

    df = df.with_columns(
        tb_label_long=pl.when(
            pl.col("tb_eligible_long")
            & (pl.col("entry_time") <= long_last_entry)
            & pl.col("_long_ok")
        )
        .then(long_label)
        .otherwise(None),
        tb_label_short=pl.when(
            pl.col("tb_eligible_short")
            & (pl.col("entry_time") <= short_last_entry)
            & pl.col("_short_ok")
        )
        .then(short_label)
        .otherwise(None),
        tb_excess_ret_long=pl.when(pl.col("_long_ok"))
        .then(pl.col("_long_path_ret") - pl.col("_long_nifty_ret") - cost)
        .otherwise(None),
        tb_excess_ret_short=pl.when(pl.col("_short_ok"))
        .then(
            # Short path PnL is -stock path; excess vs Nifty uses same-window nifty.
            (-pl.col("_short_path_ret")) - (-pl.col("_short_nifty_ret")) - cost
        )
        .otherwise(None),
    )

    return df.select(
        [
            "symbol",
            "datetime",
            "tb_label_long",
            "tb_label_short",
            "tb_excess_ret_long",
            "tb_excess_ret_short",
            "tb_eligible_long",
            "tb_eligible_short",
        ]
    )
