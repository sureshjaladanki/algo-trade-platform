"""Ingest Zenodo Nifty 1m last-trades into the report-only snapshot parquet.

Does not write ``data/GOLDEN_IV/nifty_option_snapshots.parquet`` (quote store).

    poetry run python -m src.scripts.build_nifty_option_snapshots_zenodo
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.horizon.m9.zenodo_ltp import (
    DEFAULT_ZENODO_SNAPSHOT_PATH,
    DEFAULT_ZENODO_ZIP,
    SOURCE_ID,
    build_zenodo_snapshots,
    load_golden_clock_spots,
    load_zenodo_clock_ticks,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zip-path",
        type=Path,
        default=REPO_ROOT / DEFAULT_ZENODO_ZIP,
    )
    parser.add_argument(
        "--nsei-path",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN" / "^NSEI.csv",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / DEFAULT_ZENODO_SNAPSHOT_PATH,
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2018, 2019])
    args = parser.parse_args()

    print(
        f"Zenodo last-trade ingest source={SOURCE_ID} "
        f"years={args.years}. Report-only; not the S4-P1 quote store."
    )
    ticks = load_zenodo_clock_ticks(args.zip_path, years=tuple(args.years))
    print(f"   clock_ticks={ticks.height} sessions={ticks['date_only'].n_unique()}")
    spots = load_golden_clock_spots(args.nsei_path)
    print(f"   golden_clocks={spots.height} sessions={spots['date_only'].n_unique()}")
    snapshots = build_zenodo_snapshots(ticks, spots)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    snapshots.write_parquet(args.out)
    n_sess = snapshots["date_only"].n_unique()
    print(
        f"wrote {args.out} rows={snapshots.height} sessions={n_sess} "
        f"source={SOURCE_ID}"
    )


if __name__ == "__main__":
    main()
