import pandas as pd
import pandas_ta as ta

def add_rsi(df: pd.DataFrame, rsi_period: int = 14) -> pd.DataFrame:
    """Calculate Relative Strength Index (RSI) using pandas-ta."""
    df[f'rsi_{rsi_period}'] = df.ta.rsi(length=rsi_period)
    return df
