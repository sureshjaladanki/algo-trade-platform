"""M9-0 coverage of daily ATM IV vs GOLDEN trade-symbol sessions (folds A/B).

    poetry run python -m src.experiments.eval_horizon_m9_0_coverage --folds A B
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path


from src.horizon.fresh.folds import FOLDS
from src.horizon.m9.bhavcopy_iv import load_golden_daily_closes, load_trade_symbols
from src.horizon.m9.iv_store import (
    DEFAULT_IV_PATH,
    IvStoreMissingError,
    attach_lagged_atm_iv,
    coverage_report,
    load_atm_iv_daily,
)
from src.utils.date import parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]
COVERAGE_GATE = 0.70


def _year_bounds(period: str) -> tuple:
    start, end = parse_period_range(period)

    def _bound(token: str, *, end_of_year: bool) -> dt.date:
        if "/" in token:
            month, year = token.split("/")
            y, m = int(year), int(month)
            if end_of_year:
                return dt.date(y, m, 28)
            return dt.date(y, m, 1)
        y = int(token)
        return dt.date(y, 12, 31) if end_of_year else dt.date(y, 1, 1)

    return _bound(start, end_of_year=False), _bound(end, end_of_year=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iv-path", type=Path, default=REPO_ROOT / DEFAULT_IV_PATH)
    parser.add_argument(
        "--parquet-dir",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN_PARQUET",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    args = parser.parse_args()

    print("M9-0 IV coverage vs GOLDEN (symbol, session) cells")
    try:
        iv = load_atm_iv_daily(args.iv_path)
    except IvStoreMissingError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    symbols = load_trade_symbols(args.config)
    print(f"   iv_rows={iv.height} iv_sessions={iv['date_only'].n_unique()} names={len(symbols)}")

    thin = False
    for fold in args.folds:
        test_period = FOLDS[fold]["test_period"]
        start, end = _year_bounds(test_period)
        panel = load_golden_daily_closes(symbols, args.parquet_dir, start, end).rename(
            {"close": "underlying_close"}
        )
        joined = attach_lagged_atm_iv(panel, iv)
        cov = coverage_report(joined)
        flag = "PASS" if cov["coverage"] >= COVERAGE_GATE else "THIN"
        if flag == "THIN":
            thin = True
        print(
            f"   fold {fold} test={test_period} {flag} "
            f"n={cov['n']} n_iv={cov['n_iv']} coverage={cov['coverage']:.3f} "
            f"(gate {COVERAGE_GATE:.0%})"
        )

    if thin:
        print("Coverage below 70% on at least one fold - V1 stays report-only.")
        sys.exit(0)
    print("Coverage gate met - V1 authority peek is eligible after pre-registration.")
    sys.exit(0)


if __name__ == "__main__":
    main()
