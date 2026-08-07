from pathlib import Path

import polars as pl

# 15m OHLCV bars are stamped at *close* (bar-end), not group_by_dynamic's bar-start.
BAR_MINUTES_15M = 15


def load_csv_data(filepath: str | Path, datetime_col: str = "timestamp") -> pl.DataFrame:
    """
    Loads 1-minute candle data from a CSV file using Polars.
    Standardizes column names to lowercase.
    Ensures datetime column is properly parsed and sorted.
    """
    df = pl.read_csv(filepath)
    
    # Standardize column names to lowercase
    df = df.rename({col: col.lower() for col in df.columns})
    datetime_col_lower = datetime_col.lower()
    
    if datetime_col_lower not in df.columns:
        raise ValueError(f"Datetime column '{datetime_col_lower}' not found in the dataset.")
        
    # Check if we need to parse the datetime
    dtype = df[datetime_col_lower].dtype
    if dtype in [pl.Utf8, pl.String]:
        # Try a standard parsing format, fallback to strict=False (yields nulls for unparseable)
        df = df.with_columns(
            pl.col(datetime_col_lower).str.to_datetime(strict=False)
        )
    elif dtype in [pl.Int64, pl.Float64]:
        # Assuming epoch time
        # If max value is very large, it's likely milliseconds
        if df[datetime_col_lower].max() > 2e11:
            df = df.with_columns(pl.from_epoch(pl.col(datetime_col_lower), time_unit="ms"))
        else:
            df = df.with_columns(pl.from_epoch(pl.col(datetime_col_lower), time_unit="s"))
            
    # Remove null timestamps and sort
    df = df.filter(pl.col(datetime_col_lower).is_not_null())
    df = df.sort(datetime_col_lower)
    
    # Ensure required standard columns exist
    required_cols = {'open', 'high', 'low', 'close', 'volume'}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing required standard columns: {missing}")
        
    return df


def resample_daily(df: pl.DataFrame) -> pl.DataFrame:
    if df.is_empty():
        return df
    return df.group_by_dynamic("date", every="1d").agg([
        pl.col("open").first(),
        pl.col("high").max(),
        pl.col("low").min(),
        pl.col("close").last(),
        pl.col("volume").sum(),
    ])


def resample_15m(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate 1m OHLCV to 15m bars stamped at bar-end (close time).

    ``group_by_dynamic`` emits bar-start labels; we shift +15m so ``date`` is
    when the bar is closed and Tier 1 / Tier 2 features are actionable.
    """
    if df.is_empty():
        return df
    return (
        df.group_by_dynamic("date", every="15m")
        .agg(
            [
                pl.col("open").first(),
                pl.col("high").max(),
                pl.col("low").min(),
                pl.col("close").last(),
                pl.col("volume").sum(),
            ]
        )
        .with_columns(pl.col("date") + pl.duration(minutes=BAR_MINUTES_15M))
    )
