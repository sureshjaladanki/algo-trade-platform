"""Tier 2 Horizon excess-return labels (primary rank target)."""

import datetime as dt

import polars as pl

from src.horizon.session import (
    LONG_LAST_ENTRY,
    MIS_FLAT_BY,
    SHORT_LAST_ENTRY,
)


def calculate_horizon_labels(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    horizon_bars: int = 4,
    mis_flat_by: dt.time = MIS_FLAT_BY,
    long_last_entry: dt.time = LONG_LAST_ENTRY,
    short_last_entry: dt.time = SHORT_LAST_ENTRY,
) -> pl.DataFrame:
    """
    Forward excess return vs Nifty for Tier 2 Horizon models.

    Primary: H=4 (60m). Secondary robustness: call with horizon_bars=6 (90m).

    MIS rules (bar-start timestamps):
    - Exit bar must be same session and <= mis_flat_by (~15:00).
    - Long entries only through long_last_entry (~14:00).
    - Short entries only through short_last_entry (~13:45).
    """
    stock_df = stock_df.sort(["symbol", "datetime"])
    nifty_df = nifty_df.sort("datetime")

    df = stock_df.join(
        nifty_df.select(["datetime", pl.col("close").alias("nifty_close")]),
        on="datetime",
        how="left",
    )

    df = df.with_columns(
        fwd_stock_ret=(
            pl.col("close").shift(-horizon_bars) / pl.col("close") - 1
        ).over("symbol"),
        fwd_nifty_ret=(
            pl.col("nifty_close").shift(-horizon_bars) / pl.col("nifty_close") - 1
        ).over("symbol"),
        exit_time=pl.col("datetime").shift(-horizon_bars).dt.time().over("symbol"),
        exit_date=pl.col("datetime").shift(-horizon_bars).dt.date().over("symbol"),
        entry_date=pl.col("datetime").dt.date(),
        entry_time=pl.col("datetime").dt.time(),
    ).with_columns(
        fwd_excess_ret=pl.col("fwd_stock_ret") - pl.col("fwd_nifty_ret"),
    )

    same_session_exit = (
        (pl.col("exit_date") == pl.col("entry_date"))
        & (pl.col("exit_time") <= mis_flat_by)
        & pl.col("fwd_excess_ret").is_not_null()
    )

    df = df.with_columns(
        valid_label=same_session_exit,
        valid_label_long=same_session_exit & (pl.col("entry_time") <= long_last_entry),
        valid_label_short=same_session_exit & (pl.col("entry_time") <= short_last_entry),
    ).with_columns(
        fwd_excess_ret=pl.when(pl.col("valid_label"))
        .then(pl.col("fwd_excess_ret"))
        .otherwise(None),
    )

    return df.select(
        [
            "symbol",
            "datetime",
            "fwd_excess_ret",
            "valid_label",
            "valid_label_long",
            "valid_label_short",
        ]
    )
