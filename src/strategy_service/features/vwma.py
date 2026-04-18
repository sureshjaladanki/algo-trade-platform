import pandas as pd
import pandas_ta  # noqa: F401


def add_vwma(df: pd.DataFrame, period: int = 21) -> pd.DataFrame:
    """Calculate Volume Weighted Moving Average (VWMA) using pandas-ta."""
    if "close" not in df.columns:
        raise KeyError("VWMA requires 'close' column.")
    if "volume" not in df.columns:
        raise KeyError("VWMA requires 'volume' column.")

    df[f"vwma_{period}"] = df.ta.vwma(length=period)
    return df
