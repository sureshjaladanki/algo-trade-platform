"""W2 synthetic vs physical, locked to 31 Jul 2026 factsheets."""

import pytest

from src.books.synthetic import (
    COUNTERPARTY_CAP_NAV,
    CSPX_5Y_ANNUALISED,
    INDEX_GROSS_5Y_ANNUALISED,
    INDEX_NET_5Y_ANNUALISED,
    SPXS_COUNTERPARTIES,
    SYNTHETIC_ADVANTAGE_HURDLE_BPS,
    UCITS_OTC_COUNTERPARTY_CAP,
    advantage_vs_physical_bps,
    annualise_cumulative,
    spxs_5y_annualised,
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
