import pandas as pd

def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily Volume Weighted Average Price (VWAP) that resets each day."""
    # Assuming the index is a datetime object
    date_series = df.index.date
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    price_volume = typical_price * df['volume']

    # Group by the Date so VWAP resets at the start of each new day
    cumulative_pv = price_volume.groupby(date_series).cumsum()
    cumulative_vol = df['volume'].groupby(date_series).cumsum()
    
    # Assign only the final result to the dataframe
    df['vwap'] = cumulative_pv / cumulative_vol
    
    return df
