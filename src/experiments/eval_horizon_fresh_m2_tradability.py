"""M2 — Stage A tradability rejection-mass panel (deterministic filter)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.fresh.microstructure import attach_spread_panel
from src.horizon.fresh.tradability import (
    attach_tradability_mask,
    rejection_mass_by_bucket,
)
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--period", type=str, default="2018-2018")
    parser.add_argument("--max-symbols", type=int, default=12)
    args = parser.parse_args()

    start, end = parse_period_range(args.period)
    stock_15m, *_ = load_horizon_data(
        data_dir=args.data_dir,
        config_path=args.config,
        start_period=start,
        end_period=end,
    )
    if args.max_symbols is not None:
        syms = sorted(stock_15m["symbol"].unique().to_list())[: args.max_symbols]
        stock_15m = stock_15m.filter(pl.col("symbol").is_in(syms))
    bars = filter_by_period(stock_15m, start, end, datetime_col="date")
    if bars.height == 0:
        print("empty panel")
        sys.exit(1)

    panel = attach_tradability_mask(attach_spread_panel(bars))
    summary = rejection_mass_by_bucket(panel)
    overall = float((~panel["tradable_ok"]).mean())
    print(f"period={args.period} n={panel.height} reject_rate={overall:.1%}")
    print(summary)


if __name__ == "__main__":
    main()
