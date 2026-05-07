import polars as pl

def generate_target(df: pl.DataFrame, lookahead_minutes: int = 5, price_col: str = "close") -> pl.DataFrame:
    """
    Generates a binary classification target:
    1 if the price in `lookahead_minutes` is strictly greater than the current price.
    0 otherwise.
    
    Since the data is 1-minute frequency, shifting by -lookahead_minutes 
    gets the price `lookahead_minutes` into the future.
    """
    # Shift backwards (negative shift) to get future price
    df = df.with_columns(
        pl.col(price_col).shift(-lookahead_minutes).alias("future_price")
    )
    
    # Target = 1 if future_price > current_price else 0
    df = df.with_columns(
        pl.when(pl.col("future_price") > pl.col(price_col))
        .then(1)
        .otherwise(0)
        .alias("target")
    )
    
    # Drop rows where future_price is null (the very end of the dataset)
    df = df.filter(pl.col("future_price").is_not_null())
    df = df.drop("future_price")
    
    return df
