"""EDGAR master-index parser. Keyed by accession number and filing timestamp."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

SEC_USER_AGENT = "algo-trade-platform/0.1 (research; author@example.com)"
MASTER_IDX_URL = "https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
EFTS_URL = "https://efts.sec.gov/LATEST/search-index"
REPO_ROOT = Path(__file__).resolve().parent.parent
EDGAR_CACHE = REPO_ROOT / "data" / "raw" / "edgar"
EFTS_PAUSE_SEC = 0.12
ITEMS_TAG = re.compile(r"<ITEMS>\s*([0-9]+\.[0-9]+)", re.IGNORECASE)
DISPLAY_TICKER = re.compile(r"\(([A-Z]{1,5}(?:\.[A-Z])?)(?:,|\))")
DELISTING_FORMS = frozenset(
    {
        "25",
        "25-NSE",
        "25/A",
        "25-NSE/A",
        "15-12B",
        "15-12G",
        "15-12B/A",
        "15-12G/A",
    }
)


@dataclass(frozen=True)
class Filing:
    cik: str
    company: str
    form: str
    filed_date: date
    accession: str
    filename: str

    @property
    def filed_at(self) -> datetime:
        """Master.idx has a date, not a clock time. Use end-of-day as knowledge time."""
        return datetime(
            self.filed_date.year,
            self.filed_date.month,
            self.filed_date.day,
            23,
            59,
            59,
            tzinfo=UTC,
        )


def accession_from_filename(filename: str) -> str:
    stem = Path(filename).name
    return stem.removesuffix(".txt")


def parse_master_idx(text: str) -> list[Filing]:
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("CIK|"):
            start = i + 2
            break
    filings: list[Filing] = []
    for line in lines[start:]:
        if not line.strip():
            continue
        cik, company, form, filed, filename = line.split("|")
        filings.append(
            Filing(
                cik=cik.lstrip("0") or "0",
                company=company,
                form=form,
                filed_date=date.fromisoformat(filed),
                accession=accession_from_filename(filename),
                filename=filename,
            )
        )
    return filings


def parse_master_idx_file(path: Path) -> list[Filing]:
    return parse_master_idx(path.read_text(encoding="utf-8", errors="replace"))


def _sec_request(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def parse_company_tickers(payload: dict) -> dict[str, str]:
    """CIK (no leading zeros) → ticker."""
    out: dict[str, str] = {}
    for row in payload.values():
        cik = str(int(row["cik_str"]))
        out[cik] = str(row["ticker"]).upper()
    return out


def load_or_fetch_company_tickers(path: Path | None = None) -> dict[str, str]:
    cache = path or (EDGAR_CACHE / "company_tickers.json")
    if cache.exists():
        payload = json.loads(cache.read_text(encoding="utf-8"))
    else:
        cache.parent.mkdir(parents=True, exist_ok=True)
        raw = _sec_request(COMPANY_TICKERS_URL)
        cache.write_bytes(raw)
        payload = json.loads(raw)
    return parse_company_tickers(payload)


def load_or_fetch_master_idx(year: int, quarter: int, directory: Path | None = None) -> list[Filing]:
    folder = directory or (EDGAR_CACHE / "master")
    path = folder / f"{year}_QTR{quarter}.idx"
    if not path.exists():
        folder.mkdir(parents=True, exist_ok=True)
        url = MASTER_IDX_URL.format(year=year, quarter=quarter)
        path.write_bytes(_sec_request(url))
        time.sleep(0.12)
    return parse_master_idx_file(path)


def eight_k_filings(filings: list[Filing]) -> list[Filing]:
    return [f for f in filings if f.form == "8-K"]


def is_delisting_form(form: str) -> bool:
    return form in DELISTING_FORMS


def delisting_filings(filings: list[Filing]) -> list[Filing]:
    return [f for f in filings if is_delisting_form(f.form)]


def parse_items_from_sgml(text: str) -> list[str]:
    return ITEMS_TAG.findall(text)


def ticker_from_display_name(name: str) -> str | None:
    match = DISPLAY_TICKER.search(name)
    if match is None:
        return None
    return match.group(1).replace(".", "-")


@dataclass(frozen=True)
class Item202Hit:
    cik: str
    ticker: str
    company: str
    accession: str
    filed_date: date
    form: str
    items: tuple[str, ...]

    def as_filing(self) -> Filing:
        padded = self.cik.zfill(10)
        return Filing(
            cik=self.cik,
            company=self.company,
            form=self.form,
            filed_date=self.filed_date,
            accession=self.accession,
            filename=f"edgar/data/{padded}/{self.accession}.txt",
        )


def parse_efts_hit(raw: dict) -> Item202Hit | None:
    source = raw["_source"]
    form = str(source["form"])
    if form != "8-K":
        return None
    items = tuple(str(item) for item in source.get("items") or [])
    if "2.02" not in items:
        return None
    names = source.get("display_names") or []
    display = names[0] if names else ""
    ticker = ticker_from_display_name(display)
    if ticker is None:
        return None
    cik_raw = (source.get("ciks") or ["0"])[0]
    return Item202Hit(
        cik=str(int(cik_raw)),
        ticker=ticker,
        company=display.split(" (")[0],
        accession=str(source["adsh"]),
        filed_date=date.fromisoformat(source["file_date"][:10]),
        form=form,
        items=items,
    )


def _efts_page(*, items: str, start: date, end: date, offset: int) -> dict:
    query = urllib.parse.urlencode(
        {
            "forms": "8-K",
            "items": items,
            "dateRange": "custom",
            "startdt": start.isoformat(),
            "enddt": end.isoformat(),
            "from": str(offset),
        }
    )
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            payload = json.loads(_sec_request(f"{EFTS_URL}?{query}"))
            time.sleep(EFTS_PAUSE_SEC)
            return payload
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(0.5 * (attempt + 1))
    raise last_error or urllib.error.URLError("EFTS failed")


def quarter_windows(start: date, end: date) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    year, quarter = start.year, 1 + (start.month - 1) // 3
    while True:
        q_start = date(year, 1 + 3 * (quarter - 1), 1)
        if quarter == 4:
            q_end = date(year, 12, 31)
        else:
            next_start = date(year, 1 + 3 * quarter, 1)
            q_end = date.fromordinal(next_start.toordinal() - 1)
        lo = max(start, q_start)
        hi = min(end, q_end)
        if lo <= hi:
            windows.append((lo, hi))
        if hi >= end:
            break
        if quarter == 4:
            year += 1
            quarter = 1
        else:
            quarter += 1
    return windows


def fetch_item_202_hits(*, start: date, end: date) -> list[dict]:
    hits: list[dict] = []
    offset = 0
    while offset <= 9900:
        payload = _efts_page(items="2.02", start=start, end=end, offset=offset)
        page = payload["hits"]["hits"]
        if not page:
            break
        hits.extend(page)
        if len(page) < 100:
            break
        offset += 100
    return hits


def load_or_fetch_item_202(
    *,
    start: date,
    end: date,
    directory: Path | None = None,
) -> list[Item202Hit]:
    folder = directory or (EDGAR_CACHE / "efts")
    by_accession: dict[str, Item202Hit] = {}
    for y_start, y_end in quarter_windows(start, end):
        stamp = f"{y_start.year}_Q{1 + (y_start.month - 1) // 3}"
        cache = folder / f"item_202_{stamp}.jsonl"
        if cache.exists():
            raw_hits = [
                json.loads(line)
                for line in cache.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        else:
            print(f"EFTS Item 2.02 {stamp}", flush=True)
            raw_hits = fetch_item_202_hits(start=y_start, end=y_end)
            folder.mkdir(parents=True, exist_ok=True)
            cache.write_text(
                "\n".join(json.dumps(hit) for hit in raw_hits) + ("\n" if raw_hits else ""),
                encoding="utf-8",
            )
        for raw in raw_hits:
            parsed = parse_efts_hit(raw)
            if parsed is None:
                continue
            if parsed.filed_date < start or parsed.filed_date > end:
                continue
            by_accession[parsed.accession] = parsed
    return sorted(by_accession.values(), key=lambda hit: (hit.filed_date, hit.ticker))


def load_master_range(
    start: date,
    end: date,
    directory: Path | None = None,
) -> list[Filing]:
    out: list[Filing] = []
    for year in range(start.year, end.year + 1):
        for quarter in range(1, 5):
            if date(year, 1 + 3 * (quarter - 1), 1) > end:
                continue
            try:
                batch = load_or_fetch_master_idx(year, quarter, directory=directory)
            except (OSError, urllib.error.URLError):
                continue
            print(f"EDGAR {year} Q{quarter}: {len(batch)} filings", flush=True)
            out.extend(
                f for f in batch if start <= f.filed_date <= end
            )
    return out
