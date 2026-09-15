"""RNOR/ROR dates from docs/residency-calendar.md.

Until alien N0 this module reproduces that file. It does not count US days.
"""

from __future__ import annotations

from datetime import date

# Working cliff: last day of FY 2027-28. ROR from 1 Apr 2028. Not a filed opinion.
RNOR_CLIFF = date(2028, 3, 31)
ROR_START = date(2028, 4, 1)


def rnor_cliff() -> date:
    return RNOR_CLIFF


def ror_start() -> date:
    return ROR_START
