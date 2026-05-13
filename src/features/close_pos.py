import polars as pl

def add_close_pos(df: pl.DataFrame) -> pl.DataFrame:
    """
    Adds 'close_pos' which measures where the close is relative to the high and low
    of the current bar. Results in a value between 0.0 and 1.0.
    """
    return df.with_columns(
        ((pl.col("close") - pl.col("low")) / (pl.col("high") - pl.col("low") + 1e-8)).alias("close_pos")
    )
