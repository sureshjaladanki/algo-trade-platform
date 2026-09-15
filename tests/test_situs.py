"""UK-register refusal, Irish UCITS non-US class, unchanged N5 cap."""

import pytest

from src.books.wrapper import CSPX, CSUS, VWRA, VXUA, XUSE
from src.situs import (
    US_SITUS_CAP_USD,
    SitusCapBlocked,
    SitusClass,
    UkRegisterRefused,
    assert_us_situs_cap,
    classify,
    refuse_uk_register,
)


def test_uk_register_is_refused() -> None:
    assert classify(situs_us=False, uk_register=True, irish_ucits=False) is SitusClass.UK
    with pytest.raises(UkRegisterRefused):
        refuse_uk_register(True)
    refuse_uk_register(False)


def test_irish_ucits_are_not_us_situs() -> None:
    assert not CSPX.situs_us and not XUSE.situs_us and not VWRA.situs_us
    assert not CSUS.situs_us and not VXUA.situs_us
    irish = classify(situs_us=False, uk_register=False, irish_ucits=True)
    assert irish is SitusClass.IRISH_CAT
    us_listed = classify(situs_us=True, uk_register=False, irish_ucits=False)
    assert us_listed is SitusClass.US


def test_n5_cap_is_sixty_thousand_and_blocks_over() -> None:
    assert US_SITUS_CAP_USD == 60_000.0
    assert_us_situs_cap(book_usd=60_000.0)
    with pytest.raises(SitusCapBlocked):
        assert_us_situs_cap(book_usd=50_000.0, additional_usd=10_000.01)
