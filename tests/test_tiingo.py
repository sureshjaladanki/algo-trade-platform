"""Tiingo $0 coverage of Yahoo-missing S&P 400 names. Not B1."""

from datetime import date

from src.tiingo import (
    CoverageHit,
    DIRTY_IDENTITY,
    SUCCESSOR_TICKERS,
    TickerRow,
    bars_from_eod,
    classify_row,
    dump_usable_eod,
    normalize_ticker,
    parse_supported_rows,
    pending_eod_symbols,
    price_on_disk,
    still_missing_prices,
    yahoo_missing_from_cache,
)


def test_normalize_and_parse_supported_rows() -> None:
    text = """ticker,exchange,assetType,priceCurrency,startDate,endDate
CELG,NASDAQ,Stock,USD,1990-03-26,2019-11-22
brk.b,NYSE,Stock,USD,1990-01-02,2026-08-21
"""
    rows = parse_supported_rows(text)
    assert normalize_ticker("brk.b") == "BRK-B"
    assert rows["CELG"].end == date(2019, 11, 22)
    assert rows["BRK-B"].exchange == "NYSE"


def test_classify_row_statuses() -> None:
    recovered = TickerRow("CELG", "NASDAQ", "Stock", date(1990, 3, 26), date(2019, 11, 22))
    otc = TickerRow("SBNY", "PINK", "Stock", date(2004, 3, 23), date(2026, 8, 21))
    stub = TickerRow("FOO", "PINK", "Stock", date(2024, 8, 15), date(2026, 8, 21))
    splice = TickerRow("CHK", "NASDAQ", "Stock", date(1993, 2, 16), date(2024, 10, 4))
    reuse = TickerRow("JAVA", "NYSE", "ETF", date(2021, 10, 5), date(2026, 8, 21))
    assert classify_row("CELG", recovered) == "recovered"
    assert classify_row("SBNY", otc) == "otc_history"
    assert classify_row("FOO", stub) == "stub"
    assert classify_row("CHK", splice) == "splice"
    assert classify_row("JAVA", reuse) == "reuse"
    assert classify_row("MISS", None) == "absent"


def test_bars_from_eod_use_adj_close() -> None:
    bars = bars_from_eod(
        [
            {
                "date": "2010-01-04",
                "close": 50.0,
                "adjClose": 10.0,
                "divCash": 0.25,
                "volume": 1000,
            }
        ]
    )
    assert len(bars) == 1
    assert bars[0].close == 10.0
    assert bars[0].dividend == 0.25
    assert bars[0].date == date(2010, 1, 4)


def test_yahoo_missing_from_cache(tmp_path, monkeypatch) -> None:
    from src import tiingo

    monkeypatch.setattr(tiingo, "yahoo_cache_path", lambda symbol: tmp_path / f"{symbol}.csv")
    (tmp_path / "AA.csv").write_text("date,close\n2010-01-04,1\n", encoding="utf-8")
    assert yahoo_missing_from_cache({"AA", "DEAD"}) == {"DEAD"}


def test_pending_eod_skips_cached(tmp_path) -> None:
    hits = (
        CoverageHit("CELG", "recovered", "NASDAQ", "Stock"),
        CoverageHit("ATVI", "recovered", "NASDAQ", "Stock"),
        CoverageHit("MISS", "absent", "", ""),
    )
    (tmp_path / "CELG.csv").write_text("date,close,dividend,volume\n", encoding="utf-8")
    assert pending_eod_symbols(hits, directory=tmp_path) == ["ATVI"]


def test_dump_usable_fetches_pending(tmp_path, monkeypatch) -> None:
    from src import tiingo
    from src.yahoo import DailyBar

    hits = [
        CoverageHit("CELG", "recovered", "NASDAQ", "Stock"),
        CoverageHit("ATVI", "recovered", "NASDAQ", "Stock"),
    ]
    (tmp_path / "CELG.csv").write_text(
        "date,close,dividend,volume\n2010-01-04,10,0,1\n", encoding="utf-8"
    )
    fetched: list[str] = []

    def fake_load(symbol: str, *, start=date(2010, 1, 1), directory=tmp_path):
        fetched.append(symbol)
        path = directory / f"{symbol}.csv"
        path.write_text("date,close,dividend,volume\n2010-01-04,11,0,1\n", encoding="utf-8")
        return [DailyBar(date=date(2010, 1, 4), close=11.0, volume=1.0)]

    monkeypatch.setattr(tiingo, "load_or_fetch_eod", fake_load)
    report = dump_usable_eod(hits, pause_sec=0.0, directory=tmp_path)
    assert fetched == ["ATVI"]
    assert report.n_usable == 2
    assert report.n_cached == 1
    assert report.n_fetched == 1
    assert report.n_failed == 0


def test_price_on_disk_yahoo_tiingo_and_successor(tmp_path, monkeypatch) -> None:
    from src import tiingo

    yahoo = tmp_path / "yahoo"
    tiingo_dir = tmp_path / "tiingo"
    yahoo.mkdir()
    tiingo_dir.mkdir()
    monkeypatch.setattr(tiingo, "yahoo_cache_path", lambda symbol, directory=yahoo: yahoo / f"{symbol}.csv")
    monkeypatch.setattr(tiingo, "eod_cache_path", lambda symbol, directory=tiingo_dir: tiingo_dir / f"{symbol}.csv")
    monkeypatch.setattr(tiingo, "SUCCESSOR_TICKERS", {"ASGN": "EFOR", "SIVB": "SIVBQ", "BXS": "CADE"})
    monkeypatch.setattr(tiingo, "DIRTY_IDENTITY", frozenset({"SIVB", "AHL"}))

    (yahoo / "EFOR.csv").write_text("date,close\n2010-01-04,1\n", encoding="utf-8")
    (tiingo_dir / "CADE.csv").write_text("date,close\n2010-01-04,1\n", encoding="utf-8")
    (tiingo_dir / "SIVBQ.csv").write_text("date,close\n2010-01-04,1\n", encoding="utf-8")
    (tiingo_dir / "AHL.csv").write_text("date,close\n2026-02-25,1\n", encoding="utf-8")

    assert price_on_disk("ASGN") is True
    assert price_on_disk("BXS") is True
    assert price_on_disk("SIVB") is False
    assert price_on_disk("AHL") is False
    assert still_missing_prices({"ASGN", "BXS", "SIVB", "DEAD"}) == {"SIVB", "DEAD"}
    assert SUCCESSOR_TICKERS["ENDP"] == "ENDPQ"
    assert "SIVB" in DIRTY_IDENTITY
