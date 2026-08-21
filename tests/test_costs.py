"""costs unit tests against Blueprint §0.2 and hand-worked fee arithmetic."""

import pytest

from src.costs import (
    EQUITY_CALIBRATION_TOLERANCE_BPS,
    OPTION_CALIBRATION_TOLERANCE_PCT,
    WORKING_TABLE,
    BorrowProhibited,
    Fill,
    ProductBucket,
    borrow_rate_annual,
    calibrate_fills,
    equity_sell_fees_bps,
    equity_sell_fees_usd,
    finra_taf,
    futures_round_turn_bps,
    futures_round_turn_usd,
    occ_fee,
    option_fees_round_trip_usd,
    round_trip,
    round_trip_bps,
    round_trip_pct_of_premium,
    section_31_fee,
    working_all_in,
)


def test_section_31_on_fifty_thousand_proceeds() -> None:
    assert section_31_fee(50_000.0) == pytest.approx(1.39)


def test_finra_taf_uncapped_and_capped() -> None:
    assert finra_taf(1_000.0) == pytest.approx(0.166)
    assert finra_taf(100_000.0) == pytest.approx(8.30)


def test_equity_sell_fees_at_spy_size() -> None:
    fees = equity_sell_fees_usd(shares=1_000.0, sell_price=50.0)
    assert fees == pytest.approx(1.39 + 0.166)
    bps = equity_sell_fees_bps(shares=1_000.0, sell_price=50.0)
    assert 0.2 < bps < 0.6


def test_occ_and_spx_round_trip_fees_near_table() -> None:
    assert occ_fee(10) == pytest.approx(0.20)
    # 1 contract both sides: ~$1.50 working in the blueprint
    assert 1.20 < option_fees_round_trip_usd(1) < 1.80


def test_futures_all_in_inside_blueprint_range() -> None:
    mes = futures_round_turn_bps(ProductBucket.MES)
    es = futures_round_turn_bps(ProductBucket.ES)
    assert 0.6 <= mes <= 0.9
    assert 0.5 <= es <= 0.7
    assert futures_round_turn_usd(ProductBucket.MES) == pytest.approx(2.45)
    assert futures_round_turn_usd(ProductBucket.ES) == pytest.approx(17.0)


def test_working_all_in_inside_blueprint_range() -> None:
    for bucket, spec in WORKING_TABLE.items():
        modelled = round_trip(bucket)
        assert spec.all_in_low <= modelled.value <= spec.all_in_high
        assert modelled.unit is spec.unit


def test_equity_and_option_accessors() -> None:
    assert round_trip_bps(ProductBucket.LIQUID_ETF) == pytest.approx(working_all_in(ProductBucket.LIQUID_ETF))
    assert round_trip_pct_of_premium(ProductBucket.SPX_ATM_30_45) == pytest.approx(1.5)
    with pytest.raises(ValueError):
        round_trip_bps(ProductBucket.SPX_ATM_30_45)
    with pytest.raises(ValueError):
        round_trip_pct_of_premium(ProductBucket.LIQUID_ETF)


def test_borrow_is_prohibited() -> None:
    with pytest.raises(BorrowProhibited):
        borrow_rate_annual("AAPL")


def _fill(
    fill_id: str,
    bucket: ProductBucket,
    *,
    mid: float,
    price: float,
    kind: str,
    premium: float | None = None,
) -> Fill:
    return Fill(
        fill_id=fill_id,
        symbol="TEST",
        bucket=bucket,
        side="buy",
        quantity=100,
        price=price,
        nbbo_mid=mid,
        product_kind=kind,  # type: ignore[arg-type]
        premium=premium,
    )


def test_calibration_passes_when_fills_match_model() -> None:
    spy_rt = round_trip_bps(ProductBucket.LIQUID_ETF)
    half = spy_rt / 2.0 / 1e4
    spy_fills = [
        _fill(f"e{i}", ProductBucket.LIQUID_ETF, mid=500.0, price=500.0 * (1 + half), kind="equity")
        for i in range(100)
    ]
    prem = 20.0
    opt_rt = round_trip_pct_of_premium(ProductBucket.SPX_ATM_30_45)
    one_way = opt_rt / 2.0 / 100.0 * prem
    opt_fills = [
        _fill(
            f"o{i}",
            ProductBucket.SPX_ATM_30_45,
            mid=20.0,
            price=20.0 + one_way,
            kind="option",
            premium=prem,
        )
        for i in range(100)
    ]
    report = calibrate_fills(spy_fills + opt_fills)
    assert report.n_fills == 200
    assert report.passed
    assert abs(report.equity_error_bps or 0.0) <= EQUITY_CALIBRATION_TOLERANCE_BPS
    assert abs(report.option_error_pct_of_premium or 0.0) <= OPTION_CALIBRATION_TOLERANCE_PCT


def test_calibration_fails_when_equity_slippage_exceeds_3bps() -> None:
    fills = [
        _fill("e0", ProductBucket.LIQUID_ETF, mid=100.0, price=100.10, kind="equity")
        for _ in range(10)
    ]
    report = calibrate_fills(fills)
    assert not report.equity_within_tolerance
    assert not report.passed
