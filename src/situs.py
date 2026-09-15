"""Situs classifier. N5 $60,000 US-situs cap is unchanged.

Irish UCITS units are not US-situs (working; W0 CSPX/XUSE/VWRA; GL2 CSUS/VXUA).
UK-incorporated shares (uk_register) are a refusal. Irish CAT is a class, not a
tax conclusion — s.75 CATCA 2003 is a W1 item.
"""

from __future__ import annotations

from enum import StrEnum

US_SITUS_CAP_USD = 60_000.0


class SitusClass(StrEnum):
    US = "us"
    UK = "uk"
    IRISH_CAT = "irish_cat"
    NON_SITUS = "non_situs"


class UkRegisterRefused(Exception):
    """UK-incorporated shares are refused (SDRT + UK IHT). No override."""


class SitusCapBlocked(Exception):
    """N5: aggregate US-situs market value would exceed $60,000. No override."""


def classify(*, situs_us: bool, uk_register: bool, irish_ucits: bool) -> SitusClass:
    if uk_register:
        return SitusClass.UK
    if situs_us:
        return SitusClass.US
    if irish_ucits:
        return SitusClass.IRISH_CAT
    return SitusClass.NON_SITUS


def refuse_uk_register(uk_register: bool) -> None:
    if uk_register:
        raise UkRegisterRefused("uk_register instruments are refused")


def assert_us_situs_cap(*, book_usd: float, additional_usd: float = 0.0) -> None:
    if book_usd < 0 or additional_usd < 0:
        raise ValueError("situs values must be >= 0")
    if book_usd + additional_usd > US_SITUS_CAP_USD:
        raise SitusCapBlocked(
            f"N5: US-situs {book_usd + additional_usd} exceeds {US_SITUS_CAP_USD}"
        )
