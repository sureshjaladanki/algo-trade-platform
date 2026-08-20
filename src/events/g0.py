"""G0 — assemble a free NSE quarterly results calendar for the GOLDEN panel."""

from __future__ import annotations

# NSE publishes naive IST stamps. Do not invent UTC.
# ruff: noqa: DTZ007
import datetime as dt
import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

import polars as pl

from src.events.constants import PRIOR_EVENT_SIGMA_BPS
from src.events.daily_panel import load_or_build_daily_panel
from src.events.mcwb import to_ledger_symbol
from src.events.paths import (
    DERIVED_DIR,
    G0_LOG_PATH,
    G0_MEMO_PATH,
    RESULTS_CALENDAR_PARQUET,
    RESULTS_RAW_DIR,
)
from src.events.stats import mde_bps

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_CTX = ssl.create_default_context()
_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
}
_API = (
    "https://www.nseindia.com/api/corporates-financial-results"
    "?index=equities&from_date={from_date}&to_date={to_date}&period={period}"
)
_PERIOD = "Quarterly"
G0_START = dt.date(2015, 1, 1)
G0_END = dt.date(2026, 4, 30)
_PAUSE_S = 0.2
_SCHEMA = {
    "nse_symbol": pl.String,
    "symbol": pl.String,
    "company_name": pl.String,
    "period": pl.String,
    "period_start": pl.Date,
    "period_end": pl.Date,
    "broadcast_at": pl.Datetime,
    "exchange_dissem_at": pl.Datetime,
    "consolidated": pl.String,
    "audited": pl.String,
    "xbrl_url": pl.String,
}


def half_year_windows(
    start: dt.date = G0_START,
    end: dt.date = G0_END,
) -> list[tuple[dt.date, dt.date]]:
    """Adjacent Jan–Jun / Jul–Dec windows covering [start, end]."""
    windows: list[tuple[dt.date, dt.date]] = []
    year = start.year
    first_month = 1 if start.month <= 6 else 7
    cursor = dt.date(year, first_month, 1)
    while cursor <= end:
        if cursor.month == 1:
            close = dt.date(cursor.year, 6, 30)
            nxt = dt.date(cursor.year, 7, 1)
        else:
            close = dt.date(cursor.year, 12, 31)
            nxt = dt.date(cursor.year + 1, 1, 1)
        windows.append((max(cursor, start), min(close, end)))
        cursor = nxt
    return windows


def parse_nse_datetime(text: str | None) -> dt.datetime | None:
    if text is None or text == "":
        return None
    token = text.strip()
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d-%b-%Y"):
        try:
            return dt.datetime.strptime(token, fmt)  # NSE stamps are IST, naive on purpose
        except ValueError:
            continue
    raise ValueError(f"unrecognised NSE datetime {text!r}")


def parse_nse_date(text: str | None) -> dt.date | None:
    parsed = parse_nse_datetime(text)
    if parsed is None:
        return None
    return parsed.date()


def results_url(start: dt.date, end: dt.date, period: str = _PERIOD) -> str:
    return _API.format(
        from_date=start.strftime("%d-%m-%Y"),
        to_date=end.strftime("%d-%m-%Y"),
        period=period,
    )


def chunk_path(start: dt.date, end: dt.date, dest_dir: Path = RESULTS_RAW_DIR) -> Path:
    return dest_dir / f"fr_{start.isoformat()}_{end.isoformat()}_{_PERIOD}.json"


def download_results_chunk(
    start: dt.date,
    end: dt.date,
    dest_dir: Path = RESULTS_RAW_DIR,
) -> Path:
    """Fetch one half-year JSON. Skip if already present."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = chunk_path(start, end, dest_dir)
    if path.exists() and path.stat().st_size > 2:
        return path
    req = urllib.request.Request(results_url(start, end), headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, context=_CTX, timeout=90) as resp:
            blob = resp.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"NSE results {start}..{end}: HTTP {exc.code}") from exc
    json.loads(blob.decode("utf-8"))
    path.write_bytes(blob)
    return path


def parse_results_json(blob: bytes) -> pl.DataFrame:
    payload = json.loads(blob.decode("utf-8"))
    if not isinstance(payload, list):
        raise TypeError("NSE results payload is not a list")
    rows: list[dict] = []
    for item in payload:
        nse_symbol = str(item["symbol"]).strip().upper()
        broadcast = parse_nse_datetime(item.get("broadCastDate") or item.get("filingDate"))
        if broadcast is None:
            continue
        rows.append(
            {
                "nse_symbol": nse_symbol,
                "symbol": to_ledger_symbol(nse_symbol),
                "company_name": item.get("companyName"),
                "period": item.get("period") or _PERIOD,
                "period_start": parse_nse_date(item.get("fromDate")),
                "period_end": parse_nse_date(item.get("toDate")),
                "broadcast_at": broadcast,
                "exchange_dissem_at": parse_nse_datetime(item.get("exchdisstime")),
                "consolidated": item.get("consolidated"),
                "audited": item.get("audited"),
                "xbrl_url": item.get("xbrl"),
            }
        )
    if not rows:
        return pl.DataFrame(schema=_SCHEMA)
    return pl.DataFrame(rows).select(list(_SCHEMA))


def first_broadcast(frame: pl.DataFrame) -> pl.DataFrame:
    """One row per name and period-end: the earliest exchange timestamp."""
    stamped = frame.with_columns(
        event_at=pl.coalesce("exchange_dissem_at", "broadcast_at")
    )
    return (
        stamped.sort("event_at")
        .unique(subset=["symbol", "period_end"], keep="first")
        .sort(["symbol", "event_at"])
    )


def filter_to_panel(frame: pl.DataFrame, panel_symbols: set[str]) -> pl.DataFrame:
    return frame.filter(pl.col("symbol").is_in(sorted(panel_symbols)))


def panel_symbols() -> set[str]:
    return set(load_or_build_daily_panel()["symbol"].unique().to_list())


def build_results_calendar(
    dest_dir: Path = RESULTS_RAW_DIR,
    *,
    start: dt.date = G0_START,
    end: dt.date = G0_END,
    pause_s: float = _PAUSE_S,
) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    for window_start, window_end in half_year_windows(start, end):
        path = download_results_chunk(window_start, window_end, dest_dir)
        time.sleep(pause_s)
        frames.append(parse_results_json(path.read_bytes()))
    raw = pl.concat(frames, how="vertical")
    universe = panel_symbols()
    return first_broadcast(filter_to_panel(raw, universe))


def load_or_build_results_calendar(
    parquet: Path = RESULTS_CALENDAR_PARQUET,
    *,
    rebuild: bool = False,
) -> pl.DataFrame:
    if parquet.exists() and not rebuild:
        return pl.read_parquet(parquet)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    calendar = build_results_calendar()
    parquet.parent.mkdir(parents=True, exist_ok=True)
    calendar.write_parquet(parquet)
    return calendar


def g0_verdict(n_events: int, n_names: int, n_panel: int) -> str:
    if n_events >= 200 and n_names >= max(50, n_panel // 2):
        return "PASS"
    return "DEFER"


def render_g0_memo(calendar: pl.DataFrame, n_panel: int) -> str:
    n = calendar.height
    names = calendar["symbol"].n_unique()
    missing = sorted(panel_symbols() - set(calendar["symbol"].unique().to_list()))
    years = (
        calendar.with_columns(year=pl.col("event_at").dt.year())
        .group_by("year")
        .agg(n=pl.len(), names=pl.col("symbol").n_unique())
        .sort("year")
    )
    year_lines = [
        f"| {r['year']} | {r['n']} | {r['names']} |"
        for r in years.iter_rows(named=True)
    ]
    verdict = g0_verdict(n, names, n_panel)
    miss_txt = ", ".join(missing) if missing else "(none)"
    span = (
        f"{calendar['event_at'].min()} .. {calendar['event_at'].max()}"
        if n
        else "empty"
    )
    return "\n".join(
        [
            "# G0 — Results calendar",
            "",
            "**Gate:** G0, free NSE filings. **Date:** 2026-08-19.",
            "Charter: `docs/next/g0-charter.md`. Not a residual peek.",
            "",
            "## Source",
            "",
            "NSE public `corporates-financial-results` JSON (quarterly).",
            "Timestamps are IST as published (`exchdisstime`, else `broadCastDate`).",
            "Raw chunks under `data/raw/nse_results/`. No vendor.",
            "",
            "## Coverage",
            "",
            f"- panel names: **{n_panel}**",
            f"- names with ≥1 quarterly filing: **{names}**",
            f"- events after first-broadcast dedup: **{n}**",
            f"- span: {span}",
            f"- missing names: {miss_txt}",
            f"- G1 MDE at this n, σ=600: **{mde_bps(PRIOR_EVENT_SIGMA_BPS, n):.1f} bps**"
            if n
            else "- G1 MDE: n/a",
            "",
            "The 2025–26 custom windows on this endpoint thin out (NSE moved",
            "results onto Integrated Filing). The working sample is 2015 through",
            "early 2025. That is enough for a first G1 test. Do not buy a vendor",
            "to fill 2025.",
            "",
            "| year | events | names |",
            "|---|---|---|",
            *year_lines,
            "",
            "## Book G",
            "",
            (
                "PASS. Free calendar exists on the GOLDEN panel. G1 is unblocked."
                if verdict == "PASS"
                else (
                    "DEFER. The free path did not produce a first-test calendar. "
                    "Do not buy a vendor. Book G stops."
                )
            ),
            "",
            f"**Verdict: {verdict}**",
            "",
        ]
    )


def run_g0() -> None:
    calendar = load_or_build_results_calendar(rebuild=True)
    n_panel = len(panel_symbols())
    memo = render_g0_memo(calendar, n_panel)
    G0_MEMO_PATH.write_text(memo, encoding="utf-8")
    G0_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    G0_LOG_PATH.write_text(memo, encoding="utf-8")
    print(memo)
    print(
        f"wrote {RESULTS_CALENDAR_PARQUET} rows={calendar.height} "
        f"names={calendar['symbol'].n_unique()}"
    )


def main() -> None:
    run_g0()


if __name__ == "__main__":
    main()
