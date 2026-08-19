import datetime as dt
from pathlib import Path

import polars as pl
import pytest

from src.events.benchmark import build_after_tax_passive
from src.events.constants import LTCG_RATE
from src.events.daily_panel import (
    CorporateActionError,
    assert_no_unadjusted_splits,
    build_daily_panel,
    drop_isolated_price_glitches,
)


def _write_minute_csv(
    path: Path,
    rows: list[tuple[str, float, float, float, float, int]],
) -> None:
    path.write_text(
        "date,open,high,low,close,volume\n"
        + "\n".join(
            f"{d},{o},{h},{low},{c},{v}" for d, o, h, low, c, v in rows
        )
        + "\n",
        encoding="utf-8",
    )


def _session(
    day: str, close: float, *, last_hour: int = 15, last_min: int = 29
) -> list[tuple[str, float, float, float, float, int]]:
    return [
        (f"{day} 09:15:00", close, close, close, close, 10),
        (f"{day} {last_hour:02d}:{last_min:02d}:00", close, close, close, close, 10),
    ]


def test_build_daily_panel_joins_nifty_and_membership(tmp_path: Path) -> None:
    _write_minute_csv(
        tmp_path / "^NSEI.csv",
        _session("2020-03-18", 100.0) + _session("2020-03-19", 101.0),
    )
    _write_minute_csv(
        tmp_path / "SHREECEM.NS.csv",
        _session("2020-03-18", 10.0) + _session("2020-03-19", 11.0),
    )
    panel = build_daily_panel(tmp_path)
    assert panel.columns == [
        "symbol",
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "is_nifty50_member",
        "nifty_close",
    ]
    row = panel.filter(pl.col("date") == dt.date(2020, 3, 19)).row(0, named=True)
    assert row["nifty_close"] == 101.0
    assert row["is_nifty50_member"] is True
    assert row["close"] == 11.0


def test_zero_placeholder_bar_is_dropped_not_interpolated(tmp_path: Path) -> None:
    _write_minute_csv(
        tmp_path / "^NSEI.csv",
        [
            ("2020-03-18 09:15:00", 0.0, 0.0, 0.0, 0.0, 0),
            ("2020-03-18 09:16:00", 100.0, 100.0, 100.0, 100.0, 10),
            ("2020-03-18 15:29:00", 101.0, 101.0, 101.0, 101.0, 10),
        ],
    )
    _write_minute_csv(
        tmp_path / "RELIANCE.NS.csv",
        [
            ("2020-03-18 09:15:00", 0.0, 0.0, 0.0, 0.0, 0),
            ("2020-03-18 09:16:00", 10.0, 10.0, 10.0, 10.0, 10),
            ("2020-03-18 15:29:00", 11.0, 11.0, 11.0, 11.0, 10),
        ],
    )
    panel = build_daily_panel(tmp_path)
    row = panel.row(0, named=True)
    assert row["open"] == 10.0
    assert row["close"] == 11.0
    assert row["nifty_close"] == 101.0


def test_trailing_incomplete_session_is_dropped(tmp_path: Path) -> None:
    _write_minute_csv(
        tmp_path / "^NSEI.csv",
        _session("2020-03-18", 100.0)
        + _session("2020-03-19", 101.0, last_hour=13, last_min=20),
    )
    _write_minute_csv(
        tmp_path / "RELIANCE.NS.csv",
        _session("2020-03-18", 10.0)
        + _session("2020-03-19", 11.0, last_hour=13, last_min=20),
    )
    panel = build_daily_panel(tmp_path)
    assert panel["date"].to_list() == [dt.date(2020, 3, 18)]


def test_isolated_split_glitch_is_dropped() -> None:
    panel = pl.DataFrame(
        {
            "symbol": ["FOO.NS"] * 3,
            "date": [dt.date(2020, 1, 1), dt.date(2020, 1, 2), dt.date(2020, 1, 3)],
            "open": [100.0, 200.0, 100.0],
            "close": [100.0, 200.0, 100.0],
        }
    )
    out = drop_isolated_price_glitches(panel)
    assert out["close"].to_list() == [100.0, 100.0]
    assert_no_unadjusted_splits(out)


def test_intraday_split_print_is_dropped() -> None:
    panel = pl.DataFrame(
        {
            "symbol": ["FOO.NS"] * 2,
            "date": [dt.date(2020, 1, 1), dt.date(2020, 1, 2)],
            "open": [100.0, 100.0],
            "close": [100.0, 400.0],
        }
    )
    out = drop_isolated_price_glitches(panel)
    assert out["close"].to_list() == [100.0]


def test_unadjusted_split_fails_loudly() -> None:
    panel = pl.DataFrame(
        {
            "symbol": ["FOO.NS", "FOO.NS"],
            "date": [dt.date(2020, 1, 1), dt.date(2020, 1, 2)],
            "close": [100.0, 50.0],
        }
    )
    with pytest.raises(CorporateActionError, match="split"):
        assert_no_unadjusted_splits(panel)


def test_after_tax_passive_applies_ltcg_on_gains_only() -> None:
    nifty = pl.DataFrame(
        {
            "date": [dt.date(2020, 1, 1), dt.date(2020, 1, 2), dt.date(2020, 1, 3)],
            "close": [100.0, 80.0, 200.0],
        }
    )
    series = build_after_tax_passive(nifty)
    assert series["gross_wealth"].to_list() == [1.0, 0.8, 2.0]
    assert series["after_tax_wealth"][1] == 0.8
    assert series["after_tax_wealth"][2] == pytest.approx(1.0 + (1.0 - LTCG_RATE) * 1.0)
