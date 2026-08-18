"""Single friction import path for fresh Horizon work.

Do not redefine ``c*`` here — re-export the production charter constants so
fresh and legacy ledgers never diverge on cost.
"""

from src.labels.triple_barrier import (
    ARCHIVE_ROUND_TRIP_COST,
    BPS,
    ROUND_TRIP_COST,
)

# Aliases preferred in fresh docs / Stage A–D code.
C_STAR = ROUND_TRIP_COST  # 20 bps working cost
C_STAR_BPS = ROUND_TRIP_COST * BPS  # 20.0
ARCHIVE_C_STAR = ARCHIVE_ROUND_TRIP_COST  # 30 bps stress only
ARCHIVE_C_STAR_BPS = ARCHIVE_ROUND_TRIP_COST * BPS

# Stage B admit threshold: q25(remaining range) >= 10 * c*
OPPORTUNITY_SPAN_MULT = 10.0
OPPORTUNITY_MIN_RANGE = OPPORTUNITY_SPAN_MULT * C_STAR  # 200 bps

# K2: post-gate mean |move| >= 8 * c*
K2_MOVE_MULT = 8.0
K2_MIN_MOVE = K2_MOVE_MULT * C_STAR  # 160 bps

__all__ = [
    "ARCHIVE_C_STAR",
    "ARCHIVE_C_STAR_BPS",
    "ARCHIVE_ROUND_TRIP_COST",
    "BPS",
    "C_STAR",
    "C_STAR_BPS",
    "K2_MIN_MOVE",
    "K2_MOVE_MULT",
    "OPPORTUNITY_MIN_RANGE",
    "OPPORTUNITY_SPAN_MULT",
    "ROUND_TRIP_COST",
]
