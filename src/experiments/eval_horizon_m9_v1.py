"""M9 V1 - incremental information of range_q50 over single-name ATM IV.

Blocked until M9-0 materialises ``data/GOLDEN_IV/atm_iv_daily.parquet``.
This is the authority Track A gate (not V0, not V1-index).

    poetry run python -m src.experiments.eval_horizon_m9_v1 --folds A
    poetry run python -m src.experiments.eval_horizon_m9_v1 --folds A B --max-symbols 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.fresh.folds import apply_purge_date_filter, fold_spec
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    remaining_session_range,
)
from src.horizon.m9.implied_range import DEFAULT_RANGE_KAPPA, attach_atm_implied_range
from src.horizon.m9.iv_store import (
    DEFAULT_IV_PATH,
    IvStoreMissingError,
    attach_lagged_atm_iv,
    coverage_report,
    load_atm_iv_daily,
)
from src.horizon.m9.v1_incremental import incremental_range_ols
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]
COVERAGE_GATE = 0.70


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _run_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    iv: pl.DataFrame,
    *,
    max_symbols: int,
    kappa: float,
) -> tuple[bool, pl.DataFrame]:
    spec = fold_spec(fold)
    train_start, train_end = parse_period_range(spec.train_period)
    test_start, test_end = parse_period_range(spec.test_period)
    print(
        f"\n=== M9 V1 fold {fold} train={spec.train_period} "
        f"test={spec.test_period} purge={spec.purge_calendar_days}d ==="
    )

    stock, *_ = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=min(train_start, test_start),
        end_period=max(train_end, test_end),
    )
    stock = _select_symbols(stock, max_symbols)
    print(f"   symbols={stock['symbol'].n_unique()}")

    panel = remaining_session_range(attach_opportunity_features(stock))
    panel = panel.filter(pl.col("bars_to_mis") > 0)
    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
    train_end_year = int(str(spec.train_period).split("-")[-1][:4])
    train = apply_purge_date_filter(
        train, train_end_year, spec.purge_calendar_days, datetime_col="date"
    )
    test = filter_by_period(panel, test_start, test_end, datetime_col="date")
    keep = [*OPPORTUNITY_FEATURES, "remaining_range"]
    finite = pl.all_horizontal([pl.col(c).is_finite() for c in keep])
    tr = train.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    te = test.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))

    model = OpportunityModel().fit(
        tr.select(list(OPPORTUNITY_FEATURES)).to_numpy(),
        tr["remaining_range"].to_numpy(),
    )
    q = model.predict_quantiles(te.select(list(OPPORTUNITY_FEATURES)).to_numpy())
    te = te.with_columns(range_q50=pl.Series(q["range_q50"]))
    te = attach_lagged_atm_iv(te, iv)
    cov = coverage_report(te)
    print(
        f"   IV coverage n={cov['n']} n_iv={cov['n_iv']} "
        f"coverage={cov['coverage']:.3f} (gate {COVERAGE_GATE:.0%})"
    )
    te = attach_atm_implied_range(te, kappa=kappa)
    res = incremental_range_ols(
        te["remaining_range"].to_numpy(),
        te["range_imp_atm"].to_numpy(),
        te["range_q50"].to_numpy(),
    )
    status = "PASS" if res.passed else "FAIL"
    if cov["coverage"] < COVERAGE_GATE:
        status = f"THIN/{status}"
    print(
        f"   V1 {status} n={res.n} R2={res.r2:.3f} "
        f"b_imp={res.coef_implied:+.3f} b_q50={res.coef_q50:+.3f} "
        f"t_q50={res.t_q50:+.2f} p={res.p_q50:.4g} ({res.note})"
    )
    passed = bool(res.passed and cov["coverage"] >= COVERAGE_GATE)
    return passed, te


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--iv-path", type=Path, default=REPO_ROOT / DEFAULT_IV_PATH)
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--kappa", type=float, default=DEFAULT_RANGE_KAPPA)
    args = parser.parse_args()

    print(
        "M9 V1 single-name ATM IV incremental-information gate. "
        "Charter: docs/next/horizon-m9-range-monetization-charter.md"
    )
    try:
        iv = load_atm_iv_daily(args.iv_path)
    except IvStoreMissingError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    flags = [
        _run_fold(
            fold,
            args.data_dir,
            args.config,
            iv,
            max_symbols=args.max_symbols,
            kappa=args.kappa,
        )[0]
        for fold in args.folds
    ]
    dual = all(flags) and len(flags) >= 2
    print(f"\nV1 dual-fold={'PASS' if dual else 'FAIL'}")
    if dual:
        sys.exit(0)
    sys.exit(2)


if __name__ == "__main__":
    main()
