import math

import polars as pl


def add_chop(df: pl.DataFrame, period: int = 14) -> pl.DataFrame:
    """
    Adds ``chop`` (Choppiness Index) from high/low/close with ``period``-bar lookback.

    CHOP = 100 * log10( sum(TR, period) / (HHV(period) - LLV(period)) ) / log10(period)

    Timeperiod-agnostic: produces a generic column name regardless of bar
    interval. The caller may rename (e.g. ``chop_5m``) when joining timeframes.

    Pure: operates only on the input dataframe's ``high``, ``low``, ``close`` columns.
    """
    prev_close = pl.col("close").shift(1)
    tr = pl.max_horizontal(
        pl.col("high") - pl.col("low"),
        (pl.col("high") - prev_close).abs(),
        (pl.col("low") - prev_close).abs(),
    )
    range_n = (
        pl.col("high").rolling_max(window_size=period)
        - pl.col("low").rolling_min(window_size=period)
    )
    log_period = math.log10(period)
    return df.with_columns(
        (
            100.0
            * (tr.rolling_sum(window_size=period) / range_n).log10()
            / log_period
        ).alias("chop")
    )
