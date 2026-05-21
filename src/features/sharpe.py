import polars as pl


def add_sharpe(
    df: pl.DataFrame,
    close_col: str = "close",
    period: int = 5,
) -> pl.DataFrame:
    """
    Adds Vol-Normalized Returns (Sharpe-Over-Window):
    Cumulative return over `period` bars divided by the rolling standard deviation
    of returns over that same window. Acts as a rolling information ratio.
    """
    sharpe_col = f"sharpe_{period}"
    
    pct_change_col = f"{close_col}_pct"
    
    df = df.with_columns(
        ((pl.col(close_col) / pl.col(close_col).shift(1)) - 1.0).alias(pct_change_col)
    )
    
    cum_return = (pl.col(close_col) / pl.col(close_col).shift(period)) - 1.0
    rolling_std = pl.col(pct_change_col).rolling_std(window_size=period)
    
    df = df.with_columns(
        (cum_return / rolling_std).alias(sharpe_col)
    )
    
    df = df.with_columns(
        pl.when(pl.col(sharpe_col).is_infinite()).then(None).otherwise(pl.col(sharpe_col)).alias(sharpe_col)
    )
    
    df = df.drop(pct_change_col)

    return df
