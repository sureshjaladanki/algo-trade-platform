"""NSE monthly Market Cap / Weightage / Beta files (Nifty 50 and Next 50)."""

from __future__ import annotations

import calendar
import datetime as dt
import io
import ssl
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import polars as pl

from src.events.membership import ALIASES
from src.events.paths import DERIVED_DIR, MCWB_MONTHLY_PARQUET, MCWB_RAW_DIR

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_CTX = ssl.create_default_context()
_ARCHIVE = "https://nsearchives.nseindia.com/content/indices/"
_MONTH_TOKEN = (
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
)

# Contemporaneous NSE symbols -> ledger `.NS` names used by REPLACEMENTS.
_SYMBOL_ALIASES: dict[str, str] = {
    "TATAMOTORS": "TMPV.NS",
    "MCDOWELL-N": "UNITDSPR.NS",
    "ZOMATO": "ETERNAL.NS",
    "MINDTREE": "LTM.NS",
    "LTIM": "LTM.NS",
    "LTIMINDTREE": "LTM.NS",
    "SRTRANSFIN": "SHRIRAMFIN.NS",
    "MOTHERSUMI": "MOTHERSON.NS",
    "CADILAHC": "ZYDUSLIFE.NS",
    **{canon.replace(".NS", ""): canon for canon in ALIASES.values()},
    **{alias.replace(".NS", ""): canon for alias, canon in ALIASES.items()},
}

_SCHEMA = {
    "year": pl.Int32,
    "month": pl.Int32,
    "as_of": pl.Date,
    "family": pl.String,
    "nse_symbol": pl.String,
    "symbol": pl.String,
    "ff_mcap_cr": pl.Float64,
    "impact_cost_pct": pl.Float64,
}


def mcwb_zip_name(year: int, month: int) -> str:
    return f"mcwb_{_MONTH_TOKEN[month - 1]}{year % 100:02d}.zip"


def to_ledger_symbol(nse_symbol: str) -> str:
    token = nse_symbol.strip().upper().removesuffix(".NS")
    return _SYMBOL_ALIASES.get(token, f"{token}.NS")


def zip_url(year: int, month: int) -> str:
    return _ARCHIVE + mcwb_zip_name(year, month)


def download_mcwb_zip(year: int, month: int, dest_dir: Path = MCWB_RAW_DIR) -> Path | None:
    """Fetch one monthly zip. Skip if already present. None if the archive has no file."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / mcwb_zip_name(year, month)
    if path.exists() and path.stat().st_size > 4 and path.read_bytes()[:2] == b"PK":
        return path
    req = urllib.request.Request(
        zip_url(year, month),
        headers={
            "User-Agent": _UA,
            "Accept": "*/*",
            "Referer": "https://www.nseindia.com/all-reports",
        },
    )
    try:
        with urllib.request.urlopen(req, context=_CTX, timeout=60) as resp:
            blob = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    if blob[:2] != b"PK":
        raise ValueError(f"{path.name} is not a zip")
    path.write_bytes(blob)
    return path


def _index_family(member: str) -> str:
    name = member.lower().replace("\\", "/").rsplit("/", 1)[-1]
    if "next50" in name or "jrnifty" in name or "junior" in name:
        return "next_50"
    if "nifty50" in name or name == "niftymcwb.csv":
        return "nifty_50"
    raise ValueError(f"unrecognised MCWB member {member}")


def _header_index(text: str) -> int:
    for i, line in enumerate(text.splitlines()):
        low = line.lower()
        if "security symbol" not in low:
            continue
        if "free float" in low or "index market capitalisation" in low:
            return i
    raise ValueError("MCWB CSV has no Security Symbol / market-cap header")


def _ff_column(columns: list[str]) -> str:
    try:
        return _find_column(columns, "free float")
    except ValueError:
        return _find_column(columns, "index market capitalisation")


def _find_column(columns: list[str], *needles: str) -> str:
    for col in columns:
        low = " ".join(col.lower().split())
        if all(n in low for n in needles):
            return col
    raise ValueError(f"missing column {needles} in {columns}")


def parse_mcwb_csv(text: str, family: str, year: int, month: int) -> pl.DataFrame:
    """Parse one annexure CSV. Month comes from the zip name, not the title."""
    skip = _header_index(text)
    raw = pl.read_csv(io.StringIO(text), skip_rows=skip, infer_schema_length=200)
    raw = raw.rename({c: c.strip() for c in raw.columns})
    symbol_col = _find_column(raw.columns, "security symbol")
    ff_col = _ff_column(raw.columns)
    ic_col = _find_column(raw.columns, "impact cost")
    last_day = calendar.monthrange(year, month)[1]
    as_of = dt.date(year, month, last_day)
    parsed = raw.select(
        nse_symbol=pl.col(symbol_col).cast(pl.String).str.strip_chars(),
        ff_mcap_cr=pl.col(ff_col).cast(pl.Float64, strict=False),
        impact_cost_pct=pl.col(ic_col).cast(pl.Float64, strict=False),
    ).filter(pl.col("nse_symbol").is_not_null() & (pl.col("nse_symbol") != ""))
    return parsed.with_columns(
        year=pl.lit(year).cast(pl.Int32),
        month=pl.lit(month).cast(pl.Int32),
        as_of=pl.lit(as_of),
        family=pl.lit(family),
        symbol=pl.col("nse_symbol").map_elements(to_ledger_symbol, return_dtype=pl.String),
    ).select(list(_SCHEMA))


def parse_mcwb_zip(blob: bytes, year: int, month: int) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        for member in zf.namelist():
            if member.endswith("/"):
                continue
            family = _index_family(member)
            text = zf.read(member).decode("latin-1")
            try:
                frames.append(parse_mcwb_csv(text, family, year, month))
            except ValueError as exc:
                raise ValueError(f"{year}-{month:02d} {member}: {exc}") from exc
    if not frames:
        raise ValueError(f"empty MCWB zip for {year}-{month:02d}")
    return pl.concat(frames, how="vertical")


def month_span(start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
    year, month = start
    out: list[tuple[int, int]] = []
    while (year, month) <= end:
        out.append((year, month))
        month += 1
        if month == 13:
            year += 1
            month = 1
    return out


def build_mcwb_panel(
    dest_dir: Path = MCWB_RAW_DIR,
    *,
    start: tuple[int, int] = (2014, 8),
    end: tuple[int, int] = (2025, 12),
    pause_s: float = 0.05,
) -> pl.DataFrame:
    """Download monthly zips and stack Nifty 50 + Next 50 free-float rows."""
    frames: list[pl.DataFrame] = []
    missing: list[str] = []
    for year, month in month_span(start, end):
        path = download_mcwb_zip(year, month, dest_dir)
        time.sleep(pause_s)
        if path is None:
            missing.append(f"{year}-{month:02d}")
            continue
        frames.append(parse_mcwb_zip(path.read_bytes(), year, month))
    if not frames:
        raise ValueError("no MCWB months downloaded")
    panel = pl.concat(frames, how="vertical")
    if missing:
        print("MCWB months missing from archive: " + ", ".join(missing))
    return panel


def load_or_build_mcwb_panel(parquet: Path = MCWB_MONTHLY_PARQUET) -> pl.DataFrame:
    if parquet.exists():
        return pl.read_parquet(parquet)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    panel = build_mcwb_panel()
    parquet.parent.mkdir(parents=True, exist_ok=True)
    panel.write_parquet(parquet)
    return panel


def main() -> None:
    panel = load_or_build_mcwb_panel()
    print(
        f"wrote {MCWB_MONTHLY_PARQUET} rows={panel.height} "
        f"months={panel.select('year', 'month').n_unique()} "
        f"symbols={panel['symbol'].n_unique()}"
    )


if __name__ == "__main__":
    main()
