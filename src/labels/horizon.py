"""Tier 2 Horizon excess-return labels (primary rank target)."""

import datetime as dt

import polars as pl

from src.horizon.session import (
    LONG_LAST_ENTRY,
    MIS_EXIT_BAR_END,
    SHORT_LAST_ENTRY,
)


def calculate_horizon_labels(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    horizon_bars: int = 4,
    mis_exit_bar_end: dt.time = MIS_EXIT_BAR_END,
    long_last_entry: dt.time = LONG_LAST_ENTRY,
    short_last_entry: dt.time = SHORT_LAST_ENTRY,
) -> pl.DataFrame:
    """
    Forward excess return vs Nifty for Tier 2 Horizon models.

    Primary: H=4 (60m). Secondary robustness: call with horizon_bars=6 (90m).

    MIS rules (15m bar-end timestamps):
    - Exit bar must be same session and <= mis_exit_bar_end (~15:15 stamp).
    - Long entries only through long_last_entry (~14:15).
    - Short entries only through short_last_entry (~14:00).
    """
    stock_df = stock_df.sort(["symbol", "date"])
    nifty_df = nifty_df.sort("date")

    df = stock_df.join(
        nifty_df.select(["date", pl.col("close").alias("nifty_close")]),
        on="date",
        how="left",
    )

    df = df.with_columns(
        fwd_stock_ret=(
            pl.col("close").shift(-horizon_bars) / pl.col("close") - 1
        ).over("symbol"),
        fwd_nifty_ret=(
            pl.col("nifty_close").shift(-horizon_bars) / pl.col("nifty_close") - 1
        ).over("symbol"),
        exit_time=pl.col("date").shift(-horizon_bars).dt.time().over("symbol"),
        exit_date=pl.col("date").shift(-horizon_bars).dt.date().over("symbol"),
        entry_date=pl.col("date").dt.date(),
        entry_time=pl.col("date").dt.time(),
    ).with_columns(
        fwd_excess_ret=pl.col("fwd_stock_ret") - pl.col("fwd_nifty_ret"),
    )

    # is_finite rejects null, NaN, and Inf — Polars null ≠ NaN, so is_not_null
    # alone would let IEEE NaNs through to LightGBM (which then rejects y).
    same_session_exit = (
        (pl.col("exit_date") == pl.col("entry_date"))
        & (pl.col("exit_time") <= mis_exit_bar_end)
        & pl.col("fwd_excess_ret").is_finite()
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
            "date",
            "fwd_excess_ret",
            "valid_label",
            "valid_label_long",
            "valid_label_short",
        ]
    )
