import polars as pl


def add_relative_strength(
    df: pl.DataFrame,
    close_col: str = "close",
    sector_close_col: str = "sector_close",
) -> pl.DataFrame:
    """
    Ratio of symbol close to sector close (relative strength).
    Apply ``add_roc`` on ``rs_ratio`` for rate-of-change features.
    """
    df = df.with_columns(
        (pl.col(close_col) / pl.col(sector_close_col)).alias("rs_ratio")
    )

    return df.with_columns(
        pl.when(pl.col("rs_ratio").is_infinite()).then(None).otherwise(pl.col("rs_ratio"))
    )