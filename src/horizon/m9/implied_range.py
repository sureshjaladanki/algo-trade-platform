"""Implied remaining-session range from IV / India VIX (M9 V0/V1).

Charter: docs/next/horizon-m9-range-monetization-charter.md
"""

from __future__ import annotations

import numpy as np
import polars as pl

# Parkinson-style multiplier: E[H−L] ≈ κ · σ · √Δt for Brownian motion.
# Pre-registered default; 1.4 / 1.8 are report-only sensitivity.
DEFAULT_RANGE_KAPPA = 1.6
TRADING_DAYS_PER_YEAR = 252.0
# Full cash session in 15m bars after bleed (~09:45–15:15) ≈ 23 bars.
FULL_SESSION_BARS_15M = 23


def india_vix_to_daily_sigma(vix_level: float | np.ndarray) -> float | np.ndarray:
    """India VIX (percent) → one-day return σ (fraction)."""
    return np.asarray(vix_level, dtype=float) / (100.0 * np.sqrt(TRADING_DAYS_PER_YEAR))


def implied_remaining_range(
    iv_percent: float | np.ndarray,
    bars_to_mis: float | np.ndarray,
    *,
    kappa: float = DEFAULT_RANGE_KAPPA,
    full_session_bars: float = FULL_SESSION_BARS_15M,
) -> float | np.ndarray:
    """
    ``R_imp ≈ κ · σ_day · sqrt(f)`` with ``f = bars_to_mis / full_session_bars``.

    Returns a **fraction of spot** (same units as Stage B ``remaining_range``).
    """
    sigma_day = india_vix_to_daily_sigma(iv_percent)
    f = np.clip(np.asarray(bars_to_mis, dtype=float) / full_session_bars, 0.0, 1.0)
    return kappa * sigma_day * np.sqrt(f)


def attach_vix_implied_range(
    panel: pl.DataFrame,
    vix_daily: pl.DataFrame,
    *,
    kappa: float = DEFAULT_RANGE_KAPPA,
    bars_col: str = "bars_to_mis",
) -> pl.DataFrame:
    """
    Join prior-session India VIX close onto a bar panel; emit ``range_imp_vix``.

    ``vix_daily`` must have ``date_only`` (Date) and ``vix_close`` (float, percent).
    Uses **T−1** VIX for session T (no look-ahead into the decision day).
    """
    vix = (
        vix_daily.sort("date_only")
        .with_columns(vix_close_lag1=pl.col("vix_close").shift(1))
        .select(["date_only", "vix_close_lag1"])
    )
    out = panel.join(vix, on="date_only", how="left")
    btm = out[bars_col].to_numpy().astype(float)
    vix_lvl = out["vix_close_lag1"].to_numpy().astype(float)
    r_imp = implied_remaining_range(vix_lvl, btm, kappa=kappa)
    return out.with_columns(range_imp_vix=pl.Series(r_imp))


def attach_atm_implied_range(
    panel: pl.DataFrame,
    *,
    kappa: float = DEFAULT_RANGE_KAPPA,
    iv_col: str = "atm_iv_pct",
    bars_col: str = "bars_to_mis",
) -> pl.DataFrame:
    """Emit ``range_imp_atm`` from lagged single-name ATM IV already on the panel."""
    r_imp = implied_remaining_range(
        panel[iv_col].to_numpy(),
        panel[bars_col].to_numpy(),
        kappa=kappa,
    )
    return panel.with_columns(range_imp_atm=pl.Series(r_imp))


def daily_vix_from_1m(vix_1m: pl.DataFrame) -> pl.DataFrame:
    """Collapse India VIX 1m OHLCV to one close per calendar session."""
    return (
        vix_1m.sort("date")
        .with_columns(date_only=pl.col("date").dt.date())
        .group_by("date_only")
        .agg(vix_close=pl.col("close").last())
        .sort("date_only")
    )
