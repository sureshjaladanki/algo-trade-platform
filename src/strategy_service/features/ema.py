import pandas as pd

def add_ema(df: pd.DataFrame, period: int = 200) -> pd.DataFrame:
    """Calculate Exponential Moving Average (EMA) using pandas-ta."""
    df[f'ema_{period}'] = df.ta.ema(length=period)
    return df
