"""W2 synthetic vs physical, locked to 31 Jul 2026 factsheets. GL4 extends the same gate."""

from datetime import date

import pytest

from src.books.synthetic import (
    BOND_SYNTHETIC_USD_ACC_5Y_PAIR,
    COUNTERPARTY_CAP_NAV,
    CSPX_5Y_ANNUALISED,
    EM_INDEX_GROSS_5Y_ANNUALISED,
    EM_INDEX_NET_5Y_ANNUALISED,
    EXUS_SYNTHETIC_LISTED,
    IEMA_5Y_ANNUALISED,
    INDEX_GROSS_5Y_ANNUALISED,
    INDEX_NET_5Y_ANNUALISED,
    MXFS_COUNTERPARTIES,
    MXFS_COUNTERPARTY_EXPOSURE_WITHIN_CAP,
    MXFS_MAX_COUNTERPARTY_MTM_NAV,
    SPXS_COUNTERPARTIES,
    SYNTHETIC_ADVANTAGE_HURDLE_BPS,
    UCITS_OTC_COUNTERPARTY_CAP,
    XUSE_ISIN,
    XUSE_LAUNCH,
    advantage_vs_physical_bps,
    annualise_cumulative,
    em_advantage_vs_physical_bps,
    em_tracking_vs_gross_index_bps,
    em_tracking_vs_net_index_bps,
    exus_history_years,
    gl4_bond_passes,
    gl4_em_passes,
    gl4_exus_passes,
    gl4_passes,
    mxfs_5y_annualised,
    spxs_5y_annualised,
    synthetic_non_us_leg_weight,
    synthetic_us_leg_weight,
    tracking_vs_gross_index_bps,
    tracking_vs_net_index_bps,
    w2_passes,
)


def test_five_year_window_and_synthetic_beats_physical() -> None:
    assert spxs_5y_annualised() == pytest.approx(annualise_cumulative(0.8230))
    assert CSPX_5Y_ANNUALISED == pytest.approx(0.1255)
    saving = advantage_vs_physical_bps()
    assert saving == pytest.approx(
        (spxs_5y_annualised() - CSPX_5Y_ANNUALISED) * 10_000.0
    )
    assert saving >= SYNTHETIC_ADVANTAGE_HURDLE_BPS
    assert saving == pytest.approx(20.6, abs=1.0)


def test_tracking_vs_net_and_gross() -> None:
    assert INDEX_NET_5Y_ANNUALISED == pytest.approx(0.1237)
    assert tracking_vs_net_index_bps(spxs_5y_annualised()) == pytest.approx(38.6, abs=1.0)
    assert tracking_vs_net_index_bps(CSPX_5Y_ANNUALISED) == pytest.approx(18.0, abs=0.2)
    assert tracking_vs_gross_index_bps(spxs_5y_annualised()) < 0
    assert tracking_vs_gross_index_bps(CSPX_5Y_ANNUALISED) < tracking_vs_gross_index_bps(
        spxs_5y_annualised()
    )
    assert INDEX_GROSS_5Y_ANNUALISED > INDEX_NET_5Y_ANNUALISED


def test_counterparty_cap_and_871m_path() -> None:
    assert UCITS_OTC_COUNTERPARTY_CAP == COUNTERPARTY_CAP_NAV
    assert len(SPXS_COUNTERPARTIES) >= 2
    assert w2_passes()
    assert synthetic_us_leg_weight() == pytest.approx(0.50)


def test_exus_has_no_synthetic_and_short_history() -> None:
    assert not EXUS_SYNTHETIC_LISTED
    assert not BOND_SYNTHETIC_USD_ACC_5Y_PAIR
    assert XUSE_ISIN == "IE000R4ZNTN3"
    assert XUSE_LAUNCH == date(2025, 1, 24)
    assert exus_history_years() < 5.0
    assert not gl4_exus_passes()
    assert not gl4_bond_passes()


def test_em_advantage_vs_physical_below_hurdle() -> None:
    assert mxfs_5y_annualised() == pytest.approx(annualise_cumulative(0.4508))
    assert IEMA_5Y_ANNUALISED == pytest.approx(0.0804)
    saving = em_advantage_vs_physical_bps()
    assert saving == pytest.approx(
        (mxfs_5y_annualised() - IEMA_5Y_ANNUALISED) * 10_000.0
    )
    assert saving < SYNTHETIC_ADVANTAGE_HURDLE_BPS
    assert saving == pytest.approx(-31.2, abs=1.0)
    assert not gl4_em_passes()


def test_em_tracking_vs_net_and_gross() -> None:
    assert EM_INDEX_NET_5Y_ANNUALISED == pytest.approx(0.0803)
    assert em_tracking_vs_net_index_bps(mxfs_5y_annualised()) < 0
    assert em_tracking_vs_net_index_bps(IEMA_5Y_ANNUALISED) == pytest.approx(
        1.0, abs=0.2
    )
    assert em_tracking_vs_gross_index_bps(mxfs_5y_annualised()) < 0
    assert em_tracking_vs_gross_index_bps(IEMA_5Y_ANNUALISED) < 0
    assert em_tracking_vs_gross_index_bps(mxfs_5y_annualised()) < (
        em_tracking_vs_gross_index_bps(IEMA_5Y_ANNUALISED)
    )
    assert EM_INDEX_GROSS_5Y_ANNUALISED > EM_INDEX_NET_5Y_ANNUALISED


def test_em_counterparty_cap_and_gl4_stop() -> None:
    assert UCITS_OTC_COUNTERPARTY_CAP == COUNTERPARTY_CAP_NAV
    assert SYNTHETIC_ADVANTAGE_HURDLE_BPS == pytest.approx(10.0)
    assert COUNTERPARTY_CAP_NAV == pytest.approx(0.10)
    assert len(MXFS_COUNTERPARTIES) >= 2
    assert MXFS_MAX_COUNTERPARTY_MTM_NAV <= COUNTERPARTY_CAP_NAV
    assert MXFS_COUNTERPARTY_EXPOSURE_WITHIN_CAP
    assert w2_passes()
    assert not gl4_passes()
    assert synthetic_non_us_leg_weight() == pytest.approx(0.0)
    assert synthetic_us_leg_weight() == pytest.approx(0.50)
