import pandas as pd

def add_sma(df: pd.DataFrame, period: int = 200) -> pd.DataFrame:
    """Calculate Simple Moving Average (SMA) using pandas-ta."""
    df[f'sma_{period}'] = df.ta.sma(length=period)
    return df
