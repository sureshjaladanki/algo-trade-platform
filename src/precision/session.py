"""NSE session / timing constants for Tier 3 Precision (reuses Tier 2 masks)."""

import datetime as dt

# Re-export Tier 2 entry / MIS masks — Precision must not invent a second clock.
from src.horizon.session import (  # noqa: F401
    MIS_FLAT_BY,
    long_entry_ok_expr,
    short_entry_ok_expr,
)

# Bounded wait after the 15m decision bar closes (bar-start + 15m).
WAIT_MINUTES = 5
# Vertical barrier length in minutes (H=4 × 15m) — clock from decision bar.
HORIZON_MINUTES = 60
# Decision bar length (group_by_dynamic bar-start convention).
DECISION_BAR_MINUTES = 15

# Top-K / bottom-K names Precision may touch (rank-based size beyond this → skip).
TOP_K = 8

# Afternoon cover gate for Shorts (verdict: time ≥ 13:00).
AFTERNOON_COVER_START = dt.time(13, 0)
