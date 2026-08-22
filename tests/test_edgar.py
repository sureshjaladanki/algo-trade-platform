"""EDGAR Item 2.02, Form 25/15, and display-name tickers."""

from datetime import date
from pathlib import Path

from src.edgar import (
    delisting_filings,
    is_delisting_form,
    parse_efts_hit,
    parse_items_from_sgml,
    parse_master_idx_file,
    quarter_windows,
    ticker_from_display_name,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_form_25_and_15_are_delisting_forms() -> None:
    assert is_delisting_form("25")
    assert is_delisting_form("25-NSE")
    assert is_delisting_form("15-12B")
    assert is_delisting_form("15-12G")
    assert not is_delisting_form("15-15D")
    assert not is_delisting_form("8-K")


def test_parse_items_from_sgml() -> None:
    text = "<ITEMS>2.02\n<ITEMS>9.01\n"
    assert parse_items_from_sgml(text) == ["2.02", "9.01"]


def test_ticker_from_display_name() -> None:
    assert ticker_from_display_name("Apple Inc. (AAPL) (CIK 0000320193)") == "AAPL"
    assert (
        ticker_from_display_name(
            "California Resources Corp (CRC, CRCQW) (CIK 0001609253)"
        )
        == "CRC"
    )
    assert ticker_from_display_name("No ticker here") is None


def test_parse_efts_hit_keeps_item_202_8k() -> None:
    raw = {
        "_source": {
            "ciks": ["0000320193"],
            "display_names": ["Apple Inc. (AAPL) (CIK 0000320193)"],
            "form": "8-K",
            "adsh": "0000320193-24-000001",
            "file_date": "2024-02-01",
            "items": ["2.02", "9.01"],
        }
    }
    hit = parse_efts_hit(raw)
    assert hit is not None
    assert hit.ticker == "AAPL"
    assert hit.cik == "320193"
    assert hit.accession == "0000320193-24-000001"
    filing = hit.as_filing()
    assert filing.form == "8-K"
    assert filing.filed_date == date(2024, 2, 1)


def test_parse_efts_hit_drops_amendments_and_other_items() -> None:
    amendment = {
        "_source": {
            "ciks": ["0000320193"],
            "display_names": ["Apple Inc. (AAPL) (CIK 0000320193)"],
            "form": "8-K/A",
            "adsh": "0000320193-24-000002",
            "file_date": "2024-02-02",
            "items": ["2.02"],
        }
    }
    other = {
        "_source": {
            "ciks": ["0000320193"],
            "display_names": ["Apple Inc. (AAPL) (CIK 0000320193)"],
            "form": "8-K",
            "adsh": "0000320193-24-000003",
            "file_date": "2024-02-03",
            "items": ["5.02"],
        }
    }
    assert parse_efts_hit(amendment) is None
    assert parse_efts_hit(other) is None


def test_quarter_windows_cover_range() -> None:
    windows = quarter_windows(date(2010, 1, 1), date(2010, 12, 31))
    assert len(windows) == 4
    assert windows[0] == (date(2010, 1, 1), date(2010, 3, 31))
    assert windows[-1] == (date(2010, 10, 1), date(2010, 12, 31))


def test_delisting_filings_from_master_fixture() -> None:
    filings = parse_master_idx_file(FIXTURES / "master_delist.idx")
    gone = delisting_filings(filings)
    forms = {f.form for f in gone}
    assert forms == {"25", "15-12B"}
    assert {f.cik for f in gone} == {"100", "200"}
