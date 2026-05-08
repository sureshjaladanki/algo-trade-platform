import polars as pl


def generate_long_target(
    df: pl.DataFrame,
    price_col: str = "close",
    *,
    lookahead_minutes: int = 15,
    take_profit_pct: float = 0.5,
    stop_loss_pct: float = 0.25,
) -> pl.DataFrame:
    """
    Triple Barrier Method (long-only) label.

    Barriers are defined relative to the current price:
    - upper barrier: +take_profit_pct (percent units, e.g. 0.5 means +0.5%)
    - lower barrier: -stop_loss_pct  (percent units, e.g. 0.25 means -0.25%)

    Labeling (within the next `lookahead_minutes` bars):
      1  if the upper barrier is hit first
     -1  if the lower barrier is hit first
      0  if neither barrier is hit within the window
    """
    if lookahead_minutes <= 0:
        raise ValueError("lookahead_minutes must be > 0")

    price = pl.col(price_col)
    
    # 1. Generate lists of 'time-to-hit' expressions for each barrier
    tp_hits = []
    sl_hits = []

    for k in range(1, lookahead_minutes + 1):
        # Calculate pct change for this specific lookahead step
        ret_pct = (price.shift(-k) / price - 1.0) * 100.0
        
        # If barrier hit at step k, record k, otherwise remain null
        tp_hits.append(pl.when(ret_pct >= take_profit_pct).then(k))
        sl_hits.append(pl.when(ret_pct <= -stop_loss_pct).then(k))

    # 2. Determine the first time each barrier was triggered
    # We fill nulls with 'infinity' (lookahead + 1) to simplify the comparison logic
    inf = lookahead_minutes + 1
    first_tp = pl.min_horizontal(tp_hits).fill_null(inf)
    first_sl = pl.min_horizontal(sl_hits).fill_null(inf)

    return (
        df.with_columns(
            _tp_time=first_tp,
            _sl_time=first_sl
        )
        .with_columns(
            long_target=pl.when(pl.col("_tp_time") < pl.col("_sl_time")).then(2)
            .when(pl.col("_sl_time") < pl.col("_tp_time")).then(0)
            .otherwise(1)
            .cast(pl.Int8)
        )
        # Drop rows that don't have a full lookahead window available
        .filter(price.shift(-lookahead_minutes).is_not_null())
        .drop("_tp_time", "_sl_time")
    )
