"""M9 range monetization — successor to directional Horizon Fresh Stage C.

See ``docs/next/horizon-m9-range-monetization-charter.md``.
Stage A/B live under ``src.horizon.fresh``; this package owns implied-range
math and V-gates only.
"""

from src.horizon.m9.implied_range import (
    DEFAULT_RANGE_KAPPA,
    india_vix_to_daily_sigma,
    implied_remaining_range,
)

__all__ = [
    "DEFAULT_RANGE_KAPPA",
    "india_vix_to_daily_sigma",
    "implied_remaining_range",
]
