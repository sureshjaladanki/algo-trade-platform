from __future__ import annotations

import re
import ssl
import urllib.request

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CTX = ssl.create_default_context()


def get(url: str, headers: dict | None = None) -> tuple[int, str, bytes]:
    hdrs = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, context=CTX, timeout=30) as resp:
        return resp.status, resp.headers.get_content_type(), resp.read()


def main() -> None:
    status, ctype, body = get("https://www.niftyindices.com/reports/monthly-reports")
    text = body.decode("utf-8", errors="replace")
    print("monthly-reports", status, ctype, len(text))
    for pat in [r"https?://[^\"']+\.(?:zip|csv|xlsx)", r"/[^\"']+\.(?:zip|csv)", r"ind_[a-zA-Z0-9_]+"]:
        hits = sorted(set(re.findall(pat, text)))
        print("PAT", pat, "n=", len(hits))
        for h in hits[:40]:
            print(" ", h)

    scripts = re.findall(r'src="([^"]+\.js[^"]*)"', text)
    print("SCRIPTS", len(scripts))
    for s in scripts:
        print(" ", s)

    apis = [
        "https://www.nseindia.com/api/allIndices",
        "https://www.nseindia.com/api/historical/indicesHistory?indexType=NIFTY%2050&from=01-01-2018&to=31-01-2018",
        "https://www.nseindia.com/api/reports?archives=%5B%7B%22name%22:%22Impact%20Cost%22,%22type%22:%22archives%22,%22category%22:%22indices%22,%22section%22:%22indices%22%7D%5D&from=01-01-2018&to=31-12-2018&type=indices&mode=single",
        "https://www.niftyindices.com/Backpage.aspx/getHistoricaldatatabletoString",
    ]
    for url in apis:
        try:
            st, ct, blob = get(url, {"Referer": "https://www.nseindia.com/all-reports", "Accept": "application/json"})
            print("API", st, ct, url[:80], blob[:120])
        except Exception as exc:
            print("API FAIL", type(exc).__name__, exc, url[:80])


if __name__ == "__main__":
    main()
