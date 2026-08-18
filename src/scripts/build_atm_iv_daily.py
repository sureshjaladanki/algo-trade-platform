"""Build ``data/GOLDEN_IV/atm_iv_daily.parquet`` from NSE FO bhavcopies (M9-0).

Downloads zips into ``data/GOLDEN_IV/raw/`` (gitignored via ``data/``) and
inverts near-month ATM Black-Scholes IV using FUTSTK settle as spot.

    poetry run python -m src.scripts.build_atm_iv_daily
    poetry run python -m src.scripts.build_atm_iv_daily --start 2018-01-02 --end 2018-01-31
    poetry run python -m src.scripts.build_atm_iv_daily --from-raw-only
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import zipfile
from pathlib import Path

import polars as pl

from src.horizon.m9.bhavcopy_iv import (
    extract_atm_iv_rows,
    extract_near_month_straddles,
    load_trade_symbols,
)
from src.horizon.m9.iv_store import DEFAULT_IV_PATH
from src.horizon.m9.nse_bhavcopy import (
    bhavcopy_filename,
    build_opener,
    download_fo_bhavcopy,
    iter_weekdays,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = REPO_ROOT / "data" / "GOLDEN_IV" / "raw"
DEFAULT_CONFIG = REPO_ROOT / "config" / "market_sectoral_symbols.yml"


def read_fo_bhavcopy(path: Path) -> pl.DataFrame:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
            payload = zf.read(csv_name)
        return pl.read_csv(io.BytesIO(payload), infer_schema_length=None)
    return pl.read_csv(path, infer_schema_length=None)


def _parse_iso(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=_parse_iso, default=dt.date(2015, 1, 1))
    parser.add_argument("--end", type=_parse_iso, default=dt.date(2019, 12, 31))
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / DEFAULT_IV_PATH)
    parser.add_argument(
        "--marks-out",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN_IV" / "option_marks_daily.parquet",
    )
    parser.add_argument(
        "--merge-into",
        type=Path,
        default=None,
        help="If set, diagonal-concat this build onto an existing IV parquet.",
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--from-raw-only",
        action="store_true",
        help="Do not download; rebuild parquet from zips already in raw-dir",
    )
    parser.add_argument("--skip-existing", action="store_true", default=True)
    parser.add_argument("--max-days", type=int, default=0)
    args = parser.parse_args()

    symbols = load_trade_symbols(args.config)
    universe = pl.DataFrame({"symbol": symbols})
    print(
        f"M9-0 ATM IV build {args.start} -> {args.end} "
        f"symbols={len(symbols)} out={args.out} (spot=FUTSTK settle)"
    )

    opener = None if args.from_raw_only else build_opener()
    chunks: list[pl.DataFrame] = []
    mark_chunks: list[pl.DataFrame] = []
    n_ok = n_skip = n_miss = 0
    days = list(iter_weekdays(args.start, args.end))
    if args.max_days > 0:
        days = days[: args.max_days]

    for i, day in enumerate(days, start=1):
        zip_path = args.raw_dir / bhavcopy_filename(day)
        if args.from_raw_only:
            path = zip_path if zip_path.exists() else None
        else:
            path = download_fo_bhavcopy(
                day,
                args.raw_dir,
                opener=opener,
                skip_existing=args.skip_existing,
            )
        n_names = 0
        if path is None:
            n_miss += 1
        else:
            fo = read_fo_bhavcopy(path)
            part = extract_atm_iv_rows(fo, universe, session_date=day)
            n_names = part.height
            if part.height:
                chunks.append(part)
                n_ok += 1
            else:
                n_skip += 1
            marks = extract_near_month_straddles(fo, universe, session_date=day)
            if marks.height:
                mark_chunks.append(marks)
        if i % 50 == 0 or i == len(days):
            print(
                f"   {i}/{len(days)} day={day} names={n_names} "
                f"ok={n_ok} skip={n_skip} miss={n_miss}",
                flush=True,
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    if not chunks:
        print("ERROR: no ATM IV rows produced")
        raise SystemExit(1)
    out = pl.concat(chunks).unique(["symbol", "date_only"]).sort(["symbol", "date_only"])
    out.write_parquet(args.out)
    print(f"wrote {args.out} rows={out.height} sessions={out['date_only'].n_unique()}")
    if mark_chunks:
        marks_out = pl.concat(mark_chunks).unique(
            ["symbol", "date_only", "expiry", "strike"]
        ).sort(["symbol", "date_only", "strike"])
        args.marks_out.parent.mkdir(parents=True, exist_ok=True)
        marks_out.write_parquet(args.marks_out)
        print(
            f"wrote {args.marks_out} rows={marks_out.height} "
            f"sessions={marks_out['date_only'].n_unique()}"
        )
    if args.merge_into is not None:
        prior = pl.read_parquet(args.merge_into)
        merged = (
            pl.concat([prior, out], how="diagonal")
            .unique(["symbol", "date_only"])
            .sort(["symbol", "date_only"])
        )
        merged.write_parquet(args.merge_into)
        print(
            f"merged into {args.merge_into} rows={merged.height} "
            f"sessions={merged['date_only'].n_unique()}"
        )


if __name__ == "__main__":
    main()
