import pandas as pd


def isna_safe(value):
    if isinstance(value, pd.Series):
        return value.fillna(0.0)

    return 0.0 if pd.isna(value) else value
