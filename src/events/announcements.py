"""Free public announcement dates for Nifty-50 reconstitutions.

Dates are IISL / NSE Indices press-release days when a circular cites them,
otherwise the first contemporaneous news print of the same swap. Effective
dates must match the in-repo replacement ledger. Not a vendor calendar.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import polars as pl

from src.events.membership import REPLACEMENTS


@dataclass(frozen=True)
class Announcement:
    ledger_effective: dt.date
    excluded: str
    included: str
    announcement_date: dt.date
    kind: str  # semi_annual | ad_hoc
    source: str


# One row per REPLACEMENTS pair. Validated in tests against that ledger.
ANNOUNCEMENTS: tuple[Announcement, ...] = (
    Announcement(
        dt.date(2015, 3, 27), "DLF.NS", "IDEA.NS", dt.date(2015, 2, 20),
        "semi_annual", "Hindu Business Line 2015-02-20 (IISL Friday circular)",
    ),
    Announcement(
        dt.date(2015, 3, 27), "JSPL.NS", "YESBANK.NS", dt.date(2015, 2, 20),
        "semi_annual", "Hindu Business Line 2015-02-20 (IISL Friday circular)",
    ),
    Announcement(
        dt.date(2015, 5, 29), "IDFC.NS", "BOSCHLTD.NS", dt.date(2015, 4, 29),
        "ad_hoc", "Economic Times 2015-04-29 (IISL announced today)",
    ),
    Announcement(
        dt.date(2015, 9, 28), "NMDC.NS", "ADANIPORTS.NS", dt.date(2015, 8, 12),
        "semi_annual", "Economic Times 2015-08-12 (IISL statement today)",
    ),
    Announcement(
        dt.date(2016, 4, 1), "CAIRN.NS", "AUROPHARMA.NS", dt.date(2016, 2, 23),
        "semi_annual", "Economic Times 2016-02-23 (IISL periodic review)",
    ),
    Announcement(
        dt.date(2016, 4, 1), "PNB.NS", "INFRATEL.NS", dt.date(2016, 2, 23),
        "semi_annual", "Economic Times 2016-02-23 (IISL periodic review)",
    ),
    Announcement(
        dt.date(2016, 4, 1), "VEDL.NS", "EICHERMOT.NS", dt.date(2016, 2, 23),
        "semi_annual", "Economic Times 2016-02-23 (IISL periodic review)",
    ),
    Announcement(
        dt.date(2017, 3, 31), "BHEL.NS", "IBULHSGFIN.NS", dt.date(2017, 2, 16),
        "semi_annual", "Business Standard 2017-02-16",
    ),
    Announcement(
        dt.date(2017, 3, 31), "IDEA.NS", "IOC.NS", dt.date(2017, 2, 16),
        "semi_annual", "Business Standard 2017-02-16",
    ),
    Announcement(
        dt.date(2017, 5, 26), "GRASIM.NS", "VEDL.NS", dt.date(2017, 5, 25),
        "ad_hoc", "Hindu Business Line 2017-05-25 (short-notice demerger print)",
    ),
    Announcement(
        dt.date(2017, 9, 29), "ACC.NS", "BAJFINANCE.NS", dt.date(2017, 8, 30),
        "semi_annual", "Business Today 2017-08-30 (IISL periodic review)",
    ),
    Announcement(
        dt.date(2017, 9, 29), "BANKBARODA.NS", "HINDPETRO.NS", dt.date(2017, 8, 30),
        "semi_annual", "Business Today 2017-08-30 (IISL periodic review)",
    ),
    Announcement(
        dt.date(2017, 9, 29), "TATAPOWER.NS", "UPL.NS", dt.date(2017, 8, 30),
        "semi_annual", "Business Today 2017-08-30 (IISL periodic review)",
    ),
    Announcement(
        dt.date(2018, 4, 2), "AMBUJACEM.NS", "BAJAJFINSV.NS", dt.date(2018, 2, 22),
        "semi_annual", "Moneycontrol 2018-02-22 (IISL PR)",
    ),
    Announcement(
        dt.date(2018, 4, 2), "AUROPHARMA.NS", "GRASIM.NS", dt.date(2018, 2, 22),
        "semi_annual", "Moneycontrol 2018-02-22 (IISL PR)",
    ),
    Announcement(
        dt.date(2018, 4, 2), "BOSCHLTD.NS", "TITAN.NS", dt.date(2018, 2, 22),
        "semi_annual", "Moneycontrol 2018-02-22 (IISL PR)",
    ),
    Announcement(
        dt.date(2018, 9, 28), "LUPIN.NS", "JSWSTEEL.NS", dt.date(2018, 8, 29),
        "semi_annual", "Business Standard 2018-08-29",
    ),
    Announcement(
        dt.date(2019, 3, 29), "HINDPETRO.NS", "BRITANNIA.NS", dt.date(2019, 2, 25),
        "semi_annual", "Mint 2019-02-25",
    ),
    Announcement(
        dt.date(2019, 9, 27), "IBULHSGFIN.NS", "NESTLEIND.NS", dt.date(2019, 8, 28),
        "semi_annual", "Mint 2019-08-28",
    ),
    Announcement(
        dt.date(2020, 3, 19), "YESBANK.NS", "SHREECEM.NS", dt.date(2020, 3, 16),
        "ad_hoc", "Mint 2020-03-16 (reconstruction scheme)",
    ),
    Announcement(
        dt.date(2020, 7, 31), "VEDL.NS", "HDFCLIFE.NS", dt.date(2020, 7, 2),
        "ad_hoc", "Economic Times 2020-07-02 (delisting replacement)",
    ),
    Announcement(
        dt.date(2020, 9, 25), "ZEEL.NS", "SBILIFE.NS", dt.date(2020, 8, 20),
        "semi_annual", "NSE Indices PR 2020-08-20 (NSE/FAOP/45434)",
    ),
    Announcement(
        dt.date(2020, 9, 25), "INFRATEL.NS", "DIVISLAB.NS", dt.date(2020, 8, 20),
        "semi_annual", "NSE Indices PR 2020-08-20 (NSE/FAOP/45434)",
    ),
    Announcement(
        dt.date(2021, 3, 31), "GAIL.NS", "TATACONSUM.NS", dt.date(2021, 2, 23),
        "semi_annual", "Economic Times 2021-02-23 (IMSC Tuesday)",
    ),
    Announcement(
        dt.date(2022, 3, 31), "IOC.NS", "APOLLOHOSP.NS", dt.date(2022, 2, 24),
        "semi_annual", "NSE Indices PR 2022-02-24 (NSE/FAOP/51430)",
    ),
    Announcement(
        dt.date(2022, 9, 30), "SHREECEM.NS", "ADANIENT.NS", dt.date(2022, 9, 1),
        "semi_annual", "NSE Indices PR 2022-09-01 (NSE/FAOP/53512)",
    ),
    Announcement(
        dt.date(2023, 7, 13), "HDFC.NS", "LTM.NS", dt.date(2023, 7, 4),
        "ad_hoc", "Times of India 2023-07-04 (merger replacement)",
    ),
    Announcement(
        dt.date(2024, 3, 28), "UPL.NS", "SHRIRAMFIN.NS", dt.date(2024, 2, 28),
        "semi_annual", "NSE Indices PR 2024-02-28",
    ),
    Announcement(
        dt.date(2024, 9, 30), "DIVISLAB.NS", "BEL.NS", dt.date(2024, 8, 23),
        "semi_annual", "NSE Indices PR 2024-08-23",
    ),
    Announcement(
        dt.date(2024, 9, 30), "LTM.NS", "TRENT.NS", dt.date(2024, 8, 23),
        "semi_annual", "NSE Indices PR 2024-08-23",
    ),
    Announcement(
        dt.date(2025, 3, 28), "BPCL.NS", "JIOFIN.NS", dt.date(2025, 2, 21),
        "semi_annual", "BusinessLine 2025-02-21",
    ),
    Announcement(
        dt.date(2025, 3, 28), "BRITANNIA.NS", "ETERNAL.NS", dt.date(2025, 2, 21),
        "semi_annual", "BusinessLine 2025-02-21",
    ),
    Announcement(
        dt.date(2025, 9, 30), "HEROMOTOCO.NS", "INDIGO.NS", dt.date(2025, 8, 22),
        "semi_annual", "NSE Indices PR 2025-08-22",
    ),
    Announcement(
        dt.date(2025, 9, 30), "INDUSINDBK.NS", "MAXHEALTH.NS", dt.date(2025, 8, 22),
        "semi_annual", "NSE Indices PR 2025-08-22",
    ),
)


def _match_key(effective: dt.date, excluded: str, included: str) -> tuple:
    return (effective, excluded, included)


def attach_announcement_dates(events: pl.DataFrame) -> pl.DataFrame:
    """Join recovered announcement dates onto PIT difference events."""
    rows: list[dict] = []
    for event in events.iter_rows(named=True):
        matched: Announcement | None = None
        for a in ANNOUNCEMENTS:
            delta = abs((event["effective_date"] - a.ledger_effective).days)
            if delta > 7:
                continue
            if event["event_type"] == "addition" and event["symbol"] == a.included:
                matched = a
                break
            if event["event_type"] == "deletion" and event["symbol"] == a.excluded:
                matched = a
                break
        out = dict(event)
        if matched is None:
            out["announcement_date"] = None
            out["announcement_date_status"] = "unmatched"
            out["announcement_kind"] = None
            out["announcement_source"] = None
        else:
            out["announcement_date"] = matched.announcement_date
            out["announcement_date_status"] = "recovered_free"
            out["announcement_kind"] = matched.kind
            out["announcement_source"] = matched.source
        rows.append(out)
    return pl.DataFrame(rows).with_columns(pl.col("announcement_date").cast(pl.Date))


def ledger_covers_replacements() -> bool:
    keys = {_match_key(e, x, i) for e, x, i in REPLACEMENTS}
    have = {_match_key(a.ledger_effective, a.excluded, a.included) for a in ANNOUNCEMENTS}
    return keys == have
