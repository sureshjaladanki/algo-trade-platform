import polars as pl


def add_trading_day(df: pl.DataFrame, datetime_col: str = "timestamp") -> pl.DataFrame:
    """
    Adds 'trading_day' (date portion of the datetime column), used as a
    grouping helper for intraday features (VWAP, ATR/gap, etc.).
    """
    df = df.with_columns(
        pl.col(datetime_col).dt.date().alias("trading_day")
    )
    return df
