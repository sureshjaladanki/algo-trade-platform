"""Successor S4-P1 — coverage of V2p-c sessions vs Nifty option snapshots.

Charter: docs/next/horizon-successor-s4-p1-index-marks-charter.md
Does not peek V2. Does not call eval_horizon_m9_v2_stub.

    poetry run python -m src.experiments.eval_horizon_successor_s4_p1_coverage --folds A B
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.experiments.eval_horizon_successor_s1_v2pc import _clock_panels
from src.horizon.m9.index_option_store import (
    COVERAGE_GATE,
    DEFAULT_SNAPSHOT_PATH,
    IndexOptionStoreMissingError,
    coverage_selected,
    load_nifty_option_snapshots,
    session_entry_exit,
)
from src.horizon.m9.v2p_range import fit_v2pc_scale, select_v2pc_sessions
from src.horizon.m9.zenodo_ltp import is_zenodo_last_trade

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--vix-path",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN" / "^INDIAVIX.csv",
    )
    parser.add_argument(
        "--snapshots",
        type=Path,
        default=REPO_ROOT / DEFAULT_SNAPSHOT_PATH,
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Last-trade companion: coverage does not earn quote V2.",
    )
    args = parser.parse_args()

    print(
        "Successor S4-P1 coverage - 09:45/15:15 Nifty snapshots vs V2p-c. "
        "Charter: docs/next/horizon-successor-s4-p1-index-marks-charter.md"
    )
    try:
        raw = load_nifty_option_snapshots(args.snapshots)
    except IndexOptionStoreMissingError as exc:
        print(f"S4-P1 NOT STARTED - {exc}")
        sys.exit(1)

    report_only = args.report_only or is_zenodo_last_trade(raw)
    if report_only:
        print(
            "Zenodo last-trade coverage - report-only. "
            "Prereg: docs/archive/horizon-successor-s1-v2-zenodo-preregistration.md. "
            "Quote S4-P1 is not started."
        )

    marks = session_entry_exit(raw)
    print(f"   snapshot_rows={raw.height} marked_sessions={marks.height}")
    any_thin = False
    for fold in args.folds:
        train_clock, test_clock = _clock_panels(fold, args.data_dir, args.vix_path)
        selected = select_v2pc_sessions(test_clock, fit_v2pc_scale(train_clock))
        cov = coverage_selected(selected["date_only"], marks)
        thin = cov["coverage"] < COVERAGE_GATE if cov["n"] else True
        any_thin = any_thin or thin
        print(
            f"   fold {fold} selected={cov['n']} marked={cov['n_marked']} "
            f"coverage={cov['coverage']:.1%} gate={COVERAGE_GATE:.0%} "
            f"{'PASS' if not thin else 'THIN'}"
        )
    if any_thin:
        if report_only:
            print(
                "Zenodo last-trade coverage THIN - report-only V2 is INCONCLUSIVE. "
                "Quote S4-P1 is not started."
            )
        else:
            print("S4-P1 coverage THIN - do not peek V2. Do not use EOD bhavcopy.")
        sys.exit(3)
    if report_only:
        print(
            "Zenodo last-trade coverage PASS - report-only V2 peek is allowed. "
            "Quote S4-P1 is not started."
        )
    else:
        print("S4-P1 coverage PASS - V2 peek is earned.")
    sys.exit(0)


if __name__ == "__main__":
    main()
