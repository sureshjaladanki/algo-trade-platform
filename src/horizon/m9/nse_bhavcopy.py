"""Download NSE FO bhavcopy zips (not committed; cache under data/GOLDEN_IV/raw)."""

from __future__ import annotations

import datetime as dt
import http.cookiejar
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

NSE_ARCHIVES = (
    "https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{year}/{mon}/{name}",
    "https://archives.nseindia.com/content/historical/DERIVATIVES/{year}/{mon}/{name}",
)
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def bhavcopy_filename(session_date: dt.date) -> str:
    mon = session_date.strftime("%b").upper()
    return f"fo{session_date.strftime('%d')}{mon}{session_date.year}bhav.csv.zip"


def build_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    ctx = ssl.create_default_context()
    https = urllib.request.HTTPSHandler(context=ctx)
    opener = urllib.request.build_opener(
        https, urllib.request.HTTPCookieProcessor(jar)
    )
    opener.addheaders = [
        ("User-Agent", _UA),
        ("Accept", "*/*"),
        ("Referer", "https://www.nseindia.com/"),
    ]
    try:
        opener.open("https://www.nseindia.com/", timeout=30)
    except urllib.error.URLError:
        pass
    return opener


def download_fo_bhavcopy(
    session_date: dt.date,
    dest_dir: Path,
    *,
    opener: urllib.request.OpenerDirector | None = None,
    skip_existing: bool = True,
    pause_s: float = 0.35,
) -> Path | None:
    """
    Fetch one day's FO bhavcopy zip. Returns the path, or None on 404/holiday.

    Idempotent: existing files are reused when ``skip_existing``.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = bhavcopy_filename(session_date)
    dest = dest_dir / name
    if skip_existing and dest.exists() and dest.stat().st_size > 0:
        return dest
    client = opener or build_opener()
    mon = session_date.strftime("%b").upper()
    last_err: Exception | None = None
    for _attempt in range(3):
        for tmpl in NSE_ARCHIVES:
            url = tmpl.format(year=session_date.year, mon=mon, name=name)
            try:
                with client.open(url, timeout=60) as resp:
                    payload = resp.read()
                if len(payload) < 64:
                    continue
                dest.write_bytes(payload)
                time.sleep(pause_s)
                return dest
            except urllib.error.HTTPError as exc:
                last_err = exc
                if exc.code == 404:
                    continue
                time.sleep(pause_s)
            except (urllib.error.URLError, TimeoutError) as exc:
                last_err = exc
                time.sleep(max(pause_s, 1.0))
        time.sleep(2.0)
    if last_err is not None and getattr(last_err, "code", None) not in (404, None):
        raise last_err
    return None


def iter_weekdays(start: dt.date, end: dt.date):
    """Inclusive weekday iterator (holidays still attempted; 404 skipped)."""
    day = start
    one = dt.timedelta(days=1)
    while day <= end:
        if day.weekday() < 5:
            yield day
        day += one
