"""Unit tests — Stage A tradability (M2)."""

from __future__ import annotations

import polars as pl

from src.horizon.fresh.microstructure import tick_drag_bps
from src.horizon.fresh.tradability import (
    TradabilityParams,
    attach_tradability_mask,
    effective_cost_bps,
    is_tradable,
)


def test_tick_drag_known_prices() -> None:
    # ₹200 → 0.05/200 = 2.5 bps; ₹5000 → 0.1 bps
    assert abs(tick_drag_bps(200.0) - 2.5) < 1e-9
    assert abs(tick_drag_bps(5000.0) - 0.1) < 1e-9


def test_worse_spread_likelier_reject() -> None:
    params = TradabilityParams(max_ceff_bps=20.0)
    cheap = is_tradable(price=2000.0, half_spread_bps=2.0, params=params)
    rich = is_tradable(price=2000.0, half_spread_bps=12.0, params=params)
    assert cheap is True
    assert rich is False
    assert effective_cost_bps(
        price=2000.0, half_spread_bps=12.0, params=params
    ) > effective_cost_bps(price=2000.0, half_spread_bps=2.0, params=params)


def test_attach_tradability_mask_monotonic() -> None:
    df = pl.DataFrame(
        {
            "symbol": ["A", "A"],
            "date": [1, 2],
            "close": [200.0, 5000.0],
            "cs_spread_bps": [30.0, 2.0],
        }
    )
    out = attach_tradability_mask(df)
    # Low-priced wide-spread name should have higher c_eff than liquid high-priced.
    assert out["c_eff_bps"][0] > out["c_eff_bps"][1]
    assert out["tradable_ok"].dtype == pl.Boolean
