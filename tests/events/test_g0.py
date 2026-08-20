# Naive IST stamps, matching src.events.g0.
# ruff: noqa: DTZ001
import datetime as dt
import json

import polars as pl

from src.events.g0 import (
    first_broadcast,
    g0_verdict,
    half_year_windows,
    parse_nse_datetime,
    parse_results_json,
)
from src.events.paths import G0_CHARTER_PATH


def test_charter_is_written_before_the_hunt() -> None:
    text = G0_CHARTER_PATH.read_text(encoding="utf-8")
    assert "Written **before** the calendar hunt" in text
    assert "No vendor" in text
    assert "100-name" in text


def test_half_year_windows_cover_the_panel_span() -> None:
    windows = half_year_windows(dt.date(2015, 1, 1), dt.date(2016, 4, 30))
    assert windows[0] == (dt.date(2015, 1, 1), dt.date(2015, 6, 30))
    assert windows[-1] == (dt.date(2016, 1, 1), dt.date(2016, 4, 30))
    assert len(windows) == 3


def test_parse_nse_datetime_accepts_exchange_stamp() -> None:
    assert parse_nse_datetime("17-Jun-2025 22:41:02") == dt.datetime(
        2025, 6, 17, 22, 41, 2
    )
    assert parse_nse_datetime("17-Jun-2025 22:40") == dt.datetime(2025, 6, 17, 22, 40)
    assert parse_nse_datetime(None) is None


def test_parse_results_maps_renames_and_skips_blank_broadcast() -> None:
    blob = json.dumps(
        [
            {
                "symbol": "ZOMATO",
                "companyName": "Eternal Limited",
                "period": "Quarterly",
                "fromDate": "01-Jan-2025",
                "toDate": "31-Mar-2025",
                "broadCastDate": "18-Apr-2025 18:01:00",
                "exchdisstime": "18-Apr-2025 18:01:30",
                "consolidated": "Consolidated",
                "audited": "Un-Audited",
                "xbrl": "https://nsearchives.nseindia.com/xbrl/example.xml",
            },
            {
                "symbol": "SKIPME",
                "companyName": "No stamp",
                "period": "Quarterly",
                "fromDate": "01-Jan-2025",
                "toDate": "31-Mar-2025",
                "broadCastDate": None,
                "exchdisstime": None,
                "consolidated": "Consolidated",
                "audited": "Un-Audited",
                "xbrl": None,
            },
        ]
    ).encode("utf-8")
    frame = parse_results_json(blob)
    assert frame.height == 1
    assert frame["symbol"][0] == "ETERNAL.NS"
    assert frame["broadcast_at"][0] == dt.datetime(2025, 4, 18, 18, 1, 0)


def test_first_broadcast_keeps_earliest_per_period() -> None:
    frame = pl.DataFrame(
        {
            "symbol": ["FOO.NS", "FOO.NS", "FOO.NS"],
            "period_end": [
                dt.date(2024, 3, 31),
                dt.date(2024, 3, 31),
                dt.date(2024, 6, 30),
            ],
            "broadcast_at": [
                dt.datetime(2024, 4, 20, 16, 0),
                dt.datetime(2024, 4, 20, 21, 0),
                dt.datetime(2024, 7, 20, 16, 0),
            ],
            "exchange_dissem_at": [
                dt.datetime(2024, 4, 20, 16, 1),
                dt.datetime(2024, 4, 20, 21, 1),
                None,
            ],
        }
    )
    out = first_broadcast(frame)
    assert out.height == 2
    first = out.filter(pl.col("period_end") == dt.date(2024, 3, 31))
    assert first["event_at"][0] == dt.datetime(2024, 4, 20, 16, 1)


def test_g0_verdict_defers_a_thin_calendar() -> None:
    assert g0_verdict(400, 80, 100) == "PASS"
    assert g0_verdict(20, 10, 100) == "DEFER"
