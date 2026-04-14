import pandas as pd

def add_adx(df: pd.DataFrame, period: int = 70, resample_period: int = 5) -> pd.DataFrame:
    """Calculate ADX on resampled data to measure trend strength."""
    if df.empty or not all(col in df.columns for col in ['high', 'low', 'close']):
        return df

    df_idx = df.set_index('datetime') if 'datetime' in df.columns else df
    resampled = df_idx.resample(f'{resample_period}min').agg({'high': 'max', 'low': 'min', 'close': 'last'})
    resample_adx_period = int(period / resample_period)
    
    adx_df = resampled.ta.adx(length=resample_adx_period)
    if adx_df is not None and f'ADX_{resample_adx_period}' in adx_df.columns:
        df[f'adx_{period}'] = adx_df[f'ADX_{resample_adx_period}'].reindex(df_idx.index, method='ffill').values
        
    return df
