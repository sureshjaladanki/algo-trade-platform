"""Point-in-time listing panel, ADV, and liquidity buckets."""

from __future__ import annotations

from enum import StrEnum


class LiquidityBucket(StrEnum):
    LIQUID_ETF = "liquid_etf"
    LARGE_CAP = "large_cap"
    MID_CAP = "mid_cap"
    SMALL_CAP = "small_cap"
    MICRO_CLOSED = "micro_closed"


LIQUID_ETF_SYMBOLS = frozenset({"SPY", "VTI", "QQQ", "ITOT", "SCHB", "VXUS"})
ADV_LARGE_USD = 100_000_000.0
ADV_MID_USD = 20_000_000.0
ADV_SMALL_USD = 2_000_000.0


def liquidity_bucket(adv_usd: float, *, symbol: str | None = None) -> LiquidityBucket:
    if symbol in LIQUID_ETF_SYMBOLS:
        return LiquidityBucket.LIQUID_ETF
    if adv_usd >= ADV_LARGE_USD:
        return LiquidityBucket.LARGE_CAP
    if adv_usd >= ADV_MID_USD:
        return LiquidityBucket.MID_CAP
    if adv_usd >= ADV_SMALL_USD:
        return LiquidityBucket.SMALL_CAP
    return LiquidityBucket.MICRO_CLOSED
