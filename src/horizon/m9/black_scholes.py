"""Black–Scholes ATM IV inversion for M9-0 (EOD FO bhavcopy).

Rates are set to 0: we need a VIX-style range converter, not a funding model.
``T`` is calendar years (DTE / 365).
"""

from __future__ import annotations

import math

from scipy.optimize import brentq
from scipy.stats import norm

MIN_SIGMA = 1e-6
MAX_SIGMA = 5.0


def black_scholes_price(
    spot: float,
    strike: float,
    time_years: float,
    sigma: float,
    *,
    is_call: bool,
    rate: float = 0.0,
) -> float:
    """Undiscounted-rate BS price; ``time_years <= 0`` returns intrinsic."""
    if time_years <= 0.0:
        return max(spot - strike, 0.0) if is_call else max(strike - spot, 0.0)
    sqrt_t = math.sqrt(time_years)
    d1 = (math.log(spot / strike) + (rate + 0.5 * sigma * sigma) * time_years) / (
        sigma * sqrt_t
    )
    d2 = d1 - sigma * sqrt_t
    discount = math.exp(-rate * time_years)
    if is_call:
        return spot * norm.cdf(d1) - strike * discount * norm.cdf(d2)
    return strike * discount * norm.cdf(-d2) - spot * norm.cdf(-d1)


def implied_volatility(
    premium: float,
    spot: float,
    strike: float,
    time_years: float,
    *,
    is_call: bool,
    rate: float = 0.0,
) -> float:
    """Invert BS for σ. Returns NaN when the quote cannot be a BS price."""
    if (
        premium <= 0.0
        or spot <= 0.0
        or strike <= 0.0
        or time_years <= 0.0
        or not math.isfinite(premium)
    ):
        return float("nan")
    intrinsic = (
        max(spot - strike, 0.0) if is_call else max(strike - spot, 0.0)
    )
    if premium < intrinsic:
        return float("nan")

    def _gap(sigma: float) -> float:
        return (
            black_scholes_price(
                spot, strike, time_years, sigma, is_call=is_call, rate=rate
            )
            - premium
        )

    lo = _gap(MIN_SIGMA)
    hi = _gap(MAX_SIGMA)
    if lo * hi > 0.0:
        return float("nan")
    return float(brentq(_gap, MIN_SIGMA, MAX_SIGMA, maxiter=80))
