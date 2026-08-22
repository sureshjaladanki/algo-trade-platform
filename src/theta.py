"""ThetaData FREE client for A0.5. Official Python library; no local terminal."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from thetadata import ThetaClient
from thetadata.errors import AuthenticationError, NoDataFoundError

REPO_ROOT = Path(__file__).resolve().parent.parent
THETA_CACHE = REPO_ROOT / "data" / "raw" / "theta"
REQUEST_GAP_SECONDS = 3.1
ENV_KEY = "THETADATA_API_KEY"


class ThetaUnavailable(Exception):
    """ThetaData client could not authenticate or fetch."""


@dataclass(frozen=True)
class OptionQuote:
    expiry: date
    trade_date: date
    strike: float
    right: str
    bid: float
    ask: float
    close: float = 0.0

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0


def _yyyymmdd(day: date) -> str:
    return day.strftime("%Y%m%d")


def _as_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).replace("/", "-")[:10])


def _load_api_key() -> str:
    key = os.environ.get(ENV_KEY, "").strip().strip('"').strip("'")
    if key:
        return key
    path = REPO_ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{ENV_KEY}="):
                return stripped.split("=", 1)[1].strip().strip('"').strip("'")
    raise ThetaUnavailable(f"{ENV_KEY} is missing from .env")


_CLIENT: ThetaClient | None = None


def _client() -> ThetaClient:
    global _CLIENT
    if _CLIENT is None:
        key = _load_api_key()
        try:
            _CLIENT = ThetaClient(api_key=key, dataframe_type="polars")
        except AuthenticationError as exc:
            raise ThetaUnavailable("ThetaData authentication failed") from exc
        except Exception as exc:
            raise ThetaUnavailable("ThetaData client failed") from exc
    return _CLIENT


def quotes_from_records(records: list[dict]) -> list[OptionQuote]:
    out: list[OptionQuote] = []
    for row in records:
        bid = float(row["bid"] or 0.0)
        ask = float(row["ask"] or 0.0)
        if bid <= 0 or ask <= 0 or ask < bid:
            continue
        expiry = row["expiry"] if "expiry" in row else row["expiration"]
        out.append(
            OptionQuote(
                expiry=_as_date(expiry),
                trade_date=_as_date(row["trade_date"]),
                strike=float(row["strike"]),
                right=str(row["right"]).strip().upper()[:1],
                bid=bid,
                ask=ask,
                close=float(row.get("close") or 0.0),
            )
        )
    return out


def _quotes_from_frame(frame, *, trade_date: date) -> list[OptionQuote]:
    records = [
        {
            "expiry": row["expiration"],
            "trade_date": trade_date,
            "strike": row["strike"],
            "right": row["right"],
            "bid": row["bid"],
            "ask": row["ask"],
            "close": row.get("close") or 0.0,
        }
        for row in frame.to_dicts()
    ]
    return quotes_from_records(records)


def theta_available() -> bool:
    try:
        list_expirations("SPX")
    except ThetaUnavailable:
        return False
    return True


def list_expirations(root: str = "SPX") -> list[date]:
    try:
        frame = _client().option_list_expirations(symbol=root)
    except ThetaUnavailable:
        raise
    except AuthenticationError as exc:
        raise ThetaUnavailable("ThetaData authentication failed") from exc
    except NoDataFoundError as exc:
        raise ThetaUnavailable("ThetaData returned no SPX expirations") from exc
    except Exception as exc:
        raise ThetaUnavailable("ThetaData option_list_expirations failed") from exc
    time.sleep(REQUEST_GAP_SECONDS)
    days = sorted({_as_date(row["expiration"]) for row in frame.to_dicts()})
    if not days:
        raise ThetaUnavailable("ThetaData returned no SPX expirations")
    return days


def cache_path(root: str, expiry: date, trade_date: date, directory: Path = THETA_CACHE) -> Path:
    return directory / root / f"{_yyyymmdd(expiry)}_{_yyyymmdd(trade_date)}.json"


def bulk_eod(
    *,
    root: str,
    expiry: date,
    trade_date: date,
    directory: Path = THETA_CACHE,
) -> list[OptionQuote]:
    path = cache_path(root, expiry, trade_date, directory)
    if path.exists():
        records = json.loads(path.read_text(encoding="utf-8"))
        return quotes_from_records(records)
    try:
        frame = _client().option_history_eod(
            start_date=trade_date,
            end_date=trade_date,
            symbol=root,
            expiration=expiry,
            strike="*",
            right="put",
        )
    except NoDataFoundError:
        records: list[dict] = []
    except ThetaUnavailable:
        raise
    except AuthenticationError as exc:
        raise ThetaUnavailable("ThetaData authentication failed") from exc
    except Exception as exc:
        raise ThetaUnavailable("ThetaData option_history_eod failed") from exc
    else:
        quotes = _quotes_from_frame(frame, trade_date=trade_date)
        records = [
            {
                "expiry": quote.expiry.isoformat(),
                "trade_date": quote.trade_date.isoformat(),
                "strike": quote.strike,
                "right": quote.right,
                "bid": quote.bid,
                "ask": quote.ask,
                "close": quote.close,
            }
            for quote in quotes
        ]
    time.sleep(REQUEST_GAP_SECONDS)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records), encoding="utf-8")
    return quotes_from_records(records)


def puts_on_date(*, root: str, expiry: date, trade_date: date) -> list[OptionQuote]:
    return [
        quote
        for quote in bulk_eod(root=root, expiry=expiry, trade_date=trade_date)
        if quote.right == "P"
    ]
