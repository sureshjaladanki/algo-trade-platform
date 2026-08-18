"""M3/M4 harness scaffolding — opportunity features + event counts (pre K1/K2 fit).

Full K1/K2 dual-fold fit is the next execution step once M1 diagnosis is reviewed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.fresh.events import build_long_event_panel, rule_dictionary
from src.horizon.fresh.opportunity import (
    attach_opportunity_features,
    remaining_session_range,
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
    parser.add_argument("--max-symbols", type=int, default=8)
    args = parser.parse_args()

    print(rule_dictionary())
    start, end = parse_period_range(args.period)
    stock_15m, *_ = load_horizon_data(
        data_dir=args.data_dir,
        config_path=args.config,
        start_period=start,
        end_period=end,
    )
    syms = sorted(stock_15m["symbol"].unique().to_list())[: args.max_symbols]
    bars = filter_by_period(
        stock_15m.filter(pl.col("symbol").is_in(syms)),
        start,
        end,
        datetime_col="date",
    )
    if bars.height == 0:
        print("empty")
        sys.exit(1)

    feat = attach_opportunity_features(bars)
    feat = remaining_session_range(feat)
    events = build_long_event_panel(bars)
    n_days = bars["date"].dt.date().n_unique()
    print(
        f"bars={bars.height} events={events.height} "
        f"events/day={events.height / max(n_days, 1):.2f} "
        f"remaining_range_med={feat['remaining_range'].median():.4f}"
    )
    if events.height:
        print(events.group_by("rule_id").len().sort("rule_id"))


if __name__ == "__main__":
    main()
