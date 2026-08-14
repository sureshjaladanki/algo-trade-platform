"""Point-in-time Nifty-50 membership (Wikipedia replacement ledger).

Walks the documented inclusion/exclusion list backward from the Dec-2025
constituent set. Used only as the A3 coarse-universe mask — not a live
membership feed and not a third universe rule.
"""

from __future__ import annotations

import datetime as dt
from functools import lru_cache

import polars as pl

# Canonical `.NS` tickers as of 8 Dec 2025 (Wikipedia NIFTY 50 page).
_CURRENT: frozenset[str] = frozenset(
    {
        "ADANIENT.NS",
        "ADANIPORTS.NS",
        "APOLLOHOSP.NS",
        "ASIANPAINT.NS",
        "AXISBANK.NS",
        "BAJAJ-AUTO.NS",
        "BAJFINANCE.NS",
        "BAJAJFINSV.NS",
        "BEL.NS",
        "BHARTIARTL.NS",
        "CIPLA.NS",
        "COALINDIA.NS",
        "DRREDDY.NS",
        "EICHERMOT.NS",
        "ETERNAL.NS",
        "GRASIM.NS",
        "HCLTECH.NS",
        "HDFCBANK.NS",
        "HDFCLIFE.NS",
        "HINDALCO.NS",
        "HINDUNILVR.NS",
        "ICICIBANK.NS",
        "INDIGO.NS",
        "INFY.NS",
        "ITC.NS",
        "JIOFIN.NS",
        "JSWSTEEL.NS",
        "KOTAKBANK.NS",
        "LT.NS",
        "M&M.NS",
        "MARUTI.NS",
        "MAXHEALTH.NS",
        "NESTLEIND.NS",
        "NTPC.NS",
        "ONGC.NS",
        "POWERGRID.NS",
        "RELIANCE.NS",
        "SBILIFE.NS",
        "SHRIRAMFIN.NS",
        "SBIN.NS",
        "SUNPHARMA.NS",
        "TCS.NS",
        "TATACONSUM.NS",
        "TMPV.NS",
        "TATASTEEL.NS",
        "TECHM.NS",
        "TITAN.NS",
        "TRENT.NS",
        "ULTRACEMCO.NS",
        "WIPRO.NS",
    }
)

# (effective date, excluded, included). Same-day rows are simultaneous.
_REPLACEMENTS: tuple[tuple[dt.date, str, str], ...] = (
    (dt.date(2015, 3, 27), "DLF.NS", "IDEA.NS"),
    (dt.date(2015, 3, 27), "JSPL.NS", "YESBANK.NS"),
    (dt.date(2015, 5, 29), "IDFC.NS", "BOSCHLTD.NS"),
    (dt.date(2015, 9, 28), "NMDC.NS", "ADANIPORTS.NS"),
    (dt.date(2016, 4, 1), "CAIRN.NS", "AUROPHARMA.NS"),
    (dt.date(2016, 4, 1), "PNB.NS", "INFRATEL.NS"),
    (dt.date(2016, 4, 1), "VEDL.NS", "EICHERMOT.NS"),
    (dt.date(2017, 3, 31), "BHEL.NS", "IBULHSGFIN.NS"),
    (dt.date(2017, 3, 31), "IDEA.NS", "IOC.NS"),
    (dt.date(2017, 5, 26), "GRASIM.NS", "VEDL.NS"),
    (dt.date(2017, 9, 29), "ACC.NS", "BAJFINANCE.NS"),
    (dt.date(2017, 9, 29), "BANKBARODA.NS", "HINDPETRO.NS"),
    (dt.date(2017, 9, 29), "TATAPOWER.NS", "UPL.NS"),
    (dt.date(2018, 4, 2), "AMBUJACEM.NS", "BAJAJFINSV.NS"),
    (dt.date(2018, 4, 2), "AUROPHARMA.NS", "GRASIM.NS"),
    (dt.date(2018, 4, 2), "BOSCHLTD.NS", "TITAN.NS"),
    (dt.date(2018, 9, 28), "LUPIN.NS", "JSWSTEEL.NS"),
    (dt.date(2019, 3, 29), "HINDPETRO.NS", "BRITANNIA.NS"),
    (dt.date(2019, 9, 27), "IBULHSGFIN.NS", "NESTLEIND.NS"),
    (dt.date(2020, 3, 19), "YESBANK.NS", "SHREECEM.NS"),
    (dt.date(2020, 7, 31), "VEDL.NS", "HDFCLIFE.NS"),
    (dt.date(2020, 9, 25), "ZEEL.NS", "SBILIFE.NS"),
    (dt.date(2020, 9, 25), "INFRATEL.NS", "DIVISLAB.NS"),
    (dt.date(2021, 3, 31), "GAIL.NS", "TATACONSUM.NS"),
    (dt.date(2022, 3, 31), "IOC.NS", "APOLLOHOSP.NS"),
    (dt.date(2022, 9, 30), "SHREECEM.NS", "ADANIENT.NS"),
    (dt.date(2023, 7, 13), "HDFC.NS", "LTM.NS"),
    (dt.date(2024, 3, 28), "UPL.NS", "SHRIRAMFIN.NS"),
    (dt.date(2024, 9, 30), "DIVISLAB.NS", "BEL.NS"),
    (dt.date(2024, 9, 30), "LTM.NS", "TRENT.NS"),
    (dt.date(2025, 3, 28), "BPCL.NS", "JIOFIN.NS"),
    (dt.date(2025, 3, 28), "BRITANNIA.NS", "ETERNAL.NS"),
    (dt.date(2025, 9, 30), "HEROMOTOCO.NS", "INDIGO.NS"),
    (dt.date(2025, 9, 30), "INDUSINDBK.NS", "MAXHEALTH.NS"),
)

# Names in GOLDEN that refer to the same listing as a canonical member.
_ALIASES: dict[str, str] = {
    "TATAMOTORS.NS": "TMPV.NS",
    "MCDOWELL-N.NS": "UNITDSPR.NS",
}


@lru_cache(maxsize=4096)
def nifty50_members_on(as_of: dt.date) -> frozenset[str]:
    """Nifty-50 tickers effective on ``as_of`` (inclusive of that day's change)."""
    members = set(_CURRENT)
    for event_date, excluded, included in reversed(_REPLACEMENTS):
        if event_date > as_of:
            members.discard(included)
            members.add(excluded)
    return frozenset(members)


def membership_pairs(dates: list[dt.date]) -> pl.DataFrame:
    """Long (date_only, symbol) table including GOLDEN aliases."""
    rows: list[dict] = []
    seen: set[tuple[dt.date, str]] = set()
    reverse_alias: dict[str, list[str]] = {}
    for alias, canon in _ALIASES.items():
        reverse_alias.setdefault(canon, []).append(alias)

    for day in dates:
        for symbol in nifty50_members_on(day):
            key = (day, symbol)
            if key not in seen:
                rows.append({"date_only": day, "symbol": symbol})
                seen.add(key)
            for alias in reverse_alias.get(symbol, ()):
                alias_key = (day, alias)
                if alias_key not in seen:
                    rows.append({"date_only": day, "symbol": alias})
                    seen.add(alias_key)
    return pl.DataFrame(rows)


def apply_nifty50_mask(panel: pl.DataFrame) -> pl.DataFrame:
    """Keep rows whose symbol was in Nifty 50 on that session (PIT)."""
    if panel.height == 0:
        return panel
    if "date_only" not in panel.columns:
        panel = panel.with_columns(date_only=pl.col("date").dt.date())
    dates = panel.select("date_only").unique().to_series().to_list()
    pairs = membership_pairs(dates)
    return panel.join(pairs, on=["date_only", "symbol"], how="inner")
