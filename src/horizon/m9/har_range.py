"""Causal HAR remaining-range baseline for P1 V1n (completed sessions only)."""

from __future__ import annotations

import math

import polars as pl

from src.horizon.m9.implied_range import DEFAULT_RANGE_KAPPA, FULL_SESSION_BARS_15M

_PARKINSON_DENOM = 4.0 * math.log(2.0)


def attach_causal_har_remaining_range(
    panel: pl.DataFrame,
    *,
    kappa: float = DEFAULT_RANGE_KAPPA,
    full_session_bars: float = FULL_SESSION_BARS_15M,
    bars_col: str = "bars_to_mis",
) -> pl.DataFrame:
    """
    Parkinson 1d / 5d σ from **prior completed** sessions, scaled like implied range.

    ``range_har_* = κ · σ_day · sqrt(f)`` with ``f = bars_to_mis / full_session_bars``.
    Session T never sees T's high/low.
    """
    daily = (
        panel.sort(["symbol", "date"])
        .group_by(["symbol", "date_only"], maintain_order=True)
        .agg(day_high=pl.col("high").max(), day_low=pl.col("low").min())
        .with_columns(
            park_sigma=(
                (pl.col("day_high") / pl.col("day_low")).log() ** 2 / _PARKINSON_DENOM
            ).sqrt()
        )
        .sort(["symbol", "date_only"])
        .with_columns(
            park_1d=pl.col("park_sigma").shift(1).over("symbol"),
            park_5d=pl.col("park_sigma")
            .shift(1)
            .rolling_mean(window_size=5, min_samples=3)
            .over("symbol"),
        )
        .select(["symbol", "date_only", "park_1d", "park_5d"])
    )
    out = panel.join(daily, on=["symbol", "date_only"], how="left")
    f = (pl.col(bars_col).cast(pl.Float64) / full_session_bars).clip(0.0, 1.0).sqrt()
    return out.with_columns(
        range_har_1d=pl.lit(kappa) * pl.col("park_1d") * f,
        range_har_5d=pl.lit(kappa) * pl.col("park_5d") * f,
    )
