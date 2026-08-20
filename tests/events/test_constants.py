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


def test_g1_locks() -> None:
    from src.events.constants import (
        G1_AUTHORITY_SESSIONS,
        G1_FAR_SESSIONS,
        G1_NEAR_SESSIONS,
        G3_GAP_PERCENTILE,
        NSE_EQUITY_CLOSE,
    )

    assert G1_AUTHORITY_SESSIONS == 3
    assert G1_NEAR_SESSIONS == 1
    assert G1_FAR_SESSIONS == 5
    assert NSE_EQUITY_CLOSE.hour == 15 and NSE_EQUITY_CLOSE.minute == 30
    assert G3_GAP_PERCENTILE == 50.0


def test_f3r_locks() -> None:
    from src.events.constants import (
        F3R_CONTROL_RANK_HI,
        F3R_CONTROL_RANK_LO,
        F3R_GO_BPS,
        F3R_K,
        F3R_PRIOR_SIGMA_BPS,
        F3R_STOP_BPS,
    )

    assert F3R_K == 3
    assert F3R_CONTROL_RANK_LO == 21
    assert F3R_CONTROL_RANK_HI == 50
    assert F3R_PRIOR_SIGMA_BPS == 750.0
    assert F3R_GO_BPS == 450.0
    assert F3R_STOP_BPS == 300.0
