"""Venue settlement cycles, holidays, DST windows, and cliff-straddle arithmetic.

No I/O. The RNOR cliff is consumed from residency, not redefined here.
"""

from __future__ import annotations

from datetime import date, time, timedelta
from enum import StrEnum

from src.residency import rnor_cliff

# LSE T+2 until this date; T+1 on and after. Targeted 11 Oct 2027 (working, G20).
LSE_T1_SWITCH = date(2027, 10, 11)
CLIFF_MARGIN_DAYS = 14

# LSE 2028 from the exchange business-days calendar. Easter is April, not March.
# Final week of March 2028 (27–31) has no LSE holiday.
LSE_HOLIDAYS: frozenset[date] = frozenset(
    {
        date(2027, 3, 26),  # Good Friday
        date(2027, 3, 29),  # Easter Monday
        date(2027, 12, 27),  # Christmas Day observed
        date(2027, 12, 28),  # Boxing Day observed
        date(2028, 1, 3),  # New Year's Day observed
        date(2028, 4, 14),  # Good Friday
        date(2028, 4, 17),  # Easter Monday
        date(2028, 5, 1),  # Early May bank holiday
        date(2028, 5, 29),  # Spring bank holiday
        date(2028, 8, 28),  # Summer bank holiday
        date(2028, 12, 25),
        date(2028, 12, 26),
    }
)

# NSE 2028 weekday holidays that bound the cliff week (working until the
# exchange circular). Holi 11 Mar 2028 is Saturday. Final week of March 2028
# (27–31) has no NSE holiday on this table.
NSE_HOLIDAYS: frozenset[date] = frozenset(
    {
        date(2028, 3, 11),  # Holi (Saturday)
        date(2028, 4, 4),  # Ram Navami (working)
        date(2028, 4, 7),  # Mahavir Jayanti (working)
        date(2028, 4, 14),  # Good Friday / Ambedkar Jayanti
    }
)

US_HOLIDAYS: frozenset[date] = frozenset()

LSE_LAG_BEFORE_SWITCH = 2
LSE_LAG_AFTER_SWITCH = 1
T1_LAG = 1


class Venue(StrEnum):
    INDIA = "india"
    US = "us"
    LSE = "lse"


class ExposureClass(StrEnum):
    US_EXPOSURE = "us_exposure"
    EX_US_DEVELOPED = "ex_us_developed"


def _holidays(venue: Venue) -> frozenset[date]:
    if venue is Venue.LSE:
        return LSE_HOLIDAYS
    if venue is Venue.INDIA:
        return NSE_HOLIDAYS
    if venue is Venue.US:
        return US_HOLIDAYS
    raise ValueError(f"unknown venue {venue}")


def is_weekend(on: date) -> bool:
    return on.weekday() >= 5


def is_business_day(on: date, venue: Venue) -> bool:
    return not is_weekend(on) and on not in _holidays(venue)


def add_business_days(start: date, days: int, venue: Venue) -> date:
    if days < 1:
        raise ValueError("days must be >= 1")
    current = start
    remaining = days
    while remaining:
        current += timedelta(days=1)
        if is_business_day(current, venue):
            remaining -= 1
    return current


def settlement_lag(venue: Venue, trade_date: date) -> int:
    if venue is Venue.INDIA or venue is Venue.US:
        return T1_LAG
    if venue is Venue.LSE:
        if trade_date >= LSE_T1_SWITCH:
            return LSE_LAG_AFTER_SWITCH
        return LSE_LAG_BEFORE_SWITCH
    raise ValueError(f"unknown venue {venue}")


def receipt_date(trade_date: date, venue: Venue) -> date:
    return add_business_days(trade_date, settlement_lag(venue, trade_date), venue)


def latest_safe_trade_date(
    cliff: date, margin_days: int = CLIFF_MARGIN_DAYS
) -> date:
    if cliff != rnor_cliff():
        raise ValueError("cliff must be residency.rnor_cliff(); do not redefine it")
    if margin_days < CLIFF_MARGIN_DAYS:
        raise ValueError(f"margin_days must be >= {CLIFF_MARGIN_DAYS}")
    candidate = cliff - timedelta(days=margin_days)
    while not is_business_day(candidate, Venue.LSE):
        candidate -= timedelta(days=1)
    return candidate


def straddles_cliff(trade_date: date, venue: Venue, cliff: date) -> bool:
    """True if the receipt would fall after the cliff.

    LSE is checked at T+2 while G20's switch date is still working, so R1
    cannot arm a late-March trade on an assumed T+1.
    """
    if cliff != rnor_cliff():
        raise ValueError("cliff must be residency.rnor_cliff(); do not redefine it")
    lag = settlement_lag(venue, trade_date)
    if venue is Venue.LSE:
        lag = max(lag, LSE_LAG_BEFORE_SWITCH)
    return add_business_days(trade_date, lag, venue) > cliff


def _nth_weekday(year: int, month: int, *, weekday: int, n: int) -> date:
    current = date(year, month, 1)
    seen = 0
    while current.month == month:
        if current.weekday() == weekday:
            seen += 1
            if seen == n:
                return current
        current += timedelta(days=1)
    raise ValueError(f"no {n}th weekday {weekday} in {year}-{month:02d}")


def _last_weekday(year: int, month: int, *, weekday: int) -> date:
    if month == 12:
        current = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        current = date(year, month + 1, 1) - timedelta(days=1)
    while current.weekday() != weekday:
        current -= timedelta(days=1)
    return current


def us_dst_start(year: int) -> date:
    """Second Sunday of March."""
    return _nth_weekday(year, 3, weekday=6, n=2)


def uk_bst_start(year: int) -> date:
    """Last Sunday of March. 2028 is 26 Mar."""
    return _last_weekday(year, 3, weekday=6)


def uk_bst_end(year: int) -> date:
    """Last Sunday of October."""
    return _last_weekday(year, 10, weekday=6)


def us_dst_end(year: int) -> date:
    """First Sunday of November."""
    return _nth_weekday(year, 11, weekday=6, n=1)


def in_dst_gap(on: date) -> bool:
    """London/New York offset is one hour off the winter/summer normal.

    Spring: US EDT from the 2nd Sunday of March until UK BST on the last.
    Autumn: UK still BST from last Sunday of October until US EST on the first
    Sunday of November. Windows start 13:30 London (GS9 / G21).
    """
    spring_us = us_dst_start(on.year)
    spring_uk = uk_bst_start(on.year)
    autumn_uk = uk_bst_end(on.year)
    autumn_us = us_dst_end(on.year)
    return spring_us <= on < spring_uk or autumn_uk <= on < autumn_us


def session_window(exposure_class: ExposureClass, on: date) -> tuple[time, time]:
    start = time(13, 30) if in_dst_gap(on) else time(14, 30)
    if exposure_class is ExposureClass.US_EXPOSURE:
        return start, time(16, 20)
    if exposure_class is ExposureClass.EX_US_DEVELOPED:
        return start, time(15, 30)
    raise ValueError(f"unknown exposure_class {exposure_class}")


def in_session_window(
    exposure_class: ExposureClass, on: date, london_time: time
) -> bool:
    open_at, close_at = session_window(exposure_class, on)
    return open_at <= london_time <= close_at
