"""OptionsDX monthly EOD parser. A1 tape."""

from datetime import date
from pathlib import Path

from src.optionsdx import (
    load_put_panel,
    puts_from_panel,
    puts_on_date,
    quotes_from_frame,
    read_month_file,
    summarize_chain,
)

FIXTURE = Path(__file__).parent / "fixtures" / "optionsdx_spx_eod_sample.txt"


def test_read_month_file_strips_brackets_and_casts() -> None:
    frame = read_month_file(FIXTURE)
    assert frame.height == 2
    assert frame["quote_date"].dtype == frame["expire_date"].dtype
    assert frame["p_bid"].dtype == frame["strike"].dtype
    row = frame.row(0, named=True)
    assert row["quote_date"] == date(2012, 1, 18)
    assert row["expire_date"] == date(2012, 2, 17)
    assert row["underlying_last"] == 1308.04
    assert row["p_bid"] == 6.8
    assert row["p_ask"] == 7.2
    assert row["p_delta"] == -0.225
    assert row["dte"] == 30.0


def test_quotes_drop_zero_bid_puts() -> None:
    frame = read_month_file(FIXTURE)
    quotes = quotes_from_frame(frame)
    puts = [quote for quote in quotes if quote.right == "P"]
    calls = [quote for quote in quotes if quote.right == "C"]
    assert len(puts) == 1
    assert puts[0].strike == 1250.0
    assert puts[0].bid == 6.8
    assert puts[0].ask == 7.2
    assert len(calls) == 2


def test_puts_on_date_and_summary() -> None:
    frame = read_month_file(FIXTURE)
    puts = puts_on_date(frame, expiry=date(2012, 2, 17), trade_date=date(2012, 1, 18))
    assert len(puts) == 1
    summary = summarize_chain(frame)
    assert summary["n_rows"] == 2
    assert summary["valid_puts"] == 1
    assert summary["puts_30_45_dte"] == 1
    assert summary["puts_20_25_delta"] == 1
    assert summary["first_quote"] == date(2012, 1, 18)


def test_slim_panel_keeps_valid_30dte_put() -> None:
    panel = load_put_panel(FIXTURE.parent, cache=None)
    puts = puts_from_panel(
        panel, expiry=date(2012, 2, 17), trade_date=date(2012, 1, 18)
    )
    assert len(puts) == 1
    assert puts[0].strike == 1250.0
    assert puts[0].bid == 6.8
