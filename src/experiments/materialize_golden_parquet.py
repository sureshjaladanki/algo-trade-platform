"""M0 — materialize data/GOLDEN CSV → Parquet (CSV remains SoT until validated)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.horizon.fresh.parquet_store import (
    DEFAULT_CSV_DIR,
    DEFAULT_PARQUET_DIR,
    materialize_golden,
    smoke_round_trip,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=REPO_ROOT / DEFAULT_CSV_DIR,
    )
    parser.add_argument(
        "--parquet-dir",
        type=Path,
        default=REPO_ROOT / DEFAULT_PARQUET_DIR,
    )
    parser.add_argument(
        "--smoke-symbol",
        type=str,
        default="ABB.NS",
        help="Symbol for row-count round-trip smoke (also run first).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Materialize every GOLDEN CSV (slow; default is smoke only).",
    )
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=None,
        help="Optional symbol list (e.g. ABB.NS RELIANCE.NS).",
    )
    args = parser.parse_args()

    print(f"Smoke round-trip: {args.smoke_symbol}")
    smoke = smoke_round_trip(
        args.smoke_symbol,
        csv_dir=args.csv_dir,
        parquet_dir=args.parquet_dir,
    )
    print(
        f"  OK {smoke.symbol} csv_rows={smoke.csv_rows} "
        f"parquet_rows={smoke.parquet_rows} -> {smoke.parquet_path}"
    )

    if args.all or args.symbols:
        symbols = None if args.all else args.symbols
        results = materialize_golden(
            args.csv_dir, args.parquet_dir, symbols=symbols
        )
        bad = [r for r in results if not r.ok]
        print(f"Materialized {len(results)} symbols; mismatches={len(bad)}")
        for r in bad[:10]:
            print(f"  FAIL {r.symbol}: csv={r.csv_rows} parquet={r.parquet_rows}")
        if bad:
            sys.exit(1)
    print("Done.")


if __name__ == "__main__":
    main()
