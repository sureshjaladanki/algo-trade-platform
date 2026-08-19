from __future__ import annotations

import ssl
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CTX = ssl.create_default_context()

URLS = [
    "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
    "https://nsearchives.nseindia.com/content/indices/ind_niftynext50list.csv",
    "https://nsearchives.nseindia.com/content/indices/ind_mcwb_2018.zip",
    "https://nsearchives.nseindia.com/content/indices/ind_ic_2018.zip",
    "https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv",
    "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
    "https://www.niftyindices.com/reports/monthly-reports",
    "https://www.nseindia.com/api/allIndices",
    "https://www.nseindia.com/",
]


def probe(url: str) -> None:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "*/*",
            "Referer": "https://www.nseindia.com/",
        },
    )
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=25) as resp:
            blob = resp.read(120)
            print(f"OK {resp.status} {resp.headers.get_content_type()} {url}")
            print(f"  {blob[:90]!r}")
    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code} {url}")
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc} {url}")


if __name__ == "__main__":
    for item in URLS:
        probe(item)
