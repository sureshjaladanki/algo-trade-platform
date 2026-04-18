from enum import IntEnum


class TradingSession(IntEnum):
    UNKNOWN = 0
    WARMUP = 1
    OPENING = 2
    MIDDAY = 3
    CLOSING = 4
    SQUAREOFF = 5
