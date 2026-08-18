"""Absolute-admit registry for Precision (parallel to Top-K ``horizon_rank`` emit).

Rank columns, if retained, are capacity sort keys only — not economic gates.
"""

from __future__ import annotations

import polars as pl


def build_absolute_admit_registry(
    admitted: pl.DataFrame,
    *,
    require_cols: tuple[str, ...] = (
        "symbol",
        "date",
        "side",
        "tp_w",
        "sl_w",
        "ev_net_hat",
        "admit_ok",
    ),
) -> pl.DataFrame:
    """
    Frozen-barrier registry for Precision join.

    Barriers ``tp_w`` / ``sl_w`` are frozen at Stage C decision (g*, s*).
    """
    missing = [c for c in require_cols if c not in admitted.columns]
    if missing:
        raise ValueError(f"registry missing columns: {missing}")
    out = admitted.filter(pl.col("admit_ok"))
    if "capacity_rank" in out.columns:
        # Documented as capacity-only.
        return out.with_columns(
            registry_kind=pl.lit("absolute_admit"),
            capacity_sort_key=pl.col("capacity_rank"),
        )
    return out.with_columns(registry_kind=pl.lit("absolute_admit"))
