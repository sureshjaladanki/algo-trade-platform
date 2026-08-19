"""Replicate NSE Nifty-50 free-float rank at Jan/Jul cut-offs."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.events.constants import (
    IMPACT_COST_MAX_PCT,
    INCLUSION_FF_BUFFER,
    MCWB_MIN_MONTHS,
)


def cutoff_for_announcement(announcement_date: dt.date) -> dt.date:
    """Semi-annual reviews use 31 Jan or 31 Jul data ending before the PR."""
    if announcement_date.month <= 4:
        return dt.date(announcement_date.year, 1, 31)
    if announcement_date.month >= 7:
        return dt.date(announcement_date.year, 7, 31)
    raise ValueError(f"no Jan/Jul cut-off for {announcement_date}")


def window_months(cutoff: dt.date) -> list[tuple[int, int]]:
    """Six calendar months ending on the cut-off month."""
    if cutoff.month == 1 and cutoff.day == 31:
        return [(cutoff.year - 1, m) for m in range(8, 13)] + [(cutoff.year, 1)]
    if cutoff.month == 7 and cutoff.day == 31:
        return [(cutoff.year, m) for m in range(2, 8)]
    raise ValueError(f"cut-off must be 31 Jan or 31 Jul, got {cutoff}")


def _window_frame(panel: pl.DataFrame, cutoff: dt.date) -> pl.DataFrame:
    months = window_months(cutoff)
    keys = pl.DataFrame(
        {"year": [y for y, _ in months], "month": [m for _, m in months]}
    ).with_columns(pl.col("year").cast(pl.Int32), pl.col("month").cast(pl.Int32))
    return panel.join(keys, on=["year", "month"], how="inner")


def average_free_float(panel: pl.DataFrame, cutoff: dt.date) -> pl.DataFrame:
    """6-month mean FF mcap and impact cost; family is the cut-off month's index."""
    window = _window_frame(panel, cutoff)
    cutoff_month = cutoff.month
    cutoff_year = cutoff.year
    at_cutoff = window.filter(
        (pl.col("year") == cutoff_year) & (pl.col("month") == cutoff_month)
    ).select("symbol", "family")
    averaged = window.group_by("symbol").agg(
        avg_ff_mcap_cr=pl.col("ff_mcap_cr").mean(),
        avg_impact_cost_pct=pl.col("impact_cost_pct").mean(),
        n_months=pl.len(),
    )
    return at_cutoff.join(averaged, on="symbol", how="inner").with_columns(
        cutoff=pl.lit(cutoff)
    )


def rank_next50(averaged: pl.DataFrame, *, min_months: int = MCWB_MIN_MONTHS) -> pl.DataFrame:
    """Rank Next 50 names at the cut-off by 6-month average free-float mcap."""
    candidates = averaged.filter(
        (pl.col("family") == "next_50") & (pl.col("n_months") >= min_months)
    )
    return candidates.sort("avg_ff_mcap_cr", descending=True).with_columns(
        rank=pl.int_range(1, pl.len() + 1, dtype=pl.Int32)
    )


def predict_additions(
    averaged: pl.DataFrame,
    *,
    min_months: int = MCWB_MIN_MONTHS,
    buffer: float = INCLUSION_FF_BUFFER,
    max_impact_cost: float = IMPACT_COST_MAX_PCT,
) -> pl.DataFrame:
    """Compulsory-inclusion set: Next 50 names ≥ 1.5× smallest Nifty 50 FF mcap."""
    incumbents = averaged.filter(pl.col("family") == "nifty_50")
    if incumbents.height == 0:
        raise ValueError("no Nifty 50 incumbents at cut-off")
    floor = float(incumbents["avg_ff_mcap_cr"].min()) * buffer
    ranked = rank_next50(averaged, min_months=min_months)
    return ranked.filter(
        (pl.col("avg_ff_mcap_cr") >= floor)
        & (pl.col("avg_impact_cost_pct") <= max_impact_cost)
    ).with_columns(inclusion_floor_cr=pl.lit(floor))
