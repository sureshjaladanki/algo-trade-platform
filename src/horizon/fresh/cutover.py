"""M8 cutover decision scaffold — no silent production swap.

Ship only after Long K5 PASS + sober Precision read. Until then this module
records the decision checklist only.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.horizon.fresh.production_lock import (
    FROZEN_SURFACES,
    PRODUCTION_CUTOVER_MILESTONE,
)


@dataclass(frozen=True)
class CutoverDecision:
    ship: bool
    rationale: str
    k1_k5_reprint: str


def record_decision(decision: CutoverDecision) -> str:
    verb = "SHIP" if decision.ship else "NO-SHIP"
    lines = [
        f"M8 cutover decision: {verb}",
        f"milestone={PRODUCTION_CUTOVER_MILESTONE}",
        f"rationale: {decision.rationale}",
        f"K1–K5: {decision.k1_k5_reprint}",
        "Frozen surfaces until explicit ship wiring:",
        *[f"  - {s}" for s in FROZEN_SURFACES],
    ]
    if decision.ship:
        lines.append(
            "Ship checklist: point precision_pipeline registry to fresh admit; "
            "update cascade-strategy-overview Horizon section; "
            "legacy Top-K behind audit flag; MLflow Horizon_Fresh_* names."
        )
    else:
        lines.append(
            "No-ship: leave production unchanged; archive fresh package with "
            "blueprint §14 capability FAIL sentence if K-gates failed."
        )
    return "\n".join(lines)
