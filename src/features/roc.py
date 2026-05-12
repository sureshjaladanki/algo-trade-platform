import polars as pl


def add_roc(df: pl.DataFrame, period: int = 5) -> pl.DataFrame:
    """
    Smoothed ROC on `close`: `period`-bar SMA of lagged bar-to-bar returns.
    Uses ``pct_change().shift(1)`` so the rolling mean is over *previous*
    candles only (the current bar's pct change is excluded from the window).

    Pure indicator: operates on the input dataframe's 'close' column.
    Output column: `roc`.
    """
    return df.with_columns( 
        pl.col("close")
        .pct_change()
        .shift(1)
        .rolling_mean(window_size=period)
        .alias("roc")
    )
