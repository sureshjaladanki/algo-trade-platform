"""N6 receipt assertion: every cash leg routes to a US account.

Standing broker-instruction plumbing is alien N0. This module is the gate.
"""

from __future__ import annotations

US_SETTLEMENT_COUNTRY = "US"


class NonUsReceiptBlocked(Exception):
    """N6: a non-US settlement instruction is blocked. No override."""


def assert_us_cash_leg(settlement_country: str) -> None:
    if settlement_country != US_SETTLEMENT_COUNTRY:
        raise NonUsReceiptBlocked(
            f"N6: cash leg must settle to a US account, not {settlement_country}"
        )
