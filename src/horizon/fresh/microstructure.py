"""Spread / tick microstructure helpers for fresh Stage A (not range-as-spread).

Corwin–Schultz and Abdi–Ranaldo estimate effective spread from OHLC.
Do **not** call ``(H−L)/close`` “spread” in fresh code — that is a range proxy
kept only in production Precision until cutover.
"""

from __future__ import annotations

import math

import polars as pl

# NSE equity tick (most cash names). Override per name if needed later.
NSE_TICK_SIZE = 0.05
STATUTORY_COST_BPS = 4.0  # sketch: fees/taxes share of round-trip


def tick_drag_bps(price: float, tick: float = NSE_TICK_SIZE) -> float:
    """One-tick adverse move in bps of price."""
    if price <= 0:
        raise ValueError(f"price must be positive, got {price}")
    return (tick / price) * 1e4


def range_proxy_bps_expr(
    high: str = "high",
    low: str = "low",
    close: str = "close",
) -> pl.Expr:
    """Production Precision proxy — named explicitly so it is not called spread."""
    return ((pl.col(high) - pl.col(low)) / pl.col(close)) * 1e4


def _cs_spread_frac_expr(high: str, low: str) -> pl.Expr:
    beta = (pl.col(high) / pl.col(low)).log() ** 2 + (
        pl.col(high).shift(1) / pl.col(low).shift(1)
    ).log() ** 2
    gamma = (
        pl.max_horizontal(pl.col(high), pl.col(high).shift(1))
        / pl.min_horizontal(pl.col(low), pl.col(low).shift(1))
    ).log() ** 2
    denom = 3.0 - 2.0 * math.sqrt(2.0)
    alpha = (beta.sqrt() * (math.sqrt(2.0) - 1.0) / denom) - (gamma / denom).sqrt()
    return (2.0 * (alpha.exp() - 1.0) / (1.0 + alpha.exp())).clip(lower_bound=0.0)


def corwin_schultz_spread_bps(
    df: pl.DataFrame,
    *,
    symbol_col: str = "symbol",
    high: str = "high",
    low: str = "low",
) -> pl.DataFrame:
    """Two-bar Corwin–Schultz spread estimator in bps of close (clipped ≥ 0)."""
    return (
        df.sort([symbol_col, "date"])
        .with_columns(
            cs_spread_bps=(
                _cs_spread_frac_expr(high, low) * 1e4
            ).over(symbol_col),
        )
    )


def abdi_ranaldo_spread_bps(
    df: pl.DataFrame,
    *,
    symbol_col: str = "symbol",
    high: str = "high",
    low: str = "low",
    close: str = "close",
    window: int = 20,
) -> pl.DataFrame:
    """Abdi–Ranaldo close-mid estimator in bps (rolling product expectation)."""
    mid = (pl.col(high) + pl.col(low)) / 2.0
    innov = (pl.col(close) - mid) * (pl.col(close).shift(1) - mid.shift(1))
    roll = innov.rolling_mean(window_size=window, min_samples=5)
    spread_frac = (
        2.0 * roll.clip(lower_bound=0.0).sqrt() / pl.col(close)
    ).clip(lower_bound=0.0)
    return (
        df.sort([symbol_col, "date"])
        .with_columns(ar_spread_bps=(spread_frac * 1e4).over(symbol_col))
    )


def attach_spread_panel(
    bars: pl.DataFrame,
    *,
    symbol_col: str = "symbol",
) -> pl.DataFrame:
    """Attach CS + AR estimators and the named range proxy (not for Stage A cost)."""
    if symbol_col not in bars.columns:
        raise ValueError(f"missing {symbol_col}")
    out = corwin_schultz_spread_bps(bars, symbol_col=symbol_col)
    out = abdi_ranaldo_spread_bps(out, symbol_col=symbol_col)
    return out.with_columns(range_proxy_bps=range_proxy_bps_expr())
