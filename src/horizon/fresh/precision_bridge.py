"""M7 scaffolding — Precision join path to fresh absolute-admit registry.

Precision Execution Bridge charter stays orthogonal (frozen production Top-K).
This module only defines the wiring contract for re-measure on the fresh book.
Precision result ≠ Horizon K4/K5.
"""

from __future__ import annotations

import polars as pl

from src.horizon.fresh.registry import build_absolute_admit_registry
from src.horizon.session import MIS_FLAT_BY, MIS_EXIT_BAR_END


def join_precision_to_fresh_registry(
    precision_1m: pl.DataFrame,
    admitted_15m: pl.DataFrame,
) -> pl.DataFrame:
    """
    Attach Precision 1m paths to frozen-barrier fresh registry rows.

    Barriers stay frozen at Horizon decision; do not recompute TB from 1m.
    """
    registry = build_absolute_admit_registry(admitted_15m)
    # Decision-bar key join; Precision features attach downstream.
    keys = ["symbol", "date"]
    return precision_1m.join(
        registry.select(
            [
                c
                for c in registry.columns
                if c in keys or c in {"tp_w", "sl_w", "ev_net_hat", "side", "registry_kind"}
            ]
        ),
        on=keys,
        how="inner",
    )


PRECISION_BOUNDARY_NOTE = (
    "Precision monetizes an already absolute-EV+ book (~2–4 bps timing). "
    "Never claim Horizon K4/K5 PASS from Precision P3. "
    f"MIS clocks shared: flat_by={MIS_FLAT_BY}, exit_bar_end={MIS_EXIT_BAR_END}."
)
