import pandas as pd

def add_bb(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """Calculate Bollinger Bands using pandas-ta."""
    bb = df.ta.bbands(length=period, std=std_dev)
    
    if bb is not None:
        # pandas-ta returns columns like BBL_20_2.0_2.0, BBM_20_2.0_2.0, BBU_20_2.0_2.0
        # The formatting of std_dev might drop the decimal if it's a whole number, so we find it dynamically
        bbl_col = [c for c in bb.columns if c.startswith(f'BBL_{period}_')][0]
        bbu_col = [c for c in bb.columns if c.startswith(f'BBU_{period}_')][0]
        
        df['bb_lower'] = bb[bbl_col]
        df['bb_upper'] = bb[bbu_col]
        df['bb_width_pct'] = ((df['bb_upper'] - df['bb_lower']) / df['close']) * 100
        df['expected_profit_pct_long'] = ((df['bb_upper'] - df['close']) / df['close']) * 100
        df['expected_profit_pct_short'] = ((df['close'] - df['bb_lower']) / df['close']) * 100
        
    return df
