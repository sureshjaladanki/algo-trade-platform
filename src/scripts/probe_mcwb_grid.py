from __future__ import annotations

import io
import ssl
import urllib.error
import urllib.request
import zipfile

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CTX = ssl.create_default_context()
BASE = "https://nsearchives.nseindia.com/content/indices/"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "*/*", "Referer": "https://www.nseindia.com/all-reports"},
    )
    with urllib.request.urlopen(req, context=CTX, timeout=30) as resp:
        return resp.read()


def exists(name: str) -> bool:
    try:
        data = fetch(BASE + name)
        return data[:2] == b"PK"
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False
        print("HTTP", exc.code, name)
        return False
    except Exception as exc:
        print("FAIL", type(exc).__name__, name, exc)
        return False


def inspect(name: str) -> None:
    raw = fetch(BASE + name)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        print(name, "members:", zf.namelist())
        for member in zf.namelist()[:4]:
            with zf.open(member) as fh:
                head = fh.read(500).decode("latin-1", errors="replace")
            print("---", member)
            print(head[:400])
            print("---")


if __name__ == "__main__":
    print("=== inspect samples ===")
    for sample in ["mcwb_jan18.zip", "mcwb_jul15.zip", "mcwb_jan24.zip", "mcwb_jan2018.zip", "mcwb_jan24.csv"]:
        try:
            inspect(sample)
        except urllib.error.HTTPError as exc:
            print("HTTP", exc.code, sample)
        except Exception as exc:
            print("FAIL", sample, type(exc).__name__, exc)

    print("=== year/month grid yy ===")
    for yy in range(15, 26):
        hits = [m for m in MONTHS if exists(f"mcwb_{m}{yy:02d}.zip")]
        print(yy, len(hits), ",".join(hits))
