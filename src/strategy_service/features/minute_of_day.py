import pandas as pd


def add_minute_of_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'minute_of_day' column to the DataFrame based on the datetime index or column.
    """
    if "datetime" in df.columns:
        df["minute_of_day"] = pd.to_datetime(df["datetime"]).dt.time
    elif isinstance(df.index, pd.DatetimeIndex):
        df["minute_of_day"] = df.index.time

    return df
