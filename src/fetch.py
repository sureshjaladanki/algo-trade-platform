"""HTTP fetch with IST market-hours blackout, 2s pacing, backoff, content-addressed cache."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from datetime import time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
MIN_INTERVAL_SEC = 2.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
BLACKOUT_START = dt_time(9, 0)
BLACKOUT_END = dt_time(16, 16)


class FetchBlackoutError(RuntimeError):
    """Raised when a live fetch is attempted in the NSE cash session window."""


@dataclass(frozen=True)
class CacheHit:
    key: str
    payload: bytes
    sha256: str
    missing: bool


_last_request_at = 0.0


def now_ist(clock: datetime | None = None) -> datetime:
    if clock is None:
        return datetime.now(tz=IST)
    if clock.tzinfo is None:
        return clock.replace(tzinfo=IST)
    return clock.astimezone(IST)


def in_fetch_blackout(clock: datetime | None = None) -> bool:
    """Weekday 09:00–16:15 IST. Weekends are not market hours (blueprint §9.3)."""
    stamp = now_ist(clock)
    if stamp.weekday() >= 5:
        return False
    return BLACKOUT_START <= stamp.time() < BLACKOUT_END


def _pace() -> None:
    global _last_request_at
    wait = MIN_INTERVAL_SEC - (time.monotonic() - _last_request_at)
    if wait > 0:
        time.sleep(wait)
    _last_request_at = time.monotonic()


def cache_root(root: Path) -> Path:
    path = root / "cache"
    (path / "objects").mkdir(parents=True, exist_ok=True)
    return path


def _object_path(root: Path, digest: str) -> Path:
    return cache_root(root) / "objects" / digest[:2] / digest


def _index_path(root: Path) -> Path:
    return cache_root(root) / "index.jsonl"


def _index_lookup(root: Path, key: str) -> dict | None:
    path = _index_path(root)
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        if row["key"] == key:
            return row
    return None


def _index_append(root: Path, row: dict) -> None:
    with _index_path(root).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def get_cached(root: Path, key: str) -> CacheHit | None:
    row = _index_lookup(root, key)
    if row is None:
        return None
    if row.get("missing"):
        return CacheHit(key=key, payload=b"", sha256=row["sha256"], missing=True)
    path = _object_path(root, row["sha256"])
    return CacheHit(key=key, payload=path.read_bytes(), sha256=row["sha256"], missing=False)


def put_cached(root: Path, key: str, payload: bytes, *, missing: bool = False) -> CacheHit:
    digest = hashlib.sha256(payload).hexdigest()
    if not missing:
        path = _object_path(root, digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(payload)
    if _index_lookup(root, key) is None:
        _index_append(
            root,
            {"key": key, "sha256": digest, "missing": missing, "nbytes": len(payload)},
        )
    return CacheHit(key=key, payload=payload, sha256=digest, missing=missing)


def fetch_bytes(
    url: str,
    *,
    root: Path,
    key: str,
    clock: datetime | None = None,
    allow_network: bool = True,
) -> CacheHit:
    hit = get_cached(root, key)
    if hit is not None:
        return hit
    if not allow_network:
        raise FileNotFoundError(key)
    if in_fetch_blackout(clock):
        raise FetchBlackoutError(f"no live fetch 09:00–16:15 IST weekdays: {url}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    delay = 1.0
    last_exc: Exception | None = None
    for _attempt in range(5):
        _pace()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = resp.read()
            return put_cached(root, key, payload, missing=False)
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 404:
                return put_cached(root, key, b"", missing=True)
            if exc.code in {429, 500, 502, 503, 504} or exc.code >= 500:
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except TimeoutError as exc:
            last_exc = exc
            time.sleep(delay)
            delay *= 2
    raise last_exc if last_exc else RuntimeError(url)


def cached_session_keys(root: Path, prefix: str) -> list[str]:
    path = _index_path(root)
    if not path.exists():
        return []
    keys = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        if row["key"].startswith(prefix) and not row.get("missing"):
            keys.append(row["key"])
    return keys
