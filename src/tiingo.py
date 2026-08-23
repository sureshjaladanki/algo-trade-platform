"""Tiingo Starter EOD. $0 coverage probe for Yahoo-missing S&P 400 names. Not B1."""

from __future__ import annotations

import csv
import io
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from src.books.pead import (
    SCREEN_START,
    load_or_fetch_sp400,
    load_or_fetch_sp400_history,
)
from src.yahoo import DailyBar, write_daily_bars
from src.yahoo import cache_path as yahoo_cache_path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "data" / "raw" / "tiingo"
ENV_KEY = "TIINGO_API_KEY"
TICKERS_URL = "https://apimedia.tiingo.com/docs/tiingo/daily/supported_tickers.zip"
EOD_URL = "https://api.tiingo.com/tiingo/daily/{ticker}/prices"
USER_AGENT = "algo-trade-platform/0.1 (research)"
TODAY = date(2026, 8, 22)
ALIVE_END = date(2026, 1, 1)
MAJOR_EXCHANGES = frozenset(
    {"NYSE", "NASDAQ", "AMEX", "BATS", "IEX", "NYSE MKT", "NYSE ARCA", "NYSEARCA"}
)
OTC_EXCHANGES = frozenset(
    {
        "PINK",
        "OTCMKTS",
        "OTCGREY",
        "OTCBB",
        "OTCQB",
        "OTCCE",
        "OTCQX",
        "OTCD",
        "OTCM",
    }
)
KNOWN_SPLICE = frozenset({"CHK"})
KNOWN_REUSE = frozenset({"JAVA", "PCS"})
# Identity QA: do not treat these as bound recoveries even if a file exists.
DIRTY_IDENTITY = frozenset({"AHL", "SIVB", "JAVA", "PCS", "CHK"})
EOD_VERIFY_N = 8
USABLE_STATUSES = frozenset({"recovered", "otc_history"})
REQUESTS_PER_HOUR = 50
DUMP_PAUSE_SEC = 3600.0 / REQUESTS_PER_HOUR
RATE_LIMIT_RETRY_SEC = 120.0
# Old S&P 400 / EDGAR ticker → free successor with Yahoo or Tiingo bars.
SUCCESSOR_TICKERS: dict[str, str] = {
    "AAXN": "AXON",
    "ADS": "BFH",
    "AINV": "MFIC",
    "AMB": "PLD",
    "APY": "CHX",
    "ASGN": "EFOR",
    "ATGE": "CVSA",
    "BXS": "CADE",
    "CFX": "ENOV",
    "CHFC": "HBAN",
    "CLI": "VRE",
    "CPO": "INGR",
    "CREE": "WOLF",
    "CSAL": "UNIT",
    "DRQ": "INVX",
    "EK": "KODK",
    "ELY": "MODG",
    "ENDP": "ENDPQ",
    "ERI": "CZR",
    "ESV": "VAL",
    "FBHS": "FBIN",
    "FII": "FHI",
    "GDI": "IR",
    "GMT": "GATX",
    "GPS": "GAP",
    "HANS": "MNST",
    "HFC": "DINO",
    "HPT": "SVC",
    "HSC": "NVRI",
    "HUB-B": "HUBB",
    "JCOM": "ZD",
    "JOYG": "JOY",
    "JW-A": "WLY",
    "KAR": "OPLN",
    "LANC": "MZTI",
    "LKQX": "LKQ",
    "MLHR": "MLKN",
    "NCR": "NATL",
    "NST": "ES",
    "NYB": "FLG",
    "NYCB": "FLG",
    "OFC": "CDP",
    "PMTC": "PTC",
    "PNM": "TXNM",
    "POL": "AVNT",
    "RCII": "UPBD",
    "RE": "EG",
    "SGMS": "LNW",
    "SIVB": "SIVBQ",
    "SNH": "DHC",
    "TMST": "MTUS",
    "TPX": "SGI",
    "UTR": "KMPR",
    "WFSL": "WAFD",
    "WTR": "WTRG",
    "WYND": "WH",
    "ZI": "GTM",
}


class TiingoUnavailable(Exception):
    """Tiingo client could not authenticate or fetch."""


@dataclass(frozen=True)
class TickerRow:
    ticker: str
    exchange: str
    asset_type: str
    start: date | None
    end: date | None


@dataclass(frozen=True)
class CoverageHit:
    symbol: str
    status: str
    exchange: str
    asset_type: str
    start: date | None = None
    end: date | None = None
    n_bars: int = 0
    first: date | None = None
    last: date | None = None
    eod_error: str = ""


@dataclass(frozen=True)
class CoverageReport:
    n_listed: int
    n_left: int
    n_missing: int
    n_in_file: int
    n_recovered: int
    n_otc_history: int
    n_stub: int
    n_reject: int
    n_absent: int
    n_eod_ok: int
    n_eod_fail: int
    hits: tuple[CoverageHit, ...]

    @property
    def file_coverage(self) -> float:
        if self.n_missing == 0:
            raise ValueError("empty missing set")
        return self.n_in_file / self.n_missing

    @property
    def usable_coverage(self) -> float:
        if self.n_missing == 0:
            raise ValueError("empty missing set")
        return (self.n_recovered + self.n_otc_history) / self.n_missing


def _parse_day(value: str) -> date | None:
    text = value.strip()
    if not text:
        return None
    return date.fromisoformat(text[:10])


def normalize_ticker(symbol: str) -> str:
    return symbol.strip().upper().replace(".", "-")


def _load_api_key() -> str:
    key = os.environ.get(ENV_KEY, "").strip().strip('"').strip("'")
    if key:
        return key
    path = REPO_ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{ENV_KEY}="):
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    raise TiingoUnavailable(f"{ENV_KEY} is missing from .env")


def parse_supported_rows(text: str) -> dict[str, TickerRow]:
    rows = csv.DictReader(io.StringIO(text))
    out: dict[str, TickerRow] = {}
    for raw in rows:
        ticker = normalize_ticker(raw["ticker"])
        row = TickerRow(
            ticker=ticker,
            exchange=(raw.get("exchange") or "").strip().upper(),
            asset_type=(raw.get("assetType") or "").strip(),
            start=_parse_day(raw.get("startDate") or ""),
            end=_parse_day(raw.get("endDate") or ""),
        )
        out[ticker] = row
    return out


def load_or_fetch_supported_tickers(path: Path | None = None) -> dict[str, TickerRow]:
    cache = path or (CACHE_DIR / "supported_tickers.csv")
    if cache.exists():
        return parse_supported_rows(cache.read_text(encoding="utf-8"))
    request = urllib.request.Request(TICKERS_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        blob = response.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        text = zf.read(zf.namelist()[0]).decode("utf-8")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return parse_supported_rows(text)


def classify_row(symbol: str, row: TickerRow | None) -> str:
    if row is None:
        return "absent"
    if symbol in KNOWN_SPLICE:
        return "splice"
    if symbol in KNOWN_REUSE or row.asset_type.lower() != "stock":
        return "reuse"
    ended = row.end is not None and row.end < ALIVE_END
    long_hist = row.start is not None and row.start <= SCREEN_START
    if row.exchange in MAJOR_EXCHANGES and ended:
        return "recovered"
    if row.exchange in OTC_EXCHANGES and long_hist:
        return "otc_history"
    if row.exchange in OTC_EXCHANGES:
        return "stub"
    if row.exchange in MAJOR_EXCHANGES and not ended:
        return "still_listed"
    return "other"


def yahoo_missing_from_cache(symbols: set[str]) -> set[str]:
    return {symbol for symbol in symbols if not yahoo_cache_path(symbol).exists()}


def resolve_price_symbol(symbol: str) -> str:
    """Map a historical ticker to the free-tape symbol used for prices."""
    return SUCCESSOR_TICKERS.get(normalize_ticker(symbol), normalize_ticker(symbol))


def price_on_disk(symbol: str) -> bool:
    """True if Yahoo or Tiingo cache has bars for symbol or its successor."""
    key = normalize_ticker(symbol)
    if key in DIRTY_IDENTITY:
        return False
    candidates = [key]
    successor = SUCCESSOR_TICKERS.get(key)
    if successor and successor not in DIRTY_IDENTITY:
        candidates.append(successor)
    for name in candidates:
        if yahoo_cache_path(name).exists():
            return True
        if eod_cache_path(name).exists():
            return True
    return False


def still_missing_prices(symbols: set[str]) -> set[str]:
    """Former members with no free Yahoo/Tiingo/successor tape on disk."""
    return {symbol for symbol in symbols if not price_on_disk(symbol)}


def sp400_yahoo_missing() -> tuple[set[str], set[str], set[str]]:
    listed = set(load_or_fetch_sp400())
    ever = load_or_fetch_sp400_history()
    left = ever - listed
    return listed, left, yahoo_missing_from_cache(left)


def bars_from_eod(records: list[dict]) -> list[DailyBar]:
    bars: list[DailyBar] = []
    for row in records:
        close = float(row.get("adjClose") or row.get("close") or 0.0)
        if close <= 0:
            continue
        bars.append(
            DailyBar(
                date=date.fromisoformat(str(row["date"])[:10]),
                close=close,
                dividend=float(row.get("divCash") or 0.0),
                volume=float(row.get("volume") or 0.0),
            )
        )
    return [bar for bar in bars if bar.date >= SCREEN_START]


def eod_cache_path(symbol: str, directory: Path = CACHE_DIR) -> Path:
    return directory / f"{normalize_ticker(symbol)}.csv"


def fetch_eod(symbol: str, *, start: date = SCREEN_START) -> list[DailyBar]:
    ticker = urllib.parse.quote(symbol, safe="")
    query = urllib.parse.urlencode(
        {"startDate": start.isoformat(), "endDate": TODAY.isoformat(), "format": "json"}
    )
    request = urllib.request.Request(
        f"{EOD_URL.format(ticker=ticker)}?{query}",
        headers={
            "User-Agent": USER_AGENT,
            "Authorization": f"Token {_load_api_key()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code != 429:
            raise TiingoUnavailable(f"HTTP {exc.code}") from exc
        time.sleep(RATE_LIMIT_RETRY_SEC)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as retry_exc:
            raise TiingoUnavailable(f"HTTP {retry_exc.code}") from retry_exc
    if not isinstance(payload, list):
        raise TiingoUnavailable("unexpected Tiingo payload")
    return bars_from_eod(payload)


def load_or_fetch_eod(
    symbol: str,
    *,
    start: date = SCREEN_START,
    directory: Path = CACHE_DIR,
) -> list[DailyBar]:
    path = eod_cache_path(symbol, directory)
    if path.exists():
        from src.yahoo import load_daily_bars

        return [bar for bar in load_daily_bars(path) if bar.date >= start]
    bars = fetch_eod(symbol, start=start)
    write_daily_bars(bars, path)
    return bars


def _hit_from_row(symbol: str, row: TickerRow | None) -> CoverageHit:
    status = classify_row(symbol, row)
    if row is None:
        return CoverageHit(symbol=symbol, status=status, exchange="", asset_type="")
    return CoverageHit(
        symbol=symbol,
        status=status,
        exchange=row.exchange,
        asset_type=row.asset_type,
        start=row.start,
        end=row.end,
    )


def verify_eod(hits: list[CoverageHit], *, limit: int = EOD_VERIFY_N) -> list[CoverageHit]:
    usable = usable_hits(hits)
    sample = usable[:limit]
    out: list[CoverageHit] = []
    by_symbol = {hit.symbol: hit for hit in hits}
    verified: set[str] = set()
    for hit in sample:
        verified.add(hit.symbol)
        try:
            bars = load_or_fetch_eod(hit.symbol)
        except (TiingoUnavailable, OSError, urllib.error.URLError, TypeError, KeyError, ValueError) as exc:
            by_symbol[hit.symbol] = CoverageHit(
                symbol=hit.symbol,
                status=hit.status,
                exchange=hit.exchange,
                asset_type=hit.asset_type,
                start=hit.start,
                end=hit.end,
                eod_error=str(exc),
            )
            continue
        by_symbol[hit.symbol] = CoverageHit(
            symbol=hit.symbol,
            status=hit.status,
            exchange=hit.exchange,
            asset_type=hit.asset_type,
            start=hit.start,
            end=hit.end,
            n_bars=len(bars),
            first=bars[0].date if bars else None,
            last=bars[-1].date if bars else None,
        )
    for hit in hits:
        out.append(by_symbol[hit.symbol] if hit.symbol in verified else hit)
    return out


def run_coverage(*, verify: bool = True) -> CoverageReport:
    listed, left, missing = sp400_yahoo_missing()
    tickers = load_or_fetch_supported_tickers()
    hits = [_hit_from_row(symbol, tickers.get(symbol)) for symbol in sorted(missing)]
    if verify:
        hits = verify_eod(hits)
    statuses = [hit.status for hit in hits]
    eod_ok = sum(1 for hit in hits if hit.n_bars > 0)
    eod_fail = sum(1 for hit in hits if hit.eod_error)
    return CoverageReport(
        n_listed=len(listed),
        n_left=len(left),
        n_missing=len(missing),
        n_in_file=sum(1 for status in statuses if status != "absent"),
        n_recovered=statuses.count("recovered"),
        n_otc_history=statuses.count("otc_history"),
        n_stub=statuses.count("stub"),
        n_reject=statuses.count("splice") + statuses.count("reuse"),
        n_absent=statuses.count("absent"),
        n_eod_ok=eod_ok,
        n_eod_fail=eod_fail,
        hits=tuple(hits),
    )


def eod_file_count(directory: Path = CACHE_DIR) -> int:
    return sum(1 for path in directory.glob("*.csv") if path.name != "supported_tickers.csv")


@dataclass(frozen=True)
class DumpReport:
    n_usable: int
    n_cached: int
    n_fetched: int
    n_failed: int
    failures: tuple[str, ...]


def usable_hits(hits: list[CoverageHit] | tuple[CoverageHit, ...]) -> list[CoverageHit]:
    return [hit for hit in hits if hit.status in USABLE_STATUSES]


def pending_eod_symbols(
    hits: list[CoverageHit] | tuple[CoverageHit, ...],
    *,
    directory: Path = CACHE_DIR,
) -> list[str]:
    return [
        hit.symbol
        for hit in usable_hits(hits)
        if not eod_cache_path(hit.symbol, directory).exists()
    ]


def dump_usable_eod(
    hits: list[CoverageHit] | tuple[CoverageHit, ...] | None = None,
    *,
    pause_sec: float = DUMP_PAUSE_SEC,
    directory: Path = CACHE_DIR,
) -> DumpReport:
    """Download remaining usable EOD series. Cached names are skipped."""
    if hits is None:
        hits = run_coverage(verify=False).hits
    pending = pending_eod_symbols(hits, directory=directory)
    n_usable = len(usable_hits(hits))
    fetched = 0
    failures: list[str] = []
    print(f"Tiingo dump: {len(pending)} pending of {n_usable} usable", flush=True)
    for i, symbol in enumerate(pending, start=1):
        try:
            bars = load_or_fetch_eod(symbol, directory=directory)
        except (
            TiingoUnavailable,
            OSError,
            urllib.error.URLError,
            TypeError,
            KeyError,
            ValueError,
        ) as exc:
            failures.append(symbol)
            print(f"Tiingo fail {symbol} ({i}/{len(pending)}): {exc}", flush=True)
        else:
            fetched += 1
            print(f"Tiingo {symbol} {i}/{len(pending)} n={len(bars)}", flush=True)
        if pause_sec and i < len(pending):
            time.sleep(pause_sec)
    print(
        f"Tiingo dump complete: cached={n_usable - len(pending)} "
        f"fetched={fetched} failed={len(failures)}",
        flush=True,
    )
    return DumpReport(
        n_usable=n_usable,
        n_cached=n_usable - len(pending),
        n_fetched=fetched,
        n_failed=len(failures),
        failures=tuple(failures),
    )


if __name__ == "__main__":
    dump_usable_eod()
