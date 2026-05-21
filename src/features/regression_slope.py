import polars as pl


def add_regression_slope(
    df: pl.DataFrame,
    reg_slope_col: str = "close",
    period: int = 5,
) -> pl.DataFrame:
    """
    Adds Volatility-Normalized Linear Regression Slope:
    Runs an OLS line over `period` bars and divides the slope by the rolling standard deviation.
    """
    slope_col = f"{reg_slope_col}_reg_slope_{period}"
    
    # Vectorized OLS slope over rolling window using Polars
    # slope = cov(x, y) / var(x) where x is the sequence 0, 1, ..., period-1
    x = pl.int_range(0, pl.len())
    
    sum_y = pl.col(reg_slope_col).rolling_sum(window_size=period)
    sum_xy = (pl.col(reg_slope_col) * x).rolling_sum(window_size=period)
    
    # Translate global x to local x within the window
    local_sum_xy = sum_xy - (x - period + 1) * sum_y
    
    cov_num = local_sum_xy - ((period - 1) / 2.0) * sum_y
    var_x_sum = period * (period**2 - 1) / 12.0
    
    raw_slope = cov_num / var_x_sum
    
    rolling_std = pl.col(reg_slope_col).rolling_std(window_size=period)
    
    # Normalize by standard deviation
    df = df.with_columns(
        (raw_slope / rolling_std).alias(slope_col)
    )
    
    df = df.with_columns(
        pl.when(pl.col(slope_col).is_infinite()).then(None).otherwise(pl.col(slope_col)).alias(slope_col)
    )
    
    return df
