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

CANDIDATES = [
    "ind_mcwb_2018.zip",
    "ind_mwb_2018.zip",
    "ind_mcw_2018.zip",
    "mcwb_2018.zip",
    "mwb_2018.zip",
    "ind_mcwb_nifty_2018.zip",
    "ind_mcwb_nifty50_2018.zip",
    "ind_mcwb_niftynext50_2018.zip",
    "ind_nifty_mcwb_2018.zip",
    "MWB_2018.zip",
    "ind_MCWB_2018.zip",
    "ind_mcap_2018.zip",
    "ind_mcap_wt_2018.zip",
    "ind_mcap_weightage_2018.zip",
    "ind_weightage_2018.zip",
    "indices_mcwb_2018.zip",
    "ind_nifty50_mcwb_2018.zip",
    "nifty_mcwb_2018.zip",
    "Nifty_mcwb_2018.zip",
    "ind_ffmcap_2018.zip",
    "ind_beta_2018.zip",
    "ind_mcwbbeta_2018.zip",
    "ind_mc_wt_beta_2018.zip",
    "MarketCapitalisationWeightageBeta_2018.zip",
    "ind_indices_mcap_2018.zip",
    "ind_mcapwt_2018.zip",
    "ind_mcwb.csv",
    "ind_ic_2018.zip",
    "ind_ic_niftynext50_2018.csv",
    "ind_ic_nifty50_2018.csv",
    # monthly-style
    "mcwb_jan2018.zip",
    "mcwb_jan18.zip",
    "ind_mcwb_jan2018.zip",
    "ind_mcwb_jan2018.csv",
    "MWBNiftyJan2018.csv",
    "mwbnifty_jan2018.csv",
]


def probe(url: str) -> None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": UA, "Accept": "*/*", "Referer": "https://www.nseindia.com/all-reports"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=20) as resp:
            blob = resp.read(80)
            print(f"OK {resp.status} {resp.headers.get_content_type()} {url.split('/')[-1]} {blob[:40]!r}")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            print(f"HTTP {exc.code} {url}")
    except Exception as exc:
        print(f"FAIL {type(exc).__name__}: {exc} {url}")


if __name__ == "__main__":
    for name in CANDIDATES:
        probe(BASE + name)
