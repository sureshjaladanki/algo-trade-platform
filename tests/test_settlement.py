"""Settlement cycles, cliff margin, holidays, and session windows."""

from datetime import date, time
from pathlib import Path

import pytest

from src.residency import RNOR_CLIFF, ROR_START, rnor_cliff, ror_start
from src.settlement import (
    CLIFF_MARGIN_DAYS,
    LSE_T1_SWITCH,
    ExposureClass,
    Venue,
    add_business_days,
    in_dst_gap,
    is_business_day,
    latest_safe_trade_date,
    receipt_date,
    session_window,
    straddles_cliff,
    uk_bst_start,
    us_dst_start,
)


def test_residency_reproduces_calendar_file() -> None:
    assert rnor_cliff() == RNOR_CLIFF == date(2028, 3, 31)
    assert ror_start() == ROR_START == date(2028, 4, 1)
    assert rnor_cliff().weekday() == 4  # Friday


def test_receipt_date_india_and_us_are_t1() -> None:
    friday = date(2028, 3, 17)
    monday = date(2028, 3, 20)
    assert receipt_date(friday, Venue.INDIA) == monday
    assert receipt_date(friday, Venue.US) == monday


def test_receipt_date_lse_both_sides_of_t1_switch() -> None:
    assert LSE_T1_SWITCH == date(2027, 10, 11)
    before = date(2027, 10, 8)  # Friday, still T+2
    on_switch = date(2027, 10, 11)  # Monday, T+1
    assert receipt_date(before, Venue.LSE) == date(2027, 10, 12)
    assert receipt_date(on_switch, Venue.LSE) == date(2027, 10, 12)
    thursday_before = date(2027, 10, 7)
    assert receipt_date(thursday_before, Venue.LSE) == date(2027, 10, 11)


def test_straddles_cliff_true_for_30_mar_2028_lse_at_t2() -> None:
    cliff = rnor_cliff()
    t2_receipt = add_business_days(date(2028, 3, 30), 2, Venue.LSE)
    assert t2_receipt == date(2028, 4, 3)
    assert t2_receipt > cliff
    assert straddles_cliff(date(2028, 3, 30), Venue.LSE, cliff)


def test_straddles_cliff_false_at_latest_safe_trade_date() -> None:
    cliff = rnor_cliff()
    safe = latest_safe_trade_date(cliff)
    assert safe == date(2028, 3, 17)
    assert (cliff - safe).days >= CLIFF_MARGIN_DAYS
    assert not straddles_cliff(safe, Venue.LSE, cliff)
    assert add_business_days(safe, 2, Venue.LSE) <= cliff


def test_latest_safe_is_lse_and_nse_business_day() -> None:
    safe = latest_safe_trade_date(rnor_cliff())
    assert is_business_day(safe, Venue.LSE)
    assert is_business_day(safe, Venue.INDIA)
    for day in (date(2028, 3, 27), date(2028, 3, 28), date(2028, 3, 29), date(2028, 3, 30), date(2028, 3, 31)):
        assert is_business_day(day, Venue.LSE)
        assert is_business_day(day, Venue.INDIA)


def test_latest_safe_rejects_a_redefined_cliff() -> None:
    with pytest.raises(ValueError, match="residency"):
        latest_safe_trade_date(date(2028, 3, 30))


def test_uk_bst_and_us_edt_2028() -> None:
    assert uk_bst_start(2028) == date(2028, 3, 26)
    assert us_dst_start(2028) == date(2028, 3, 12)
    assert in_dst_gap(date(2028, 3, 12))
    assert in_dst_gap(date(2028, 3, 25))
    assert not in_dst_gap(date(2028, 3, 26))
    assert not in_dst_gap(date(2028, 3, 29))


def test_gl0_cliff_calendar_artefact_exists() -> None:
    path = Path(__file__).resolve().parents[1] / "docs" / "archive" / "gl0-cliff-calendar.md"
    text = path.read_text(encoding="utf-8")
    assert "17 Mar 2028" in text
    assert "30 Mar 2028" in text
    assert "straddles" in text.lower()


def test_session_window_us_and_exus() -> None:
    normal = date(2028, 3, 29)
    gap = date(2028, 3, 20)
    assert session_window(ExposureClass.US_EXPOSURE, normal) == (time(14, 30), time(16, 20))
    assert session_window(ExposureClass.EX_US_DEVELOPED, normal) == (time(14, 30), time(15, 30))
    assert session_window(ExposureClass.US_EXPOSURE, gap) == (time(13, 30), time(16, 20))
    assert session_window(ExposureClass.EX_US_DEVELOPED, gap) == (time(13, 30), time(15, 30))
