from enum import Enum


class DailyRegime(Enum):
    SUPPORTIVE = "SUPPORTIVE"
    AMBIGUOUS = "AMBIGUOUS"
    HOSTILE = "HOSTILE"
    NO_TRADE = "NO_TRADE"

class IntradayRegime(Enum):
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    CHOP = "CHOP"
    HIGH_VOL = "HIGH_VOL"
