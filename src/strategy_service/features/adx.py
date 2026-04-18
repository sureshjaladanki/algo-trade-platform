import pandas as pd

def add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate ADX to measure trend strength using pandas-ta."""
    adx_df = df.ta.adx(length=period)
    if adx_df is None or adx_df.empty:
        return df

    df[f"adx_{period}"] = adx_df[f"ADX_{period}"]
    return df
