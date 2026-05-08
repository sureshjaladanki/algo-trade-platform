import polars as pl

def add_roc(df: pl.DataFrame, period: int = 5) -> pl.DataFrame:
    """
    Calculates Rate of Change (ROC).
    ROC = (close - previous_close) / previous_close
    
    Pure indicator: operates on the input dataframe's 'close' column.
    """
    df = df.with_columns(
        ((pl.col("close") - pl.col("close").shift(period)) / pl.col("close").shift(period)).alias("roc")
    )
    return df
