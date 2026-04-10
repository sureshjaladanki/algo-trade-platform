import pandas as pd
from typing import Dict

def add_ad_ratio(df: pd.DataFrame, component_dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Calculate the industry-standard Advance/Decline (A/D) Ratio.
    
    Industry Standard Definition:
    - Advance: Current Close > Previous Close
    - Decline: Current Close < Previous Close
    - Unchanged: Current Close == Previous Close (ignored in ratio)
    - A/D Ratio: Number of Advancing Stocks / Number of Declining Stocks
    
    Args:
        main_df: The main DataFrame to add the A/D ratio to.
        component_dfs: Dictionary mapping stock symbols to their 1-minute DataFrames.
                
    Returns:
        DataFrame with ad_ratio.
    """
    if not component_dfs:
        return df

    # Extract close prices into a 2D matrix (columns = symbols, index = time)
    closes = pd.DataFrame({
        sym: df['close']
        for sym, df in component_dfs.items()
    }).reindex(df.index)
    
    # Industry standard: compare current close to previous close
    prev_closes = closes.shift(1)
    
    advances = (closes > prev_closes).sum(axis=1)
    declines = (closes < prev_closes).sum(axis=1)

    # Calculate A/D Ratio (Advances / Declines)
    # Replace 0 with NaN to avoid division by zero
    import numpy as np
    ad_ratio = np.where(declines == 0, advances, advances / declines)
    
    df['ad_ratio'] = ad_ratio
    return df
