"""PDT state machine and margin thresholds. Constants only — no order routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

PDT_MIN_EQUITY = 25_000.0
PDT_LOOKBACK_DAYS = 5
PDT_FLAG_DAY_TRADES = 4
PDT_DAY_TRADES_BELOW_MIN = 3
PDT_RESTRICTION_DAYS = 90

REG_T_INITIAL_MARGIN = 0.50
REG_T_LEVERAGE = 1.0 / REG_T_INITIAL_MARGIN
PORTFOLIO_MARGIN_MIN_EQUITY = 125_000.0
MAX_OVERNIGHT_LEVERAGE = 1.0


def is_portfolio_margin_eligible(equity: float) -> bool:
    return equity >= PORTFOLIO_MARGIN_MIN_EQUITY


def overnight_gross_allowed(equity: float) -> float:
    return equity * MAX_OVERNIGHT_LEVERAGE


@dataclass
class PdtState:
    equity: float
    day_trades: list[date] = field(default_factory=list)
    flagged_as_pdt: bool = False
    restriction_until: date | None = None

    def day_trades_in_window(self, session: date) -> int:
        start = session - timedelta(days=PDT_LOOKBACK_DAYS - 1)
        return sum(1 for day in self.day_trades if start <= day <= session)

    def can_day_trade(self, session: date, *, is_futures: bool = False) -> bool:
        if is_futures:
            return True
        if self.restriction_until is not None and session <= self.restriction_until:
            return False
        if self.equity >= PDT_MIN_EQUITY:
            return True
        return self.day_trades_in_window(session) < PDT_DAY_TRADES_BELOW_MIN

    def record_day_trade(self, session: date, *, is_futures: bool = False) -> None:
        if is_futures:
            return
        self.day_trades.append(session)
        if self.day_trades_in_window(session) >= PDT_FLAG_DAY_TRADES:
            self.flagged_as_pdt = True
            if self.equity < PDT_MIN_EQUITY:
                self.restriction_until = session + timedelta(days=PDT_RESTRICTION_DAYS)
