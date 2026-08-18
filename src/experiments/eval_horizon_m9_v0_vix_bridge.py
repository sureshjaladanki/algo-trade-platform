"""M9 V0 — India VIX bridge (report-only). Not authority V1.

Regress realized remaining range on (VIX-implied remaining range, range_q50).
If range_q50 is already redundant vs index IV, Track A is in trouble before
single-name IV arrives. If it is incremental, that only motivates acquiring
single-name IV for authority V1 — it does not PASS Track A.

Charter: docs/next/horizon-m9-range-monetization-charter.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    remaining_session_range,
)
from src.horizon.m9.implied_range import (
    DEFAULT_RANGE_KAPPA,
    attach_vix_implied_range,
    daily_vix_from_1m,
)
from src.horizon.m9.v1_incremental import incremental_range_ols
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range
from src.utils.symbol_data import load_symbol_data

REPO_ROOT = Path(__file__).resolve().parents[2]


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _run_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    vix_path: Path,
    *,
    max_symbols: int,
    kappa: float,
) -> bool:
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(f"\n=== M9 V0 fold {fold} train={cfg['train_period']} test={cfg['test_period']} ===")

    stock, *_ = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=min(train_start, test_start),
        end_period=max(train_end, test_end),
    )
    stock = _select_symbols(stock, max_symbols)
    print(f"   symbols={stock['symbol'].n_unique()}")

    vix_1m = load_symbol_data(
        vix_path,
        start_period=min(train_start, test_start),
        end_period=max(train_end, test_end),
    )
    vix_daily = daily_vix_from_1m(vix_1m)

    panel = remaining_session_range(attach_opportunity_features(stock))
    panel = panel.filter(pl.col("bars_to_mis") > 0)
    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
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
    te = attach_vix_implied_range(te, vix_daily, kappa=kappa)

    res = incremental_range_ols(
        te["remaining_range"].to_numpy(),
        te["range_imp_vix"].to_numpy(),
        te["range_q50"].to_numpy(),
    )
    status = "INCREMENTAL" if res.passed else "NOT_INCREMENTAL"
    print(
        f"   V0 {status} n={res.n} R2={res.r2:.3f} "
        f"b_imp={res.coef_implied:+.3f} b_q50={res.coef_q50:+.3f} "
        f"t_q50={res.t_q50:+.2f} p={res.p_q50:.4g} ({res.note})"
    )
    print(
        "   note: V0 uses India VIX for all names — report-only; "
        "authority V1 requires single-name IV (M9-0)."
    )
    return res.passed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument(
        "--vix-path",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN" / "^INDIAVIX.csv",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--kappa", type=float, default=DEFAULT_RANGE_KAPPA)
    args = parser.parse_args()

    print(
        "M9 V0 India VIX bridge — report-only "
        f"(kappa={args.kappa}). Charter: docs/next/horizon-m9-range-monetization-charter.md"
    )
    if not args.vix_path.exists():
        print(f"ERROR: VIX file not found: {args.vix_path}")
        sys.exit(1)

    flags = [
        _run_fold(
            fold,
            args.data_dir,
            args.config,
            args.vix_path,
            max_symbols=args.max_symbols,
            kappa=args.kappa,
        )
        for fold in args.folds
    ]
    dual = all(flags) and len(flags) >= 2
    print(
        f"\nV0 dual-fold incremental={'YES' if dual else 'NO'} "
        f"(still not authority V1)."
    )
    # Report-only: never fail the process on V0 outcome.
    sys.exit(0)


if __name__ == "__main__":
    main()
