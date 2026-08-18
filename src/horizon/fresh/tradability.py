"""Stage A — deterministic tradability filter (effective cost vs working c*).

Accounting cost is locked at 20 bps; effective cost varies by name/session.
Drop cells where working ``c*`` is not realistically achievable.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from src.horizon.fresh.friction import C_STAR_BPS
from src.horizon.fresh.microstructure import (
    NSE_TICK_SIZE,
    STATUTORY_COST_BPS,
    tick_drag_bps,
)


@dataclass(frozen=True)
class TradabilityParams:
    statutory_bps: float = STATUTORY_COST_BPS
    tick: float = NSE_TICK_SIZE
    # Optional impact sketch as bps of ADV participation (0 = off).
    impact_bps: float = 0.0
    # Reject when c_eff exceeds this multiple of working c* (default: full budget).
    max_ceff_bps: float = C_STAR_BPS


def effective_cost_bps(
    *,
    price: float,
    half_spread_bps: float,
    params: TradabilityParams = TradabilityParams(),
) -> float:
    """
    ``c_eff ≈ statutory + 2×half-spread + tick_drag + impact`` (bps).

    ``half_spread_bps`` is one-way; round-trip uses 2×.
    """
    return (
        params.statutory_bps
        + 2.0 * half_spread_bps
        + tick_drag_bps(price, params.tick)
        + params.impact_bps
    )


def is_tradable(
    *,
    price: float,
    half_spread_bps: float,
    params: TradabilityParams = TradabilityParams(),
) -> bool:
    return effective_cost_bps(
        price=price, half_spread_bps=half_spread_bps, params=params
    ) <= params.max_ceff_bps


def attach_tradability_mask(
    bars: pl.DataFrame,
    *,
    spread_col: str = "cs_spread_bps",
    price_col: str = "close",
    params: TradabilityParams = TradabilityParams(),
) -> pl.DataFrame:
    """
    Join Stage A columns onto a bar panel that already has a spread estimate.

    ``spread_col`` must be a **full** spread in bps (CS/AR); half-spread = /2.
    Emits ``c_eff_bps``, ``tradable_ok``.
    """
    half = pl.col(spread_col) / 2.0
    tick_bps = (pl.lit(params.tick) / pl.col(price_col)) * 1e4
    c_eff = (
        pl.lit(params.statutory_bps)
        + 2.0 * half
        + tick_bps
        + pl.lit(params.impact_bps)
    )
    return bars.with_columns(
        c_eff_bps=c_eff,
        tradable_ok=c_eff <= params.max_ceff_bps,
    )


def rejection_mass_by_bucket(
    panel: pl.DataFrame,
    *,
    price_col: str = "close",
) -> pl.DataFrame:
    """Explain rejection mass by price bucket (not a silent black hole)."""
    return (
        panel.with_columns(
            price_bucket=pl.when(pl.col(price_col) < 200)
            .then(pl.lit("<200"))
            .when(pl.col(price_col) < 500)
            .then(pl.lit("200-500"))
            .when(pl.col(price_col) < 2000)
            .then(pl.lit("500-2000"))
            .otherwise(pl.lit(">=2000")),
        )
        .group_by("price_bucket")
        .agg(
            n=pl.len(),
            n_reject=(~pl.col("tradable_ok")).sum(),
            reject_rate=(~pl.col("tradable_ok")).mean(),
            median_ceff=pl.col("c_eff_bps").median(),
            median_spread=pl.col("cs_spread_bps").median()
            if "cs_spread_bps" in panel.columns
            else pl.lit(None),
        )
        .sort("price_bucket")
    )
