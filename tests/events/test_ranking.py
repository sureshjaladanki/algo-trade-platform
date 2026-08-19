import calendar
import datetime as dt
import io
import zipfile

import polars as pl

from src.events.f1b import naive_hit_probability, ranking_verdict, render_f1b_charter
from src.events.mcwb import parse_mcwb_csv, parse_mcwb_zip, to_ledger_symbol
from src.events.ranking import (
    average_free_float,
    cutoff_for_announcement,
    predict_additions,
    rank_next50,
    window_months,
)

_SAMPLE_CSV = """Annexure II- Nifty Next 50 Index : January 2018,,,
,,,
Sr. No,Security Symbol,Security Name,Free Float Market Capitalisation (Rs. Crores),Avg. Impact Cost (%)
1,ABB,ABB India Ltd.,8758.17,0.07
2,ZOMATO,Zomato Ltd.,12000.5,0.02
"""


def test_to_ledger_symbol_maps_renames() -> None:
    assert to_ledger_symbol("ABB") == "ABB.NS"
    assert to_ledger_symbol("ZOMATO") == "ETERNAL.NS"
    assert to_ledger_symbol("TATAMOTORS") == "TMPV.NS"


def test_parse_mcwb_csv_accepts_index_market_cap_header() -> None:
    text = """title,,,
,,,
Sr. No,Security Symbol,Security Name,Index Market Capitalisation (Rs. Crores),Avg. Impact Cost (%)
1,BEL,Bharat Electronics Ltd.,9000.0,0.02
"""
    frame = parse_mcwb_csv(text, "next_50", 2024, 8)
    assert frame["symbol"][0] == "BEL.NS"
    assert frame["ff_mcap_cr"][0] == 9000.0
    frame = parse_mcwb_csv(_SAMPLE_CSV, "next_50", 2018, 1)
    assert frame["as_of"][0] == dt.date(2018, 1, 31)
    assert "ETERNAL.NS" in frame["symbol"].to_list()
    assert frame.filter(pl.col("symbol") == "ABB.NS")["ff_mcap_cr"][0] == 8758.17


def test_parse_mcwb_zip_splits_families() -> None:
    fifty = _SAMPLE_CSV.replace("Next 50", "50").replace("ZOMATO", "RELIANCE").replace("ABB", "TCS")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("nifty50_mcwb.csv", fifty)
        zf.writestr("niftynext50_mcwb.csv", _SAMPLE_CSV)
    panel = parse_mcwb_zip(buf.getvalue(), 2018, 1)
    assert set(panel["family"].to_list()) == {"nifty_50", "next_50"}


def test_cutoff_and_window() -> None:
    assert cutoff_for_announcement(dt.date(2018, 2, 22)) == dt.date(2018, 1, 31)
    assert cutoff_for_announcement(dt.date(2024, 8, 23)) == dt.date(2024, 7, 31)
    assert window_months(dt.date(2018, 1, 31)) == [
        (2017, 8),
        (2017, 9),
        (2017, 10),
        (2017, 11),
        (2017, 12),
        (2018, 1),
    ]
    assert window_months(dt.date(2020, 7, 31))[0] == (2020, 2)
    assert window_months(dt.date(2020, 7, 31))[-1] == (2020, 7)


def _month_row(year: int, month: int, family: str, symbol: str, ff: float) -> dict:
    last = calendar.monthrange(year, month)[1]
    return {
        "year": year,
        "month": month,
        "as_of": dt.date(year, month, last),
        "family": family,
        "nse_symbol": symbol.replace(".NS", ""),
        "symbol": symbol,
        "ff_mcap_cr": ff,
        "impact_cost_pct": 0.10,
    }


def test_rank_and_buffer_on_synthetic_window() -> None:
    rows = []
    for month in range(2, 8):
        rows.append(_month_row(2020, month, "nifty_50", "SMALL.NS", 80.0))
        rows.append(_month_row(2020, month, "nifty_50", "BIG.NS", 200.0))
        rows.append(_month_row(2020, month, "next_50", "CAND.NS", 150.0))
        rows.append(_month_row(2020, month, "next_50", "MID.NS", 90.0))
        rows.append(_month_row(2020, month, "next_50", "LOW.NS", 40.0))
    panel = pl.DataFrame(rows)
    averaged = average_free_float(panel, dt.date(2020, 7, 31))
    ranked = rank_next50(averaged)
    assert ranked["symbol"].to_list() == ["CAND.NS", "MID.NS", "LOW.NS"]
    predicted = predict_additions(averaged)
    # 1.5 × 80 = 120, so only CAND (150) clears the buffer.
    assert predicted["symbol"].to_list() == ["CAND.NS"]


def test_charter_locks_naive_before_peek() -> None:
    text = render_f1b_charter(29, 0.04)
    assert "Written **before** the ranking peek" in text
    assert "0.0400" in text
    assert "wrong universe" in text


def test_ranking_verdict_inconclusive_when_mde_covers_lift() -> None:
    assert ranking_verdict(0.20, 0.05, 0.35, mde=0.20, naive=0.04) == "INCONCLUSIVE"
    assert ranking_verdict(0.50, 0.30, 0.70, mde=0.10, naive=0.04) == "PASS"
    assert ranking_verdict(0.02, 0.00, 0.03, mde=0.01, naive=0.10) == "FAIL"


def test_naive_probability_is_k_over_fifty() -> None:
    p = naive_hit_probability()
    assert 0.0 < p < 0.2
