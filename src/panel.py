"""Point-in-time Indian daily panel from NSE/BSE bhavcopy, with CA spine and L6 close_method."""

from __future__ import annotations

import argparse
import io
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

import polars as pl

from src.fetch import CacheHit, cached_session_keys, fetch_bytes

UDDIFF_START = date(2024, 7, 8)
CAS_START = date(2026, 8, 3)
EQ_SERIES = {"EQ", "BE", "SM", "ST"}

_MONTH = (
    "JAN",
    "FEB",
    "MAR",
    "APR",
    "MAY",
    "JUN",
    "JUL",
    "AUG",
    "SEP",
    "OCT",
    "NOV",
    "DEC",
)


def cm_udiff_url(session: date) -> str:
    stamp = session.strftime("%Y%m%d")
    return f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{stamp}_F_0000.csv.zip"


def cm_legacy_url(session: date) -> str:
    mon = _MONTH[session.month - 1]
    name = f"cm{session.strftime('%d')}{mon}{session.year}bhav.csv.zip"
    return (
        f"https://nsearchives.nseindia.com/content/historical/EQUITIES/"
        f"{session.year}/{mon}/{name}"
    )


def fo_udiff_url(session: date) -> str:
    stamp = session.strftime("%Y%m%d")
    return f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{stamp}_F_0000.csv.zip"


def bse_udiff_url(session: date) -> str:
    stamp = session.strftime("%Y%m%d")
    return f"https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_{stamp}_F_0000.CSV"


def delivery_url(session: date) -> str:
    return (
        "https://nsearchives.nseindia.com/products/content/"
        f"sec_bhavdata_full_{session.strftime('%d%m%Y')}.csv"
    )


def _unzip_csv(payload: bytes) -> str:
    if payload[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            name = zf.namelist()[0]
            return zf.read(name).decode("utf-8", errors="replace")
    return payload.decode("utf-8", errors="replace")


def parse_cm_bhavcopy(payload: bytes, session: date) -> pl.DataFrame:
    text = _unzip_csv(payload)
    raw = pl.read_csv(io.StringIO(text), infer_schema_length=5000)
    cols = {c.lower(): c for c in raw.columns}
    if "tckrsymb" in cols:
        series_col = cols["sctysrs"]
        frame = raw.select(
            pl.lit(session).alias("session_date"),
            pl.col(cols["tckrsymb"]).cast(pl.Utf8).alias("symbol"),
            pl.col(cols["isin"]).cast(pl.Utf8).alias("isin"),
            pl.col(series_col).cast(pl.Utf8).alias("series"),
            pl.col(cols["clspric"]).cast(pl.Float64).alias("unadj_close"),
            pl.col(cols["ttltradgvol"]).cast(pl.Float64).alias("volume"),
            pl.col(cols["ttltrfval"]).cast(pl.Float64).alias("turnover"),
        )
    else:
        frame = raw.select(
            pl.lit(session).alias("session_date"),
            pl.col(cols["symbol"]).cast(pl.Utf8).alias("symbol"),
            pl.col(cols["isin"]).cast(pl.Utf8).alias("isin"),
            pl.col(cols["series"]).cast(pl.Utf8).alias("series"),
            pl.col(cols["close"]).cast(pl.Float64).alias("unadj_close"),
            pl.col(cols["tottrdqty"]).cast(pl.Float64).alias("volume"),
            pl.col(cols["tottrdval"]).cast(pl.Float64).alias("turnover"),
        )
    return frame.filter(pl.col("series").is_in(sorted(EQ_SERIES)))


def parse_delivery(payload: bytes, session: date) -> pl.DataFrame:
    text = payload.decode("utf-8", errors="replace")
    raw = pl.read_csv(io.StringIO(text), infer_schema_length=2000)
    cols = {c.strip().lower().replace(" ", "_"): c for c in raw.columns}
    sym = cols.get("symbol") or cols.get("tckrsymb")
    series = cols.get("series") or cols.get("sctysrs")
    deliv = None
    for key in ("deliverable_quantity", "delivery_qty", "deliv_qty", "deliveryqty"):
        if key in cols:
            deliv = cols[key]
            break
    if sym is None or deliv is None:
        return pl.DataFrame(
            schema={
                "session_date": pl.Date,
                "symbol": pl.Utf8,
                "series": pl.Utf8,
                "delivery_qty": pl.Float64,
            }
        )
    close_col = cols.get("close_price") or cols.get("close") or cols.get("clspric")
    frame = raw.select(
        pl.lit(session).alias("session_date"),
        pl.col(sym).cast(pl.Utf8).str.strip_chars().alias("symbol"),
        pl.col(series).cast(pl.Utf8).alias("series") if series else pl.lit("EQ").alias("series"),
        pl.col(deliv).cast(pl.Float64, strict=False).alias("delivery_qty"),
    )
    if close_col:
        frame = frame.with_columns(pl.col(close_col).cast(pl.Float64, strict=False).alias("_close"))
        frame = frame.with_columns(
            (pl.col("delivery_qty") * pl.col("_close")).alias("delivery_value")
        ).drop("_close")
    else:
        frame = frame.with_columns(pl.lit(None).cast(pl.Float64).alias("delivery_value"))
    return frame


def parse_fo_underlyings(payload: bytes) -> set[str]:
    if not payload:
        return set()
    text = _unzip_csv(payload)
    raw = pl.read_csv(io.StringIO(text), infer_schema_length=2000)
    cols = {c.lower(): c for c in raw.columns}
    for name in ("tckrsymb", "symbol", "undrlyg"):
        if name in cols:
            return set(raw.get_column(cols[name]).cast(pl.Utf8).unique().to_list())
    return set()


def load_corporate_actions(path: Path) -> pl.DataFrame:
    return pl.read_csv(path, try_parse_dates=True)


def apply_corporate_actions(bhav: pl.DataFrame, actions: pl.DataFrame) -> pl.DataFrame:
    """Keep unadjusted close; store factor and adj_close. Only CAs with ex_date <= session."""
    if actions.is_empty():
        return bhav.with_columns(
            pl.lit(1.0).alias("adjustment_factor"),
            pl.col("unadj_close").alias("adj_close"),
        )
    events = actions.with_columns(
        pl.when(pl.col("kind").is_in(["split", "bonus"]))
        .then(pl.col("ratio_den") / pl.col("ratio_num"))
        .when(pl.col("kind") == "demerger")
        .then(pl.col("factor"))
        .otherwise(pl.lit(1.0))
        .alias("event_factor")
    )
    keys = bhav.columns
    joined = bhav.join(events.select(["symbol", "ex_date", "event_factor"]), on="symbol", how="left")
    joined = joined.with_columns(
        pl.when(pl.col("ex_date").is_not_null() & (pl.col("ex_date") > pl.col("session_date")))
        .then(pl.col("event_factor").fill_null(1.0))
        .otherwise(1.0)
        .alias("event_factor")
    )
    out = joined.group_by(keys, maintain_order=True).agg(
        pl.col("event_factor").product().alias("adjustment_factor")
    )
    return out.with_columns((pl.col("unadj_close") * pl.col("adjustment_factor")).alias("adj_close"))


def attach_close_method(panel: pl.DataFrame, fno_by_date: dict[date, set[str]]) -> pl.DataFrame:
    if not fno_by_date:
        return panel.with_columns(pl.lit("vwap_30min").alias("close_method"))
    rows = [
        {"session_date": day, "symbol": symbol}
        for day, names in fno_by_date.items()
        for symbol in names
    ]
    fno = pl.DataFrame(rows).unique().with_columns(pl.lit(True).alias("fno_eligible"))
    out = panel.join(fno, on=["session_date", "symbol"], how="left")
    cas = (pl.col("session_date") >= pl.lit(CAS_START)) & pl.col("fno_eligible").fill_null(False)
    return out.with_columns(
        pl.when(cas).then(pl.lit("cas_auction")).otherwise(pl.lit("vwap_30min")).alias("close_method")
    ).drop("fno_eligible")


def attach_delivery_median(panel: pl.DataFrame, window: int = 20) -> pl.DataFrame:
    if "delivery_value" not in panel.columns:
        panel = panel.with_columns(pl.lit(None).cast(pl.Float64).alias("delivery_value"))
    return panel.sort(["symbol", "session_date"]).with_columns(
        pl.col("delivery_value")
        .rolling_median(window_size=window, min_samples=1)
        .over("symbol")
        .alias("delivery_value_median_20")
    )


def join_impact_cost(panel: pl.DataFrame, impact: pl.DataFrame) -> pl.DataFrame:
    if impact.is_empty():
        return panel.with_columns(pl.lit(None).cast(pl.Float64).alias("impact_cost_bps"))
    ic = impact.with_columns(pl.col("month").cast(pl.Utf8))
    return panel.with_columns(
        pl.col("session_date").dt.strftime("%Y-%m").alias("month")
    ).join(ic, on=["month", "symbol"], how="left").drop("month")


def load_impact_cost(path: Path) -> pl.DataFrame:
    if not path.exists():
        return pl.DataFrame(schema={"month": pl.Utf8, "symbol": pl.Utf8, "impact_cost_bps": pl.Float64})
    return pl.read_csv(path)


def derived_column_names() -> tuple[str, ...]:
    return ("adj_close", "delivery_value_median_20", "adjustment_factor", "close_method")


def demerger_holding_gap(panel: pl.DataFrame, parent: str, child: str, ex_date: date) -> float:
    pre = panel.filter((pl.col("symbol") == parent) & (pl.col("session_date") < ex_date)).sort(
        "session_date"
    )
    post_p = panel.filter((pl.col("symbol") == parent) & (pl.col("session_date") >= ex_date)).sort(
        "session_date"
    )
    post_c = panel.filter((pl.col("symbol") == child) & (pl.col("session_date") >= ex_date)).sort(
        "session_date"
    )
    pre_val = float(pre.get_column("unadj_close")[-1])
    post_val = float(post_p.get_column("unadj_close")[0]) + float(post_c.get_column("unadj_close")[0])
    return abs(post_val - pre_val) / pre_val


def close_method_month_counts(panel: pl.DataFrame) -> pl.DataFrame:
    return (
        panel.with_columns(pl.col("session_date").dt.strftime("%Y-%m").alias("month"))
        .group_by(["month", "close_method"])
        .len()
        .sort(["month", "close_method"])
    )


def fetch_cm_session(
    session: date,
    *,
    root: Path,
    clock: datetime | None = None,
    allow_network: bool = True,
) -> CacheHit:
    if session >= UDDIFF_START:
        url, key = cm_udiff_url(session), f"nse-cm-udiff:{session.isoformat()}"
    else:
        url, key = cm_legacy_url(session), f"nse-cm-legacy:{session.isoformat()}"
    return fetch_bytes(url, root=root, key=key, clock=clock, allow_network=allow_network)


def fetch_fo_session(
    session: date,
    *,
    root: Path,
    clock: datetime | None = None,
    allow_network: bool = True,
) -> CacheHit:
    url = fo_udiff_url(session)
    key = f"nse-fo-udiff:{session.isoformat()}"
    return fetch_bytes(url, root=root, key=key, clock=clock, allow_network=allow_network)


def fetch_delivery_session(
    session: date,
    *,
    root: Path,
    clock: datetime | None = None,
    allow_network: bool = True,
) -> CacheHit:
    return fetch_bytes(
        delivery_url(session),
        root=root,
        key=f"nse-delivery:{session.isoformat()}",
        clock=clock,
        allow_network=allow_network,
    )


def fetch_bse_session(
    session: date,
    *,
    root: Path,
    clock: datetime | None = None,
    allow_network: bool = True,
) -> CacheHit:
    return fetch_bytes(
        bse_udiff_url(session),
        root=root,
        key=f"bse-cm-udiff:{session.isoformat()}",
        clock=clock,
        allow_network=allow_network,
    )


def build_panel(
    sessions: list[date],
    *,
    root: Path,
    actions: pl.DataFrame,
    impact: pl.DataFrame,
    fno_by_date: dict[date, set[str]] | None = None,
    delivery_by_date: dict[date, pl.DataFrame] | None = None,
    allow_network: bool = False,
    clock: datetime | None = None,
) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    fno_map = dict(fno_by_date or {})
    for session in sessions:
        hit = fetch_cm_session(session, root=root, clock=clock, allow_network=allow_network)
        if hit is None or hit.missing or not hit.payload:
            continue
        day = parse_cm_bhavcopy(hit.payload, session)
        if delivery_by_date and session in delivery_by_date:
            day = day.join(
                delivery_by_date[session].select(["symbol", "series", "delivery_value"]),
                on=["symbol", "series"],
                how="left",
            )
        frames.append(day)
    if not frames:
        return pl.DataFrame()
    panel = pl.concat(frames, how="diagonal_relaxed")
    panel = apply_corporate_actions(panel, actions)
    panel = attach_close_method(panel, fno_map)
    panel = attach_delivery_median(panel)
    return join_impact_cost(panel, impact)


def cached_cm_sessions(root: Path) -> list[date]:
    keys = cached_session_keys(root, "nse-cm-")
    out = []
    for key in keys:
        out.append(date.fromisoformat(key.split(":", 1)[1]))
    return sorted(set(out))


def weekdays(start: date, end: date) -> list[date]:
    days = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:
            days.append(cur)
        cur += timedelta(days=1)
    return days


def backfill_cm(
    start: date,
    end: date,
    *,
    root: Path,
    clock: datetime | None = None,
) -> int:
    stored = 0
    for session in weekdays(start, end):
        hit = fetch_cm_session(session, root=root, clock=clock, allow_network=True)
        if hit is not None and not hit.missing and hit.payload:
            stored += 1
    return stored


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["backfill", "count"])
    parser.add_argument("--start", default="2006-01-02")
    parser.add_argument("--end", default="2026-09-04")
    parser.add_argument("--root", default="data")
    args = parser.parse_args()
    root = Path(args.root)
    if args.command == "count":
        print(len(cached_cm_sessions(root)))
        return
    n = backfill_cm(date.fromisoformat(args.start), date.fromisoformat(args.end), root=root)
    print(n)


if __name__ == "__main__":
    main()
