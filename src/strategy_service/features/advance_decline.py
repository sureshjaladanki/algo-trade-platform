import pandas as pd
from typing import Dict
import pandas_ta as ta
import numpy as np

def add_ad_regime(df: pd.DataFrame, component_dfs: Dict[str, pd.DataFrame], period: int = 20) -> pd.DataFrame:
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

    # 1. Calculate the net breadth (Advances - Declines)
    df['ad_net_breadth'] = advances - declines

    # 2. Calculate the Cumulative A/D Line
    # This transforms 1-minute 'flicker' into a continuous trend
    df['ad_cumulative'] = df['ad_net_breadth'].cumsum()
    
    # 3. An EMA helps identify the 'Regime' direction
    df['ad_ema'] = ta.ema(df['ad_cumulative'], length=period)
    
    # 4. ROC helps identify if breadth is accelerating or decelerating
    roc_period = int(period / 4)
    df['ad_roc'] = ta.roc(df['ad_cumulative'], length=roc_period)

    # Calculate A/D Ratio (Advances / Declines)
    # Replace 0 with NaN to avoid division by zero
    ad_ratio = np.where(declines == 0, advances, advances / declines)
    df['ad_ratio'] = ad_ratio
    return df
