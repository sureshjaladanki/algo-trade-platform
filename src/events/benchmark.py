"""After-tax passive buy-and-hold series (P0 comparator)."""

from __future__ import annotations

import polars as pl

from src.events.constants import LTCG_RATE


def build_after_tax_passive(nifty_daily: pl.DataFrame) -> pl.DataFrame:
    """Buy the Nifty close on the first session; apply LTCG only on exit.

    ``after_tax_wealth`` is the rupee value of ₹1 invested at the start if the
    position were sold that day. Losses are not assumed to be harvested.
    """
    start = nifty_daily.sort("date")["close"][0]
    return nifty_daily.sort("date").select(
        "date",
        pl.col("close").alias("nifty_close"),
        (pl.col("close") / start).alias("gross_wealth"),
        pl.when(pl.col("close") >= start)
        .then(1.0 + (1.0 - LTCG_RATE) * (pl.col("close") / start - 1.0))
        .otherwise(pl.col("close") / start)
        .alias("after_tax_wealth"),
    )
