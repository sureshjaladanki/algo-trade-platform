"""M4 — Long event clock: counts, opportunity overlap, oracle ceiling on event pool."""

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
from src.horizon.fresh.events import build_long_event_panel, rule_dictionary
from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.microstructure import attach_spread_panel
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    attach_opportunity_ok,
    remaining_session_range,
)
from src.horizon.fresh.tradability import attach_tradability_mask
from src.labels.fresh_barrier import (
    PROD_LONG_GEOMETRY,
    calculate_fresh_long_labels,
)
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _fit_opportunity(
    stock: pl.DataFrame,
    train_start,
    train_end,
    test_start,
    test_end,
) -> pl.DataFrame:
    """Return test bars with opportunity_ok from a train-fit Stage B model."""
    panel = remaining_session_range(attach_opportunity_features(stock))
    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
    test = filter_by_period(panel, test_start, test_end, datetime_col="date")
    tr = train.drop_nulls(subset=[*OPPORTUNITY_FEATURES, "remaining_range"])
    te = test.drop_nulls(subset=[*OPPORTUNITY_FEATURES, "remaining_range"])
    finite = pl.all_horizontal(
        [pl.col(c).is_finite() for c in (*OPPORTUNITY_FEATURES, "remaining_range")]
    )
    tr = tr.filter(finite & (pl.col("remaining_range") > 0))
    te = te.filter(finite & (pl.col("remaining_range") > 0))
    model = OpportunityModel().fit(
        tr.select(list(OPPORTUNITY_FEATURES)).to_numpy(),
        tr["remaining_range"].to_numpy(),
    )
    q = model.predict_quantiles(te.select(list(OPPORTUNITY_FEATURES)).to_numpy())
    return attach_opportunity_ok(
        te.with_columns(range_q25=pl.Series(q["range_q25"]))
    ).select(["symbol", "date", "opportunity_ok", "range_q25", "remaining_range"])


def _run_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    *,
    max_symbols: int,
    n_boot: int,
    seed: int,
) -> None:
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    print(f"\n=== Fold {fold} test={cfg['test_period']} ===")
    stock_15m, nifty_15m, *_ = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    stock_15m = _select_symbols(stock_15m, max_symbols)
    print(f"   symbols={stock_15m['symbol'].n_unique()}")

    test_stock = filter_by_period(stock_15m, test_start, test_end, datetime_col="date")
    test_nifty = filter_by_period(nifty_15m, test_start, test_end, datetime_col="date")

    events = build_long_event_panel(test_stock)
    n_days = test_stock["date"].dt.date().n_unique()
    print(
        f"   events={events.height} events/day={events.height / max(n_days, 1):.2f} "
        f"symbols_with_event/day="
        f"{events.select(['symbol', 'date_only']).unique().height / max(n_days, 1):.2f}"
    )
    if events.height:
        print(events.group_by("rule_id").len().sort("rule_id"))

    opp = _fit_opportunity(
        stock_15m, train_start, train_end, test_start, test_end
    )
    trad = attach_tradability_mask(attach_spread_panel(test_stock)).select(
        ["symbol", "date", "tradable_ok", "c_eff_bps"]
    )
    labeled = calculate_fresh_long_labels(
        test_stock, test_nifty, PROD_LONG_GEOMETRY
    )

    # Bar pool (eligible) vs event pool ceilings.
    bar_pool = labeled.filter(pl.all_horizontal(production_long_eligible_mask()))
    bar_ceil = selection_ceiling(
        bar_pool, fold=fold, pool_name="bar_eligible", n_boot=n_boot, seed=seed
    )

    event_join = (
        events.select(["event_id", "symbol", "date", "rule_id", "side"])
        .join(labeled, on=["symbol", "date"], how="inner")
        .join(opp, on=["symbol", "date"], how="left")
        .join(trad, on=["symbol", "date"], how="left")
    )
    event_elig = event_join.filter(pl.all_horizontal(production_long_eligible_mask()))
    event_ceil = selection_ceiling(
        event_elig, fold=fold, pool_name="event_eligible", n_boot=n_boot, seed=seed
    )

    # Stage A ∩ B on events
    gated = event_elig.filter(
        pl.col("tradable_ok").fill_null(False) & pl.col("opportunity_ok").fill_null(False)
    )
    gated_ceil = selection_ceiling(
        gated,
        fold=fold,
        pool_name="event_A_and_B",
        n_boot=n_boot,
        seed=seed,
    )
    overlap = float(event_elig["opportunity_ok"].fill_null(False).mean()) if event_elig.height else 0.0

    print(format_ceiling_report(bar_ceil))
    print(format_ceiling_report(event_ceil))
    print(format_ceiling_report(gated_ceil))
    print(
        f"   event∩opportunity_ok={overlap:.1%}  "
        f"event A∩B n={gated.height}  "
        f"top10% bar={bar_ceil.top_decile_mean:.4f} "
        f"event={event_ceil.top_decile_mean:.4f} "
        f"A∩B={gated_ceil.top_decile_mean:.4f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    print(rule_dictionary())
    if not args.data_dir.exists():
        print(f"missing data dir {args.data_dir}")
        sys.exit(1)
    for fold in args.folds:
        _run_fold(
            fold,
            args.data_dir,
            args.config,
            max_symbols=args.max_symbols,
            n_boot=args.n_boot,
            seed=args.seed,
        )


if __name__ == "__main__":
    main()
