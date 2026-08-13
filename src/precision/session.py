"""NSE session / timing constants for Tier 3 Precision (reuses Tier 2 masks)."""

import datetime as dt

# Re-export Tier 2 entry / wall-clock MIS flatten — Precision must not invent
# a second live clock. 15m label exit stamps use MIS_EXIT_BAR_END separately.
from src.horizon.session import (  # noqa: F401
    MIS_FLAT_BY,
    long_entry_ok_expr,
    short_entry_ok_expr,
)
from src.utils.eval_common import HORIZON_MINUTES  # noqa: F401  # cascade H_BARS × 15m

# Bounded wait on 1m bars starting at the 15m decision bar (bar-end / actionable).
WAIT_MINUTES = 5

# Top-K / bottom-K names Precision may touch (rank-based size beyond this → skip).
# Phase 1 selectivity: tightened 8 → 5 (drop ranks 6–8; do not micro-size them).
TOP_K = 5

# Afternoon cover gate for Shorts (verdict: time ≥ 13:00).
AFTERNOON_COVER_START = dt.time(13, 0)
