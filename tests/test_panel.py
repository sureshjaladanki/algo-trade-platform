"""U0: PIT membership, corporate actions, leakage, EDGAR index, liquidity buckets."""

from datetime import date
from pathlib import Path

import polars as pl
import pytest

from src.edgar import parse_master_idx_file
from src.panel import (
    LeakageError,
    apply_split,
    assert_no_leakage,
    leakage_rows,
    load_csv,
    membership_asof,
    require_sane_final_prices,
    special_dividend_price_factor,
    split_price_factor,
    with_liquidity_bucket,
)
from src.universe import LiquidityBucket, liquidity_bucket

FIXTURES = Path(__file__).parent / "fixtures"


def test_six_known_corporate_actions() -> None:
    splits = {
        "AAPL_2020-08-31": 4.0,
        "TSLA_2020-08-31": 5.0,
        "AMZN_2022-06-06": 20.0,
    }
    assert split_price_factor(splits["AAPL_2020-08-31"]) == 0.25
    assert split_price_factor(splits["TSLA_2020-08-31"]) == 0.20
    assert split_price_factor(splits["AMZN_2022-06-06"]) == 0.05
    # Specials: COST $7 (2017-05-11), $15 (2020-12-01), $15 (2023-12-26)
    assert special_dividend_price_factor(close_cum_div=175.0, amount=7.0) == pytest.approx(168.0 / 175.0)
    assert special_dividend_price_factor(close_cum_div=390.0, amount=15.0) == pytest.approx(375.0 / 390.0)
    assert special_dividend_price_factor(close_cum_div=660.0, amount=15.0) == pytest.approx(645.0 / 660.0)
    prices = pl.DataFrame({"symbol": ["AAPL"], "close": [400.0], "volume": [10_000_000]})
    adjusted = apply_split(prices, ratio=4.0)
    assert adjusted["close"][0] == pytest.approx(100.0)
    assert adjusted["volume"][0] == pytest.approx(40_000_000)


def test_membership_round_trip_and_delisted_present() -> None:
    panel = load_csv(FIXTURES / "pit_membership.csv")
    asof = date(2020, 1, 2)
    snap = membership_asof(panel, asof)
    names = set(snap["symbol"].to_list())
    assert names == {"AAPL", "MSFT", "SIVB", "VTI"}
    assert "ABNB" not in names
    round_tripped = pl.read_csv(snap.write_csv().encode(), try_parse_dates=True)
    assert round_tripped.sort("symbol").equals(snap.sort("symbol"))
    sivb = panel.filter(pl.col("symbol") == "SIVB")
    assert sivb["end_date"][0] == date(2023, 3, 10)


def test_delisted_final_price_is_sane() -> None:
    prices = load_csv(FIXTURES / "pit_prices.csv")
    require_sane_final_prices(prices)
    sivb = prices.filter(pl.col("symbol") == "SIVB")
    assert sivb["close"][0] > 0


def test_leakage_test_catches_future_source_timestamp() -> None:
    clean = load_csv(FIXTURES / "pit_prices.csv")
    assert_no_leakage(clean)
    leaked = clean.with_columns(pl.col("source_timestamp") + pl.duration(days=1))
    with pytest.raises(LeakageError):
        assert_no_leakage(leaked)
    labeled = clean.with_columns(pl.lit(date(2020, 2, 1)).alias("label_fwd_20d"))
    assert leakage_rows(labeled).height == 0
    assert_no_leakage(labeled)


def test_liquidity_buckets() -> None:
    assert liquidity_bucket(1e9, symbol="VTI") is LiquidityBucket.LIQUID_ETF
    assert liquidity_bucket(150_000_000) is LiquidityBucket.LARGE_CAP
    assert liquidity_bucket(40_000_000) is LiquidityBucket.MID_CAP
    assert liquidity_bucket(5_000_000) is LiquidityBucket.SMALL_CAP
    assert liquidity_bucket(500_000) is LiquidityBucket.MICRO_CLOSED
    prices = with_liquidity_bucket(load_csv(FIXTURES / "pit_prices.csv"))
    by_symbol = dict(zip(prices["symbol"], prices["liquidity_bucket"], strict=True))
    assert by_symbol["VTI"] == "liquid_etf"
    assert by_symbol["MID1"] == "mid_cap"


def test_edgar_index_keyed_by_accession() -> None:
    filings = parse_master_idx_file(FIXTURES / "master.idx")
    assert len(filings) == 2
    apple = next(f for f in filings if f.form == "8-K")
    assert apple.accession == "0000320193-24-000001"
    assert apple.filed_date == date(2024, 2, 1)
    assert apple.filed_at.hour == 23
    by_accession = {f.accession: f for f in filings}
    assert "0001193125-24-000002" in by_accession
