# Naive IST stamps, matching G0 / NSE broadcasts.
# ruff: noqa: DTZ001
import datetime as dt

import polars as pl
import pytest

from src.events.g1 import (
    AUTHORITY,
    COMPANION_NEAR,
    build_g1_events,
    count_complete_hold,
    evaluate_trades,
    measure_hold,
    render_charter,
)
from src.events.g2 import net_of_delivery_and_stcg, with_net
from src.events.g3 import gap_threshold_bps, split_by_gap
from src.events.paths import G1_CHARTER_PATH, G2_CHARTER_PATH, G3_CHARTER_PATH


def _sessions() -> list[dt.date]:
    return [
        dt.date(2020, 1, 2),
        dt.date(2020, 1, 3),
        dt.date(2020, 1, 6),
        dt.date(2020, 1, 7),
        dt.date(2020, 1, 8),
        dt.date(2020, 1, 9),
    ]


def _panel() -> pl.DataFrame:
    dates = _sessions()
    # Name beats Nifty by +200 bps each session (close-to-close).
    closes = [100.0, 103.0, 106.09, 109.27, 112.55, 115.93]
    nifty = [200.0, 202.0, 204.02, 206.06, 208.12, 210.20]
    opens = [100.0, 101.0, 104.0, 107.0, 110.0, 113.0]
    nifty_open = [200.0, 201.0, 203.0, 205.0, 207.0, 209.0]
    return pl.DataFrame(
        {
            "symbol": ["FOO.NS"] * len(dates),
            "date": dates,
            "open": opens,
            "close": closes,
            "nifty_close": nifty,
        }
    ), pl.DataFrame(
        {"date": dates, "open": nifty_open, "close": nifty}
    )


def test_charter_template_is_written_before_peek_language() -> None:
    text = render_charter(100)
    assert "Written **before** the residual peek" in text
    assert "Skip overnight-repriced names is **G3**" in text
    assert "T close → T+3 close" in text


def test_after_hours_filing_enters_next_session() -> None:
    panel, nifty = _panel()
    filings = pl.DataFrame(
        {
            "symbol": ["FOO.NS"],
            "period_end": [dt.date(2019, 12, 31)],
            "event_at": [dt.datetime(2020, 1, 2, 18, 0)],
        }
    )
    events = build_g1_events(filings, panel, nifty, _sessions())
    assert events.height == 1
    assert events["entry_date"][0] == dt.date(2020, 1, 3)


def test_side_follows_announcement_residual_not_the_hold() -> None:
    panel, nifty = _panel()
    filings = pl.DataFrame(
        {
            "symbol": ["FOO.NS"],
            "period_end": [dt.date(2019, 12, 31)],
            "event_at": [dt.datetime(2020, 1, 2, 18, 0)],
        }
    )
    events = build_g1_events(filings, panel, nifty, _sessions())
    assert events["side"][0] == 1.0
    held = measure_hold(events, panel, nifty, _sessions(), AUTHORITY)
    assert held.height == 1
    assert held["trade_residual_bps"][0] == pytest.approx(held["residual_bps"][0])


def test_count_complete_does_not_require_the_hold_residual() -> None:
    panel, nifty = _panel()
    filings = pl.DataFrame(
        {
            "symbol": ["FOO.NS"],
            "period_end": [dt.date(2019, 12, 31)],
            "event_at": [dt.datetime(2020, 1, 2, 18, 0)],
        }
    )
    events = build_g1_events(filings, panel, nifty, _sessions())
    assert count_complete_hold(events, panel, nifty, _sessions(), AUTHORITY) == 1
    assert count_complete_hold(events, panel, nifty, _sessions(), COMPANION_NEAR) == 1


def test_evaluate_trades_prints_n() -> None:
    panel, nifty = _panel()
    filings = pl.DataFrame(
        {
            "symbol": ["FOO.NS"],
            "period_end": [dt.date(2019, 12, 31)],
            "event_at": [dt.datetime(2020, 1, 2, 18, 0)],
        }
    )
    events = build_g1_events(filings, panel, nifty, _sessions())
    held = measure_hold(events, panel, nifty, _sessions(), AUTHORITY)
    result = evaluate_trades(held)
    assert result["n"] == 1
    assert result["point_bps"] == pytest.approx(held["trade_residual_bps"][0])


def test_net_identity_is_point_seven_nine_two_times_gross_minus_45() -> None:
    assert net_of_delivery_and_stcg(145.0) == pytest.approx(79.2)


def test_with_net_clips_gross_then_haircuts() -> None:
    frame = pl.DataFrame(
        {
            "trade_residual_bps": [-800.0, 145.0],
            "entry_date": [dt.date(2020, 1, 3), dt.date(2020, 1, 6)],
            "year": [2020, 2020],
            "era": ["late", "late"],
        }
    )
    out = with_net(frame)
    assert out["trade_clipped_bps"][0] == pytest.approx(-500.0)
    assert out["net_bps"][1] == pytest.approx(79.2)


def test_gap_split_keeps_at_or_below_median() -> None:
    frame = pl.DataFrame(
        {
            "overnight_residual_bps": [-10.0, 20.0, 40.0, None],
            "trade_residual_bps": [1.0, 2.0, 3.0, 4.0],
        }
    )
    threshold = gap_threshold_bps(frame.filter(pl.col("overnight_residual_bps").is_not_null()))
    small, large, dropped = split_by_gap(frame, threshold)
    assert dropped == 1
    assert small.height + large.height == 3
    assert small.height >= 1
    assert large.height >= 1


def test_g1_charter_path_is_in_docs_next() -> None:
    assert G1_CHARTER_PATH.name == "g1-charter.md"


def test_charters_were_written_before_the_peek() -> None:
    g1 = G1_CHARTER_PATH.read_text(encoding="utf-8")
    g2 = G2_CHARTER_PATH.read_text(encoding="utf-8")
    g3 = G3_CHARTER_PATH.read_text(encoding="utf-8")
    assert "Written **before** the residual peek" in g1
    assert "Skip overnight-repriced names is **G3**" in g1
    assert "Written **before** the G1 residual peek" in g2
    assert "net = 0.792 × (gross − 45)" in g2
    assert "Written **before** the G1 residual peek" in g3
    assert "50th" in g3
