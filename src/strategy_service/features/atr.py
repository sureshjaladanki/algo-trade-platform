import pandas as pd


def get_atr(df: pd.DataFrame, period: int = 14) -> dict:
    """
    Given a dataframe of multiday OHLCV data, calculates ATR and returns a dictionary
    containing the ATR value for the latest row.
    """
    if df.empty or not all(col in df.columns for col in ["high", "low", "close"]):
        return {}

    # Calculate ATR using pandas-ta
    atr_series = df.ta.atr(length=period)

    if (
        atr_series is not None
        and isinstance(atr_series, pd.Series)
        and not atr_series.empty
    ):
        # Get the latest non-NaN value
        latest_atr = (
            atr_series.dropna().iloc[-1] if not atr_series.dropna().empty else None
        )
        latest_close = df["close"].iloc[-1]

        if latest_atr is not None:
            return {"prev_atr": float(latest_atr), "prev_close": float(latest_close)}

    return {}
