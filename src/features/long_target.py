import polars as pl
from typing import Dict
from ..constants import DEFAULT_TARGET_CLASSES

def add_long_target(
    df: pl.DataFrame,
    price_col: str = "close",
    *,
    lookahead_minutes: int = 15,
    natr_col: str = "natr_5m",
    take_profit_natr: float = 2.0,
    stop_loss_natr: float = 1.5,
    target_classes: Dict = DEFAULT_TARGET_CLASSES,
) -> pl.DataFrame:
    """
    Triple Barrier Method (long-only) label.

    Barriers use the entry bar's normalized ATR (`natr_col`, e.g. rolling mean TR / close):
    - upper barrier: +take_profit_natr * NATR
    - lower barrier: -stop_loss_natr * NATR

    Labeling (within the next `lookahead_minutes` bars) defaults to: DEFAULT_TARGET_CLASSES
    """
    if lookahead_minutes <= 0:
        raise ValueError("lookahead_minutes must be > 0")
    if natr_col not in df.columns:
        raise ValueError(f"natr column {natr_col!r} not in dataframe; required for NATR barriers")

    stop_loss = int(target_classes.get("stop_loss", {}).get("num", 0))
    hold = int(target_classes.get("hold", {}).get("num", 1))
    take_profit = int(target_classes.get("take_profit", {}).get("num", 2))

    price = pl.col(price_col)
    natr = pl.col(natr_col)
    tp_delta = natr * take_profit_natr
    sl_delta = natr * stop_loss_natr

    # 1. Generate lists of 'time-to-hit' expressions for each barrier
    tp_hits = []
    sl_hits = []

    for k in range(1, lookahead_minutes + 1):
        ret = price.shift(-k) / price - 1.0

        # If barrier hit at step k, record k, otherwise remain null
        tp_hits.append(pl.when(ret >= tp_delta).then(k))
        sl_hits.append(pl.when(ret <= -sl_delta).then(k))

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
            long_target=pl.when(pl.col("_tp_time") < pl.col("_sl_time")).then(take_profit)
            .when(pl.col("_sl_time") < pl.col("_tp_time")).then(stop_loss)
            .otherwise(hold)
            .cast(pl.Int8)
        )
        # Drop rows that don't have a full lookahead window available
        .filter(price.shift(-lookahead_minutes).is_not_null())
        .drop("_tp_time", "_sl_time")
    )
