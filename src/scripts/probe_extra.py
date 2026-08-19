from __future__ import annotations

import ssl
import urllib.error
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CTX = ssl.create_default_context()
BASE = "https://nsearchives.nseindia.com/content/indices/"


def exists(name: str) -> bool:
    req = urllib.request.Request(
        BASE + name,
        headers={"User-Agent": UA, "Accept": "*/*", "Referer": "https://www.nseindia.com/all-reports"},
    )
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=20) as resp:
            return resp.read(2) == b"PK"
    except urllib.error.HTTPError as exc:
        return exc.code != 404 and False
    except Exception:
        return False


def main() -> None:
    print("2014 mcwb")
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    hits = [m for m in months if exists(f"mcwb_{m}14.zip")]
    print("14", hits)
    print("nov24 alts")
    for name in ["mcwb_nov24.zip", "mcwb_nov2024.zip", "mcwb_Nov24.zip"]:
        print(name, exists(name))
    print("IC years")
    for y in range(2015, 2026):
        print(y, exists(f"ind_ic_{y}.zip"))
    print("method pdfs")
    for name in ["ind_nifty50.pdf", "ind_next50.pdf"]:
        req = urllib.request.Request(
            BASE + name,
            headers={"User-Agent": UA, "Accept": "*/*"},
        )
        try:
            with urllib.request.urlopen(req, context=CTX, timeout=20) as resp:
                print(name, resp.status, resp.headers.get_content_type(), len(resp.read(50)))
        except Exception as exc:
            print(name, type(exc).__name__, exc)


if __name__ == "__main__":
    main()
