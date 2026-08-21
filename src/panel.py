"""Polars daily/event panels, aligned on knowledge date. df in → df out."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import polars as pl

from src.universe import (
    ADV_LARGE_USD,
    ADV_MID_USD,
    ADV_SMALL_USD,
    LIQUID_ETF_SYMBOLS,
    LiquidityBucket,
)

KNOWLEDGE_DATE = "knowledge_date"
LABEL_PREFIX = "label_"


class LeakageError(Exception):
    """A row's knowledge date can see a timestamp in its future."""


def with_liquidity_bucket(df: pl.DataFrame) -> pl.DataFrame:
    etf = pl.col("symbol").is_in(list(LIQUID_ETF_SYMBOLS))
    return df.with_columns(
        pl.when(etf)
        .then(pl.lit(LiquidityBucket.LIQUID_ETF.value))
        .when(pl.col("adv_usd") >= ADV_LARGE_USD)
        .then(pl.lit(LiquidityBucket.LARGE_CAP.value))
        .when(pl.col("adv_usd") >= ADV_MID_USD)
        .then(pl.lit(LiquidityBucket.MID_CAP.value))
        .when(pl.col("adv_usd") >= ADV_SMALL_USD)
        .then(pl.lit(LiquidityBucket.SMALL_CAP.value))
        .otherwise(pl.lit(LiquidityBucket.MICRO_CLOSED.value))
        .alias("liquidity_bucket")
    )


def split_price_factor(ratio: float) -> float:
    if ratio <= 0:
        raise ValueError("split ratio must be > 0")
    return 1.0 / ratio


def special_dividend_price_factor(*, close_cum_div: float, amount: float) -> float:
    """Factor applied to pre-ex prices so the series is continuous through the special."""
    if close_cum_div <= 0:
        raise ValueError("close must be > 0")
    return (close_cum_div - amount) / close_cum_div


def apply_split(df: pl.DataFrame, *, ratio: float) -> pl.DataFrame:
    factor = split_price_factor(ratio)
    return df.with_columns(
        (pl.col("close") * factor).alias("close"),
        (pl.col("volume") / factor).alias("volume"),
    )


def membership_asof(df: pl.DataFrame, asof: date) -> pl.DataFrame:
    """Names effective on `asof`, including those that later delist."""
    return df.filter(
        (pl.col("start_date") <= asof)
        & (pl.col("end_date").is_null() | (pl.col("end_date") >= asof))
    )


def leakage_rows(df: pl.DataFrame) -> pl.DataFrame:
    if KNOWLEDGE_DATE not in df.columns:
        raise ValueError("panel must carry knowledge_date")
    date_cols = [
        name
        for name, dtype in df.schema.items()
        if name != KNOWLEDGE_DATE
        and not name.startswith(LABEL_PREFIX)
        and dtype in (pl.Date, pl.Datetime)
    ]
    if not date_cols:
        return df.head(0)
    late = pl.any_horizontal([pl.col(name) > pl.col(KNOWLEDGE_DATE) for name in date_cols])
    return df.filter(late)


def assert_no_leakage(df: pl.DataFrame) -> None:
    bad = leakage_rows(df)
    if bad.height:
        raise LeakageError(f"{bad.height} rows have timestamps after knowledge_date")


def require_sane_final_prices(df: pl.DataFrame) -> None:
    last = (
        df.sort("date")
        .group_by("symbol")
        .agg(pl.col("close").last().alias("final_close"), pl.col("date").last().alias("final_date"))
    )
    bad = last.filter((pl.col("final_close") <= 0) | pl.col("final_close").is_null())
    if bad.height:
        raise ValueError(f"insane final prices: {bad.to_dicts()}")


def load_csv(path: Path) -> pl.DataFrame:
    return pl.read_csv(path, try_parse_dates=True)
