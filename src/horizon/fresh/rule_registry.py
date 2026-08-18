"""Primary-rule registry — family + side for one-sleeve Stage C (M4R).

Blueprint §5.2: one rule, one sleeve, one head. Do not pool opposite-sign
rules into a single Long head with rule identity as a feature.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Family = Literal["reversion", "continuation", "volatility"]
Side = Literal["long", "short"]


@dataclass(frozen=True)
class RegisteredRule:
    rule_id: str
    family: Family
    side: Side
    description: str
    causality: str


# Pre-registered candidate set for the M4R drift-sign ledger.
# Continuations that fired Long in M5 are kept so the ledger can reject them
# with evidence; reversion rules cover both sides.
RULE_REGISTRY: tuple[RegisteredRule, ...] = (
    RegisteredRule(
        "vwap_reclaim",
        "reversion",
        "long",
        "Close reclaims VWAP after ≥2 bars below",
        "VWAP cumulates within session; prior bars below counted causally",
    ),
    RegisteredRule(
        "vwap_loss",
        "reversion",
        "short",
        "Close loses VWAP after ≥2 bars above",
        "Symmetric to vwap_reclaim; prior bars above counted causally",
    ),
    RegisteredRule(
        "orb_fade_long",
        "reversion",
        "long",
        "Close re-enters ORB from below after breaking ORB low",
        "ORB bounds from first two post-bleed bars; signal on reclaim close",
    ),
    RegisteredRule(
        "orb_fade_short",
        "reversion",
        "short",
        "Close re-enters ORB from above after breaking ORB high",
        "ORB bounds from first two post-bleed bars; signal on fail close",
    ),
    RegisteredRule(
        "prior_day_high_reject",
        "reversion",
        "short",
        "Close rejects prior-day high after touching it (failed breakout)",
        "Prior-day high from completed prior session; touch then close back below",
    ),
    RegisteredRule(
        "prior_day_low_reject",
        "reversion",
        "long",
        "Close rejects prior-day low after touching it (failed breakdown)",
        "Prior-day low from completed prior session; touch then close back above",
    ),
    RegisteredRule(
        "gap_fill_long",
        "reversion",
        "long",
        "Open gap-down fills back to prior close",
        "Prior close from completed prior session; fill on close ≥ prior close",
    ),
    RegisteredRule(
        "gap_fill_short",
        "reversion",
        "short",
        "Open gap-up fills back to prior close",
        "Prior close from completed prior session; fill on close ≤ prior close",
    ),
    RegisteredRule(
        "orb_break_vol",
        "continuation",
        "long",
        "ORB high break with volume > 20-bar median",
        "ORB high/volume from prior bars only; signal on close of break bar",
    ),
    RegisteredRule(
        "prior_day_high",
        "continuation",
        "long",
        "Close breaks prior session high",
        "Prior-day high from completed prior session only",
    ),
    RegisteredRule(
        "range_expand_2x",
        "volatility",
        "long",
        "Bar range > 2× TOD median range (Long sleeve placeholder)",
        "TOD median uses shift(1) history only; side inherited from M5 Long pool",
    ),
)

_BY_ID = {r.rule_id: r for r in RULE_REGISTRY}


def get_rule(rule_id: str) -> RegisteredRule:
    return _BY_ID[rule_id]


def rules_for(*, family: Family | None = None, side: Side | None = None) -> tuple[RegisteredRule, ...]:
    out = RULE_REGISTRY
    if family is not None:
        out = tuple(r for r in out if r.family == family)
    if side is not None:
        out = tuple(r for r in out if r.side == side)
    return out


def sleeve_id(family: Family, side: Side) -> str:
    return f"{side}_{family}"
