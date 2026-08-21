"""EDGAR master-index parser. Keyed by accession number and filing timestamp."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

SEC_USER_AGENT = "algo-trade-platform/0.1 (research; author@example.com)"
MASTER_IDX_URL = "https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
REPO_ROOT = Path(__file__).resolve().parent.parent
EDGAR_CACHE = REPO_ROOT / "data" / "raw" / "edgar"


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
