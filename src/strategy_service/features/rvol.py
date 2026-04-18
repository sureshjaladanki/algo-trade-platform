import pandas as pd
from src.strategy_service.features.minute_of_day import add_minute_of_day


def get_volume_profile(df: pd.DataFrame) -> dict:
    """
    Given a dataframe of multiday OHLCV data, returns a dictionary mapping
    minute_of_day to avg_volume_for_time.
    """
    if df.empty or "volume" not in df.columns:
        return {}

    df = add_minute_of_day(df.copy())

    # Calculate the average volume for each minute and convert to dictionary
    volume_profile_dict = df.groupby("minute_of_day")["volume"].mean().to_dict()

    return volume_profile_dict
