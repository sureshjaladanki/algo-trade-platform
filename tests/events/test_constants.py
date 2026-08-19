from src.events.constants import (
    DELIVERY_ROUND_TRIP,
    DELIVERY_ROUND_TRIP_BPS,
    DISASTER_CLIP_BPS,
    INDEX_FUTURES_ROUND_TRIP_HIGH_BPS,
    INDEX_FUTURES_ROUND_TRIP_LOW_BPS,
    LTCG_RATE,
    PRIOR_EVENT_SIGMA_BPS,
    STCG_RATE,
)


def test_delivery_round_trip_is_45_bps() -> None:
    assert DELIVERY_ROUND_TRIP_BPS == 45
    assert DELIVERY_ROUND_TRIP == 0.0045


def test_stcg_rate_is_20_point_8_percent() -> None:
    assert STCG_RATE == 0.208


def test_ltcg_rate_is_12_point_5_percent() -> None:
    assert LTCG_RATE == 0.125


def test_index_futures_reference_band_is_10_to_12_bps() -> None:
    assert INDEX_FUTURES_ROUND_TRIP_LOW_BPS == 10
    assert INDEX_FUTURES_ROUND_TRIP_HIGH_BPS == 12


def test_disaster_clip_is_500_bps() -> None:
    assert DISASTER_CLIP_BPS == 500


def test_prior_event_sigma_is_600_bps() -> None:
    assert PRIOR_EVENT_SIGMA_BPS == 600.0
