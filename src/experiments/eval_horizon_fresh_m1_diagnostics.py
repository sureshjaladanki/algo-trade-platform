"""M1 — fresh Horizon truth diagnostics (selection ceiling, spread, abs vs excess).

Report-only. Does not train or ship models. Production Top-K path untouched.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.fresh.diagnostics import (
    format_ceiling_report,
    production_long_eligible_mask,
    selection_ceiling,
)
from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.microstructure import attach_spread_panel
from src.labels.fresh_barrier import (
    PROD_LONG_GEOMETRY,
    absolute_excess_sign_disagreement,
    calculate_fresh_long_labels,
)
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]


def _diagnose_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    *,
    max_symbols: int | None,
    n_boot: int,
    seed: int,
) -> str:
    cfg = FOLDS[fold]
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(f"\n=== Fold {fold}  test={cfg['test_period']} ===")
    stock_15m, nifty_15m, _sector, _daily, _dn = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=test_start,
        end_period=test_end,
    )
    if max_symbols is not None:
        syms = sorted(stock_15m["symbol"].unique().to_list())[:max_symbols]
        stock_15m = stock_15m.filter(pl.col("symbol").is_in(syms))
        print(f"   symbol subset n={len(syms)}")

    test_stock = filter_by_period(stock_15m, test_start, test_end, datetime_col="date")
    test_nifty = filter_by_period(nifty_15m, test_start, test_end, datetime_col="date")
    print(f"   rows={test_stock.height}")
    if test_stock.height == 0:
        return f"fold {fold}: empty"

    labeled = calculate_fresh_long_labels(
        test_stock, test_nifty, PROD_LONG_GEOMETRY
    )
    pool = labeled.filter(pl.all_horizontal(production_long_eligible_mask()))
    ceiling = selection_ceiling(
        pool, fold=fold, pool_name="prod_eligible_long", n_boot=n_boot, seed=seed
    )
    lines = [format_ceiling_report(ceiling)]

    disagree = absolute_excess_sign_disagreement(pool)
    lines.append(
        f"abs_vs_excess disagree_rate={disagree['disagree_rate']:.2%} "
        f"n={disagree['n']} n_disagree={disagree.get('n_disagree', 0)}"
    )

    # Spread panel on a sample of bars (median by price bucket).
    sample = test_stock.head(min(50_000, test_stock.height))
    spread = attach_spread_panel(sample)
    panel = (
        spread.with_columns(
            price_bucket=pl.when(pl.col("close") < 200)
            .then(pl.lit("<200"))
            .when(pl.col("close") < 500)
            .then(pl.lit("200-500"))
            .when(pl.col("close") < 2000)
            .then(pl.lit("500-2000"))
            .otherwise(pl.lit(">=2000")),
        )
        .group_by("price_bucket")
        .agg(
            n=pl.len(),
            med_cs=pl.col("cs_spread_bps").median(),
            med_ar=pl.col("ar_spread_bps").median(),
            med_range_proxy=pl.col("range_proxy_bps").median(),
        )
        .sort("price_bucket")
    )
    lines.append("spread panel (median bps by price bucket):")
    lines.append(str(panel))

    # One-paragraph diagnosis hook.
    top = ceiling.top_decile_mean
    if top == top and top > 0.004:  # > 40 bps
        diag = (
            "Diagnosis: oracle top-decile ceiling is material → selector / Stage C "
            "problem later; keep Stage B to enlarge span before deep scorers."
        )
    else:
        diag = (
            "Diagnosis: oracle ceiling thin under production geometry → "
            "opportunity/geometry problem now (Stage B / MIS-vertical), not Top-K peeks."
        )
    lines.append(diag)
    text = "\n".join(lines)
    print(text)
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--max-symbols", type=int, default=8)
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    if not args.data_dir.exists():
        print(f"Error: data dir missing: {args.data_dir}")
        sys.exit(1)

    for fold in args.folds:
        _diagnose_fold(
            fold,
            args.data_dir,
            args.config,
            max_symbols=args.max_symbols,
            n_boot=args.n_boot,
            seed=args.seed,
        )


if __name__ == "__main__":
    main()
