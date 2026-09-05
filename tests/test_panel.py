"""U0 panel, universe, fetch discipline, and the four evidence tests."""

from __future__ import annotations

import zipfile
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import polars as pl
import pytest

from src.fetch import FetchBlackoutError, fetch_bytes, in_fetch_blackout, put_cached
from src.harness import date_shift_test
from src.panel import (
    attach_delivery_median,
    build_panel,
    close_method_month_counts,
    demerger_holding_gap,
    join_impact_cost,
    load_corporate_actions,
    load_impact_cost,
    parse_cm_bhavcopy,
)
from src.universe import (
    NIFTY_50,
    flags_as_of,
    load_flag_intervals,
    load_membership_events,
    load_snapshot,
    membership_as_of,
    tradable_symbols,
)

IST = ZoneInfo("Asia/Kolkata")
FIXTURES = Path(__file__).parent / "fixtures" / "u0"

UDIFF_HEADER = (
    "TradDt,BizDt,Sgmt,Src,FinInstrmTp,FinInstrmId,ISIN,TckrSymb,SctySrs,XpryDt,"
    "FininstrmActlXpryDt,StrkPric,OptnTp,FinInstrmNm,OpnPric,HghPric,LwPric,ClsPric,"
    "LastPric,PrvsClsgPric,UndrlygPric,SttlmPric,OpnIntrst,ChngInOpnIntrst,TtlTradgVol,"
    "TtlTrfVal,TtlNbOfTxsExctd,SsnId,NewBrdLotQty,Rmks,Rsvd1,Rsvd2,Rsvd3,Rsvd4"
)


def _udiff_row(session: date, symbol: str, isin: str, close: float, series: str = "EQ") -> str:
    d = session.isoformat()
    vol = 1000
    val = close * vol
    return (
        f"{d},{d},CM,NSE,STK,1,{isin},{symbol},{series},,,,,{symbol},"
        f"{close},{close},{close},{close},{close},{close},,{close},,,"
        f"{vol},{val},1,F1,1,,,,,"
    )


def _zip_udiff(session: date, rows: list[str]) -> bytes:
    body = UDIFF_HEADER + "\n" + "\n".join(rows) + "\n"
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(f"BhavCopy_NSE_CM_0_0_0_{session.strftime('%Y%m%d')}_F_0000.csv", body)
    return buf.getvalue()


def _seed_day(root: Path, session: date, rows: list[str]) -> None:
    key = f"nse-cm-udiff:{session.isoformat()}"
    if session < date(2024, 7, 8):
        key = f"nse-cm-legacy:{session.isoformat()}"
    put_cached(root, key, _zip_udiff(session, rows))


def _u0_root_panel(tmp_path: Path) -> tuple[pl.DataFrame, Path]:
    root = tmp_path
    days = {
        date(2012, 12, 31): [
            _udiff_row(date(2012, 12, 31), "STER", "INE268A01049", 2000.0),
            _udiff_row(date(2012, 12, 31), "RELIANCE", "INE002A01018", 800.0),
            _udiff_row(date(2012, 12, 31), "TCS", "INE467B01029", 1200.0),
        ],
        date(2013, 8, 26): [
            _udiff_row(date(2013, 8, 26), "STER", "INE268A01049", 90.3),
            _udiff_row(date(2013, 8, 26), "RELIANCE", "INE002A01018", 850.0),
            _udiff_row(date(2013, 8, 26), "TCS", "INE467B01029", 1250.0),
        ],
        date(2013, 8, 27): [
            _udiff_row(date(2013, 8, 27), "RELIANCE", "INE002A01018", 852.0),
            _udiff_row(date(2013, 8, 27), "TCS", "INE467B01029", 1260.0),
        ],
        date(2023, 7, 19): [
            _udiff_row(date(2023, 7, 19), "RELIANCE", "INE002A01018", 2796.0),
        ],
        date(2023, 7, 20): [
            _udiff_row(date(2023, 7, 20), "RELIANCE", "INE002A01018", 2534.15),
            _udiff_row(date(2023, 7, 20), "JIOFIN", "INE758E01017", 261.85),
        ],
        date(2026, 7, 31): [
            _udiff_row(date(2026, 7, 31), "RELIANCE", "INE002A01018", 1400.0),
            _udiff_row(date(2026, 7, 31), "SETCO", "INE676H01014", 12.0),
        ],
        date(2026, 8, 3): [
            _udiff_row(date(2026, 8, 3), "RELIANCE", "INE002A01018", 1410.0),
            _udiff_row(date(2026, 8, 3), "SETCO", "INE676H01014", 11.5),
        ],
        date(2026, 8, 4): [
            _udiff_row(date(2026, 8, 4), "RELIANCE", "INE002A01018", 1412.0),
            _udiff_row(date(2026, 8, 4), "SETCO", "INE676H01014", 11.4),
        ],
        date(2026, 5, 5): [
            _udiff_row(date(2026, 5, 5), "SETCO", "INE676H01014", 13.0),
            _udiff_row(date(2026, 5, 5), "RELIANCE", "INE002A01018", 1390.0),
        ],
        date(2026, 5, 6): [
            _udiff_row(date(2026, 5, 6), "SETCO", "INE676H01014", 12.8),
            _udiff_row(date(2026, 5, 6), "RELIANCE", "INE002A01018", 1395.0),
        ],
    }
    for session, rows in days.items():
        _seed_day(root, session, rows)
    actions = load_corporate_actions(FIXTURES / "corporate_actions.csv")
    impact = load_impact_cost(FIXTURES / "impact_cost.csv")
    fno = {
        date(2026, 7, 31): {"RELIANCE"},
        date(2026, 8, 3): {"RELIANCE"},
        date(2026, 8, 4): {"RELIANCE"},
    }
    panel = build_panel(
        sorted(days),
        root=root,
        actions=actions,
        impact=impact,
        fno_by_date=fno,
        allow_network=False,
    )
    return panel, root


def test_blackout_weekdays_only() -> None:
    monday = datetime(2026, 9, 7, 11, 0, tzinfo=IST)
    saturday = datetime(2026, 9, 5, 11, 0, tzinfo=IST)
    evening = datetime(2026, 9, 7, 16, 16, tzinfo=IST)
    assert in_fetch_blackout(monday)
    assert not in_fetch_blackout(saturday)
    assert not in_fetch_blackout(evening)


def test_blackout_blocks_network_but_not_cache(tmp_path: Path) -> None:
    monday = datetime(2026, 9, 7, 11, 0, tzinfo=IST)
    put_cached(tmp_path, "k", b"hello")
    hit = fetch_bytes("https://example.invalid", root=tmp_path, key="k", clock=monday)
    assert hit.payload == b"hello"
    with pytest.raises(FetchBlackoutError):
        fetch_bytes("https://example.invalid/missing", root=tmp_path, key="missing", clock=monday)


def test_parse_udiff_roundtrip() -> None:
    session = date(2024, 7, 8)
    payload = _zip_udiff(session, [_udiff_row(session, "RELIANCE", "INE002A01018", 100.0)])
    frame = parse_cm_bhavcopy(payload, session)
    assert frame.get_column("symbol").to_list() == ["RELIANCE"]
    assert frame.get_column("unadj_close").to_list() == [100.0]


def test_survivorship_sterlite(tmp_path: Path) -> None:
    panel, _ = _u0_root_panel(tmp_path)
    y2012 = panel.filter(pl.col("session_date") == date(2012, 12, 31))
    after = panel.filter(pl.col("session_date") == date(2013, 8, 27))
    assert "STER" in y2012.get_column("symbol").to_list()
    assert "STER" not in after.get_column("symbol").to_list()

    def ranks(frame: pl.DataFrame) -> dict[str, int]:
        ordered = frame.sort("unadj_close", descending=True).get_column("symbol").to_list()
        return {sym: i for i, sym in enumerate(ordered)}

    pit = ranks(y2012)
    survivors_only = ranks(y2012.filter(pl.col("symbol").is_in(after.get_column("symbol").to_list())))
    assert pit["RELIANCE"] != survivors_only["RELIANCE"]


def test_demerger_reliance_jiofin(tmp_path: Path) -> None:
    panel, _ = _u0_root_panel(tmp_path)
    gap = demerger_holding_gap(panel, "RELIANCE", "JIOFIN", date(2023, 7, 20))
    assert gap < 0.01
    post = panel.filter(
        (pl.col("session_date") == date(2023, 7, 20)) & (pl.col("symbol") == "JIOFIN")
    )
    assert post.get_column("isin").to_list() == ["INE758E01017"]
    pre = panel.filter(
        (pl.col("session_date") == date(2023, 7, 19)) & (pl.col("symbol") == "RELIANCE")
    )
    assert float(pre.get_column("adjustment_factor")[0]) == pytest.approx(0.9063483547925608)


def test_look_ahead_date_shift(tmp_path: Path) -> None:
    panel, _ = _u0_root_panel(tmp_path)
    ordered = panel.sort(["symbol", "session_date"])

    def lag(frame: pl.DataFrame) -> pl.Series:
        return (
            frame.sort(["symbol", "session_date"])
            .with_columns(pl.col("unadj_close").shift(1).over("symbol").alias("feat"))
            .get_column("feat")
        )

    date_shift_test(ordered, lag)

    future = {
        (r["session_date"], r["symbol"]): nxt
        for r, nxt in zip(
            ordered.iter_rows(named=True),
            ordered.with_columns(pl.col("unadj_close").shift(-1).over("symbol")).get_column(
                "unadj_close"
            ),
            strict=True,
        )
    }

    def leak(frame: pl.DataFrame) -> pl.Series:
        values = [future[(r["session_date"], r["symbol"])] for r in frame.iter_rows(named=True)]
        return pl.Series("feat", values)

    with pytest.raises(AssertionError, match="unchanged"):
        date_shift_test(ordered, leak)


def test_esm_stage_two_not_tradable() -> None:
    intervals = load_flag_intervals(FIXTURES / "flag_intervals.csv")
    names = {"SETCO", "RELIANCE"}
    assert "SETCO" in tradable_symbols(names, intervals, date(2026, 5, 5))
    assert "SETCO" not in tradable_symbols(names, intervals, date(2026, 5, 6))
    assert flags_as_of(intervals, "SETCO", date(2026, 5, 6))["esm_stage"] == 2
    assert flags_as_of(intervals, "SETCO", date(2026, 5, 6))["price_band_pct"] == 2


def test_close_method_cas_break(tmp_path: Path) -> None:
    panel, _ = _u0_root_panel(tmp_path)
    assert panel.get_column("close_method").null_count() == 0
    jul = panel.filter(
        (pl.col("session_date") == date(2026, 7, 31)) & (pl.col("symbol") == "RELIANCE")
    )
    aug = panel.filter(
        (pl.col("session_date") == date(2026, 8, 3)) & (pl.col("symbol") == "RELIANCE")
    )
    setco_aug = panel.filter(
        (pl.col("session_date") == date(2026, 8, 3)) & (pl.col("symbol") == "SETCO")
    )
    assert jul.get_column("close_method").to_list() == ["vwap_30min"]
    assert aug.get_column("close_method").to_list() == ["cas_auction"]
    assert setco_aug.get_column("close_method").to_list() == ["vwap_30min"]
    counts = close_method_month_counts(panel)
    assert counts.filter(pl.col("month") == "2026-08").height >= 1


def test_rebuild_offline(tmp_path: Path) -> None:
    _u0_root_panel(tmp_path)
    actions = load_corporate_actions(FIXTURES / "corporate_actions.csv")
    impact = load_impact_cost(FIXTURES / "impact_cost.csv")
    again = build_panel(
        [date(2023, 7, 20)],
        root=tmp_path,
        actions=actions,
        impact=impact,
        allow_network=False,
    )
    assert again.height == 2


def test_delivery_median_and_impact_join(tmp_path: Path) -> None:
    panel, _ = _u0_root_panel(tmp_path)
    with_deliv = panel.with_columns(pl.col("turnover").alias("delivery_value"))
    with_deliv = attach_delivery_median(with_deliv)
    assert "delivery_value_median_20" in with_deliv.columns
    joined = join_impact_cost(panel, load_impact_cost(FIXTURES / "impact_cost.csv"))
    ril_aug = joined.filter(
        (pl.col("symbol") == "RELIANCE") & (pl.col("session_date") == date(2026, 8, 3))
    )
    assert ril_aug.get_column("impact_cost_bps").to_list() == [4.0]


def test_nifty50_membership_snapshot() -> None:
    snap = load_snapshot(FIXTURES / "ind_nifty50list.csv", NIFTY_50, date(2026, 9, 5))
    events = load_membership_events(FIXTURES / "index_events.csv")
    now = membership_as_of(events, NIFTY_50, date(2026, 9, 5), seed=snap)
    assert "RELIANCE" in now
    assert "SETCO" not in now
    in_2013 = membership_as_of(events, NIFTY_50, date(2013, 8, 26), seed=snap)
    assert "STER" in in_2013
    after = membership_as_of(events, NIFTY_50, date(2013, 8, 27), seed=snap)
    assert "STER" not in after
