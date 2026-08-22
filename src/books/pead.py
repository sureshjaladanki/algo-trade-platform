"""Book B $0 screen: EDGAR 8-K dates × Yahoo bars on names that still trade.

Not B1. Survivorship can only help a long-only drift, so a miss here kills
Polygon spend; a hit is permission to buy a delisted PIT panel, not a pass.
"""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from src.costs import WORKING_TABLE, ProductBucket
from src.edgar import (
    Filing,
    delisting_filings,
    eight_k_filings,
    load_master_range,
    load_or_fetch_company_tickers,
    load_or_fetch_item_202,
    load_or_fetch_master_idx,
)
from src.harness import Declaration
from src.universe import ADV_MID_USD, LiquidityBucket, liquidity_bucket
from src.yahoo import USER_AGENT, DailyBar, load_or_fetch

FORWARD_DAYS = 20
ADV_DAYS = 20
PEAD_SIGMA = 800.0
PEAD_HYPOTHESIZED = 100.0
PEAD_CLUSTER = 5.0
KILL_BPS = 40.0
SCREEN_START = date(2010, 1, 1)
SP500_CSV = (
    "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
)
SP400_RAW = (
    "https://en.wikipedia.org/w/index.php?title=List_of_S%26P_400_companies&action=raw"
)
SP600_RAW = (
    "https://en.wikipedia.org/w/index.php?title=List_of_S%26P_600_companies&action=raw"
)
WIKI_API = "https://en.wikipedia.org/w/api.php"
B0_LISTED_MEAN_BPS = 80.9
W_KILL = 1.0 - KILL_BPS / B0_LISTED_MEAN_BPS
TOP_ADV_N = 1_500
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UNIVERSE_CACHE = REPO_ROOT / "data" / "raw" / "universe"
YAHOO_PAUSE_SEC = 0.15

_BUCKET_PRODUCT = {
    LiquidityBucket.LIQUID_ETF: ProductBucket.LIQUID_ETF,
    LiquidityBucket.LARGE_CAP: ProductBucket.LARGE_CAP,
    LiquidityBucket.MID_CAP: ProductBucket.MID_CAP,
    LiquidityBucket.SMALL_CAP: ProductBucket.SMALL_CAP,
}


def screen_declaration(n: int) -> Declaration:
    return Declaration(
        book_id="B",
        spec_id="B.public-listed-pead",
        n=n,
        sigma=PEAD_SIGMA,
        hypothesized_effect=PEAD_HYPOTHESIZED,
        clustering_haircut=PEAD_CLUSTER,
        unit="bps_per_event",
    )


def item_202_declaration(n: int) -> Declaration:
    return Declaration(
        book_id="B",
        spec_id="B.item-202-listed-bound",
        n=n,
        sigma=PEAD_SIGMA,
        hypothesized_effect=PEAD_HYPOTHESIZED,
        clustering_haircut=PEAD_CLUSTER,
        unit="bps_per_event",
    )


def expensive_round_trip_bps(bucket: LiquidityBucket) -> float:
    product = _BUCKET_PRODUCT[bucket]
    return WORKING_TABLE[product].all_in_high


def parse_constituents_csv(text: str) -> list[str]:
    rows = csv.DictReader(text.splitlines())
    symbols: list[str] = []
    for row in rows:
        raw = row.get("Symbol") or row.get("symbol") or row.get("Ticker")
        if not raw:
            continue
        symbols.append(raw.strip().upper().replace(".", "-"))
    return symbols


def parse_wiki_tickers(wikitext: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(
        r"\{\{(?:nyse|nasdaq|amex|NYSE|NASDAQ|AMEX|NyseSymbol|NasdaqSymbol|AmexSymbol)"
        r"\|([A-Z]{1,5}(?:\.[A-Z])?)\}",
        wikitext,
        flags=re.IGNORECASE,
    ):
        ticker = match.group(1).upper().replace(".", "-")
        if ticker not in seen:
            seen.add(ticker)
            found.append(ticker)
    if len(found) >= 300:
        return found
    in_table = False
    for line in wikitext.splitlines():
        if "wikitable" in line:
            in_table = True
            continue
        if in_table and line.startswith("|}") :
            break
        if not in_table:
            continue
        stripped = line.strip()
        if re.fullmatch(r"\|\s*[A-Z]{1,5}(?:[.-][A-Z])?", stripped):
            ticker = stripped.lstrip("|").strip().upper().replace(".", "-")
            if ticker not in seen:
                seen.add(ticker)
                found.append(ticker)
    return found


def _http_text(url: str, *, user_agent: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def load_or_fetch_sp500(path: Path | None = None) -> list[str]:
    cache = path or (UNIVERSE_CACHE / "sp500.csv")
    if cache.exists():
        return parse_constituents_csv(cache.read_text(encoding="utf-8"))
    text = _http_text(SP500_CSV, user_agent=USER_AGENT)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return parse_constituents_csv(text)


def load_or_fetch_sp400(path: Path | None = None) -> list[str]:
    cache = path or (UNIVERSE_CACHE / "sp400.wiki")
    if cache.exists():
        text = cache.read_text(encoding="utf-8")
    else:
        text = _http_text(SP400_RAW, user_agent=USER_AGENT)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text, encoding="utf-8")
    return parse_wiki_tickers(text)


@dataclass(frozen=True)
class Event:
    symbol: str
    event_date: date
    surprise: float
    fwd: float
    adv_usd: float
    bucket: LiquidityBucket
    net_bps: float


def _index_on_or_after(days: list[date], target: date) -> int | None:
    for i, day in enumerate(days):
        if day >= target:
            return i
    return None


def build_events(
    *,
    filings: list[Filing],
    cik_to_ticker: dict[str, str],
    universe: set[str],
    prices: dict[str, list[DailyBar]],
) -> list[Event]:
    by_ticker: dict[str, list[date]] = {}
    for filing in eight_k_filings(filings):
        ticker = cik_to_ticker.get(filing.cik)
        if ticker is None or ticker not in universe:
            continue
        by_ticker.setdefault(ticker, []).append(filing.filed_date)
    events: list[Event] = []
    for ticker, event_days in by_ticker.items():
        bars = prices.get(ticker)
        if not bars:
            continue
        days = [bar.date for bar in bars]
        closes = [bar.close for bar in bars]
        notionals = [bar.close * bar.volume for bar in bars]
        for event_date in event_days:
            event = _one_event(ticker, event_date, days, closes, notionals)
            if event is not None:
                events.append(event)
    events.sort(key=lambda item: (item.event_date, item.symbol))
    return events


def _one_event(
    ticker: str,
    event_date: date,
    days: list[date],
    closes: list[float],
    notionals: list[float],
) -> Event | None:
    i = _index_on_or_after(days, event_date)
    if i is None:
        return None
    end = i + 1 + FORWARD_DAYS
    if i < ADV_DAYS or i < 1 or end >= len(days):
        return None
    surprise = closes[i + 1] / closes[i - 1] - 1.0
    if surprise <= 0:
        return None
    fwd = closes[end] / closes[i + 1] - 1.0
    adv = sum(notionals[i - ADV_DAYS : i]) / ADV_DAYS
    if adv < ADV_MID_USD:
        return None
    bucket = liquidity_bucket(adv, symbol=ticker)
    if bucket is LiquidityBucket.MICRO_CLOSED:
        return None
    net = 1e4 * fwd - expensive_round_trip_bps(bucket)
    return Event(
        symbol=ticker,
        event_date=days[i],
        surprise=surprise,
        fwd=fwd,
        adv_usd=adv,
        bucket=bucket,
        net_bps=net,
    )


def mid_cap_events(events: list[Event]) -> list[Event]:
    return [event for event in events if event.bucket is LiquidityBucket.MID_CAP]


def pooled_net_bps(events: list[Event]) -> float:
    if not events:
        raise ValueError("no events")
    return sum(event.net_bps for event in events) / len(events)


@dataclass(frozen=True)
class PeadScreen:
    n: int
    n_mid: int
    mean_net_bps: float
    mean_mid_bps: float | None
    kill: bool
    buy_polygon: bool


def run_pead_screen(events: list[Event]) -> PeadScreen:
    """Summarize a panel that has already cleared the MDE printer."""
    mid = mid_cap_events(events)
    mean = pooled_net_bps(events)
    mid_mean = pooled_net_bps(mid) if mid else None
    dead = mid_mean is not None and mid_mean < KILL_BPS
    return PeadScreen(
        n=len(events),
        n_mid=len(mid),
        mean_net_bps=mean,
        mean_mid_bps=mid_mean,
        kill=dead,
        buy_polygon=mid_mean is not None and mid_mean >= KILL_BPS,
    )


def load_universe() -> set[str]:
    names = set(load_or_fetch_sp400())
    print(f"S&P 400 tickers: {len(names)}", flush=True)
    if len(names) < 300:
        extra = load_or_fetch_sp500()
        names.update(extra)
        print(f"added S&P 500, universe {len(names)}", flush=True)
    return names


def load_filings(start: date = SCREEN_START, end: date | None = None) -> list[Filing]:
    stop = end or datetime.now(tz=UTC).date()
    out: list[Filing] = []
    for year in range(start.year, stop.year + 1):
        for quarter in range(1, 5):
            if date(year, 1 + 3 * (quarter - 1), 1) > stop:
                continue
            try:
                batch = load_or_fetch_master_idx(year, quarter)
            except (OSError, urllib.error.URLError):
                continue
            print(f"EDGAR {year} Q{quarter}: {len(batch)} filings", flush=True)
            out.extend(eight_k_filings(batch))
    return [f for f in out if start <= f.filed_date <= stop]


def load_prices(symbols: set[str], *, pause: float = YAHOO_PAUSE_SEC) -> dict[str, list[DailyBar]]:
    from src.yahoo import cache_path

    symbols_sorted = sorted(symbols)
    out: dict[str, list[DailyBar]] = {}
    for i, symbol in enumerate(symbols_sorted, start=1):
        cached = cache_path(symbol).exists()
        try:
            out[symbol] = load_or_fetch(symbol, start=SCREEN_START)
        except (OSError, urllib.error.URLError, TypeError, KeyError, ValueError):
            print(f"Yahoo skip {symbol} ({i}/{len(symbols_sorted)})", flush=True)
            continue
        if i == 1 or i % 25 == 0 or i == len(symbols_sorted):
            print(f"Yahoo {symbol} {i}/{len(symbols_sorted)}", flush=True)
        if not cached and pause:
            time.sleep(pause)
    return out


def load_public_events() -> list[Event]:
    universe = load_universe()
    tickers = load_or_fetch_company_tickers()
    filings = load_filings()
    prices = load_prices(universe)
    return build_events(
        filings=filings,
        cik_to_ticker=tickers,
        universe=set(prices),
        prices=prices,
    )


def load_or_fetch_sp600(path: Path | None = None) -> list[str]:
    cache = path or (UNIVERSE_CACHE / "sp600.wiki")
    if cache.exists():
        text = cache.read_text(encoding="utf-8")
    else:
        text = _http_text(SP600_RAW, user_agent=USER_AGENT)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text, encoding="utf-8")
    return parse_wiki_tickers(text)


def listed_candidate_symbols() -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    loaders = (load_or_fetch_sp500, load_or_fetch_sp400, load_or_fetch_sp600)
    for loader in loaders:
        try:
            batch = loader()
        except (OSError, urllib.error.URLError, TypeError, KeyError, ValueError):
            continue
        for symbol in batch:
            if symbol in seen:
                continue
            seen.add(symbol)
            names.append(symbol)
    print(f"listed candidates: {len(names)}", flush=True)
    return names


def recent_adv_usd(bars: list[DailyBar], *, days: int = ADV_DAYS) -> float:
    window = bars[-days:]
    return sum(bar.close * bar.volume for bar in window) / len(window)


def load_liquid_universe() -> tuple[set[str], dict[str, list[DailyBar]]]:
    symbols = listed_candidate_symbols()
    prices = load_prices(set(symbols))
    ranked: list[tuple[float, str]] = []
    for symbol, bars in prices.items():
        if len(bars) < ADV_DAYS:
            continue
        adv = recent_adv_usd(bars)
        if adv < ADV_MID_USD:
            continue
        ranked.append((adv, symbol))
    ranked.sort(reverse=True)
    top = ranked[:TOP_ADV_N]
    universe = {symbol for _, symbol in top}
    print(f"liquid universe ADV>${ADV_MID_USD / 1e6:.0f}M: {len(universe)}", flush=True)
    return universe, {symbol: prices[symbol] for symbol in universe}


def _wiki_revision_text(title: str, asof: date) -> str:
    query = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvlimit": "1",
            "rvstart": asof.isoformat() + "T00:00:00Z",
            "rvdir": "older",
            "rvprop": "content",
            "rvslots": "main",
        }
    )
    payload = json.loads(_http_text(f"{WIKI_API}?{query}", user_agent=USER_AGENT))
    pages = payload["query"]["pages"]
    page = next(iter(pages.values()))
    revision = page["revisions"][0]
    if "slots" in revision:
        return revision["slots"]["main"]["*"]
    return revision["*"]


def load_or_fetch_sp400_history(path: Path | None = None) -> set[str]:
    cache = path or (UNIVERSE_CACHE / "sp400_history.txt")
    if cache.exists():
        return {line.strip() for line in cache.read_text(encoding="utf-8").splitlines() if line.strip()}
    names = set(load_or_fetch_sp400())
    for year in range(2010, 2027, 2):
        try:
            text = _wiki_revision_text("List of S&P 400 companies", date(year, 1, 1))
        except (OSError, urllib.error.URLError, KeyError, TypeError, ValueError):
            continue
        found = parse_wiki_tickers(text)
        if len(found) >= 200:
            names.update(found)
        time.sleep(0.2)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text("\n".join(sorted(names)) + "\n", encoding="utf-8")
    return names


def missing_share(*, n_listed: int, n_missing: int) -> float:
    """w = N_missing / (N_listed + N_missing)."""
    denom = n_listed + n_missing
    if denom == 0:
        raise ValueError("empty listed and missing sets")
    return n_missing / denom


def zero_drift_bound(*, listed_mean_bps: float, w: float) -> float:
    return (1.0 - w) * listed_mean_bps


def yahoo_missing(symbols: set[str]) -> set[str]:
    from src.yahoo import cache_path

    missing: set[str] = set()
    for symbol in sorted(symbols):
        if cache_path(symbol).exists():
            continue
        try:
            load_or_fetch(symbol, start=SCREEN_START)
        except (OSError, urllib.error.URLError, TypeError, KeyError, ValueError):
            missing.add(symbol)
            print(f"Yahoo missing {symbol}", flush=True)
            continue
        time.sleep(YAHOO_PAUSE_SEC)
    return missing


@dataclass(frozen=True)
class BoundScreen:
    n_mid: int
    mean_mid_bps: float | None
    w: float
    w_membership: float
    n_listed: int
    n_missing: int
    n_left_index: int
    n_form25: int
    bound_bps: float
    w_kill: float
    item_202_alive: bool
    b0_informs: bool
    kill: bool


def run_bound_screen(
    *,
    events: list[Event],
    listed: set[str],
    ever: set[str],
    delisted: set[str],
    n_form25: int,
) -> BoundScreen:
    mid = mid_cap_events(events)
    mid_mean = pooled_net_bps(mid) if mid else None
    n_missing = len(delisted)
    n_left = len(ever - listed)
    w = missing_share(n_listed=len(listed), n_missing=n_missing)
    w_membership = missing_share(n_listed=len(listed), n_missing=n_left) if ever else 0.0
    bound = zero_drift_bound(listed_mean_bps=mid_mean or 0.0, w=w)
    dead = mid_mean is None or mid_mean < KILL_BPS
    return BoundScreen(
        n_mid=len(mid),
        mean_mid_bps=mid_mean,
        w=w,
        w_membership=w_membership,
        n_listed=len(listed),
        n_missing=n_missing,
        n_left_index=n_left,
        n_form25=n_form25,
        bound_bps=bound,
        w_kill=W_KILL,
        item_202_alive=not dead,
        b0_informs=w < W_KILL and not dead and bound >= KILL_BPS,
        kill=dead,
    )


def load_item_202_events() -> tuple[list[Event], set[str], dict[str, list[DailyBar]]]:
    universe, prices = load_liquid_universe()
    hits = load_or_fetch_item_202(start=SCREEN_START, end=datetime.now(tz=UTC).date())
    cik_to_ticker = {hit.cik: hit.ticker for hit in hits}
    cik_to_ticker.update(load_or_fetch_company_tickers())
    filings = [hit.as_filing() for hit in hits]
    events = build_events(
        filings=filings,
        cik_to_ticker=cik_to_ticker,
        universe=universe,
        prices=prices,
    )
    return events, universe, prices


def load_delist_identifiers() -> tuple[set[str], int, set[str]]:
    listed = set(load_or_fetch_sp400())
    ever = load_or_fetch_sp400_history()
    left = ever - listed
    print(f"S&P 400 ever {len(ever)} current {len(listed)} left {len(left)}", flush=True)
    yahoo_gone = yahoo_missing(left)
    master = load_master_range(SCREEN_START, datetime.now(tz=UTC).date())
    form25 = delisting_filings(master)
    n_form25 = len({filing.cik for filing in form25})
    print(f"Form 25/15 unique CIKs: {n_form25}; Yahoo-gone leavers: {len(yahoo_gone)}", flush=True)
    return listed, n_form25, yahoo_gone
