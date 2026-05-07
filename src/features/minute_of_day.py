import polars as pl


def add_minute_of_day(df: pl.DataFrame, datetime_col: str = "timestamp") -> pl.DataFrame:
    """
    Adds 'minute_of_day' column derived from the datetime column.
    """
    df = df.with_columns(
        (pl.col(datetime_col).dt.hour() * 60 + pl.col(datetime_col).dt.minute()).alias("minute_of_day")
    )
    return df
