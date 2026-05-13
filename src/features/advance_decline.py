import polars as pl
from typing import Dict

def add_advance_decline(
    df: pl.DataFrame,
    symbol_dfs: Dict[str, pl.DataFrame],
    datetime_col: str = "timestamp"
) -> pl.DataFrame:
    """
    Calculates (Advances - Declines) / Total stocks in the sector.
    Advances: stocks where close > previous close.
    Declines: stocks where close < previous close.
    
    Inputs:
    - symbol_dfs: A dictionary of symbol dataframes (already resampled to target timeframe).
    
    Returns:
    - A dataframe with datetime_col and 'advance_decline' column.
    """
    if not symbol_dfs:
        return df
        
    dfs = []
    for sym, df in symbol_dfs.items():
        df_sub = df.select([pl.col(datetime_col), pl.col("close")])
        df_sub = df_sub.with_columns(pl.lit(sym).alias("symbol"))
        dfs.append(df_sub)
        
    all_symbols = pl.concat(dfs)
    
    # Calculate advance/decline
    all_symbols = all_symbols.with_columns(
        pl.col("close").shift(1).over("symbol").alias("prev_close")
    )
    
    all_symbols = all_symbols.with_columns(
        (pl.col("close") > pl.col("prev_close")).cast(pl.Int32).alias("is_advance"),
        (pl.col("close") < pl.col("prev_close")).cast(pl.Int32).alias("is_decline")
    )
    
    # Aggregate across symbols for each timestamp
    ad_agg = all_symbols.group_by(datetime_col).agg([
        pl.col("is_advance").sum().alias("advances"),
        pl.col("is_decline").sum().alias("declines"),
        pl.col("symbol").count().alias("total_stocks")
    ])
    
    ad_agg = ad_agg.with_columns(
        ((pl.col("advances") - pl.col("declines")) / pl.col("total_stocks")).alias("advance_decline")
    )
    ad_agg = ad_agg.with_columns(
        pl.when(pl.col("advance_decline").is_infinite()).then(None).otherwise(pl.col("advance_decline")).alias("advance_decline")
    )
    
    ad_agg = ad_agg.select([datetime_col, "advance_decline"]).sort(datetime_col)

    # Join A/D into the 5m sector features
    df = df.join(ad_agg, on=datetime_col, how="left")

    return df
