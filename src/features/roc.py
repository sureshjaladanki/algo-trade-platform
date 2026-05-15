import polars as pl


def add_roc(df: pl.DataFrame, roc_col: str = "close", period: int = 3) -> pl.DataFrame:
    """
    Adds 'roc' — rate of change of close over `period` bars:
    close / close.shift(period) - 1.

    Timeperiod-agnostic: produces a generic column name regardless of bar
    interval. The caller may rename (e.g. 'roc_5m') when joining timeframes.

    Pure: operates only on the input dataframe's 'roc_col' column.
    """
    df = df.with_columns(
        (pl.col(roc_col) / pl.col(roc_col).shift(period) - 1.0).alias(f"{roc_col}_roc")
    )
    return df.with_columns(
        pl.when(pl.col(f"{roc_col}_roc").is_infinite()).then(None).otherwise(pl.col(f"{roc_col}_roc"))
    )
