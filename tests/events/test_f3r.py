import datetime as dt

import pytest

from src.events.f3r import (
    announcement_for_cutoff,
    capital_verdict,
    entry_month_for_cutoff,
    equal_weight_residual,
    n_semi_annual_additions,
    semi_annual_cutoffs,
)
from src.events.residual import residual_bps


def test_twenty_two_cutoffs_each_have_a_pr() -> None:
    cutoffs = semi_annual_cutoffs()
    assert len(cutoffs) == 22
    assert cutoffs[0] == dt.date(2015, 1, 31)
    assert cutoffs[-1] == dt.date(2025, 7, 31)
    for cutoff in cutoffs:
        day, source = announcement_for_cutoff(cutoff)
        assert day > cutoff
        assert source


def test_entry_month_is_february_or_august() -> None:
    assert entry_month_for_cutoff(dt.date(2018, 1, 31)) == 2
    assert entry_month_for_cutoff(dt.date(2018, 7, 31)) == 8


def test_empty_cycles_are_included() -> None:
    assert n_semi_annual_additions(dt.date(2016, 7, 31)) == 0
    assert n_semi_annual_additions(dt.date(2023, 1, 31)) == 0
    assert announcement_for_cutoff(dt.date(2016, 7, 31))[0] == dt.date(2016, 8, 12)


def test_missing_slot_is_cash_zero() -> None:
    start = dt.date(2020, 2, 3)
    end = dt.date(2020, 2, 21)
    closes = {
        ("A.NS", start): 100.0,
        ("A.NS", end): 110.0,
        ("B.NS", start): 100.0,
        ("B.NS", end): 100.0,
    }
    nifty = {start: 200.0, end: 210.0}
    mean, covered, slots = equal_weight_residual(
        closes, nifty, ["A.NS", "B.NS", "C.NS"], start, end
    )
    a = residual_bps(100.0, 110.0, 200.0, 210.0)
    b = residual_bps(100.0, 100.0, 200.0, 210.0)
    assert slots == 3
    assert covered == 2
    assert mean == pytest.approx((a + b + 0.0) / 3.0)


def test_capital_verdict_locks() -> None:
    assert capital_verdict(500.0, 10.0, 100.0, 50.0) == "GO"
    assert capital_verdict(500.0, 10.0, 100.0, -1.0) == "INCONCLUSIVE"
    assert capital_verdict(500.0, -1.0, 100.0, 50.0) == "INCONCLUSIVE"
    assert capital_verdict(400.0, 10.0, 100.0, 50.0) == "INCONCLUSIVE"
    assert capital_verdict(250.0, -10.0, 100.0, 50.0) == "STOP"
