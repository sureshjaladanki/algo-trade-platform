"""Tier 1 Regime eval harness CLI — see docs/regime-tier1-eval-verdict.md."""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

from src.labels.triple_barrier import ROUND_TRIP_COST
from src.pipelines.build_regime_features import (
    build_regime_features,
    load_regime_data,
)
from src.pipelines.regime_pipeline import fit_intraday_hmm, predict_intraday_hmm
from src.regime.daily import classify_daily_regime
from src.regime.eval import (
    N_BOOT,
    build_ew_basket_15m,
    evaluate_regime,
    format_report,
)
from src.regime.intraday import override_intraday_regime
from src.utils.data import resample_15m
from src.utils.date import filter_by_period, parse_period_range
from src.utils.load_config import load_config
from src.utils.symbol_data import load_symbol_data

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_nifty100_15m(
    data_dir: Path,
    config_path: Path,
    start_period: str,
    end_period: str,
) -> list[pl.DataFrame]:
    symbols = load_config(config_path).get("nifty100_symbols") or []
    frames = []
    for sym in symbols:
        path = data_dir / f"{sym}.csv"
        if not path.exists():
            continue
        raw = load_symbol_data(path, start_period=start_period, end_period=end_period)
        if raw.height == 0:
            continue
        frames.append(resample_15m(raw).select(["date", "open", "high", "low", "close"]))
    return frames


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Tier 1 Regime (Daily D2' + Intraday I1/I5) on a fold."
    )
    parser.add_argument("--config", type=str, default="config/market_sectoral_symbols.yml")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN")
    parser.add_argument("--train-period", type=str, required=True)
    parser.add_argument("--test-period", type=str, required=True)
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = REPO_ROOT / data_dir
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path

    train_start, train_end = parse_period_range(args.train_period)
    test_start, test_end = parse_period_range(args.test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    print(f"Loading regime data {load_start} -> {load_end}...")
    vix_daily, market_daily, market_15m, nifty100_daily = load_regime_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    daily_features, intraday_features = build_regime_features(
        vix_daily, market_daily, market_15m, nifty100_daily
    )

    daily_train = filter_by_period(daily_features, train_start, train_end, datetime_col="date")
    daily_test = filter_by_period(daily_features, test_start, test_end, datetime_col="date")
    intra_train = filter_by_period(
        intraday_features, train_start, train_end, datetime_col="date"
    )
    intra_test = filter_by_period(
        intraday_features, test_start, test_end, datetime_col="date"
    )
    market_test = filter_by_period(market_15m, test_start, test_end, datetime_col="date")

    print(
        "Daily=locked v1 (regime-tier1-verdict). "
        "D2': first tradable bar -> exit H=4, "
        f"cost-netted ({ROUND_TRIP_COST:.4f} RT); gated. D2max=legacy diagnostic."
    )

    print(f"Fitting HMM on train {args.train_period}...")
    hmm = fit_intraday_hmm(
        daily_train, intra_train, random_state=args.seed, n_iter=100
    )

    print(f"Predicting regimes on test {args.test_period}...")
    preds = override_intraday_regime(
        predict_intraday_hmm(daily_test, intra_test, hmm, apply_hysteresis=True)
    )
    daily_classified = classify_daily_regime(daily_test)

    print("Building EW Nifty-100 15m basket for confirmatory D2'...")
    stock_15m = load_nifty100_15m(data_dir, config_path, test_start, test_end)
    basket = build_ew_basket_15m(stock_15m)
    print(f"   Basket bars: {basket.height} from {len(stock_15m)} symbols")

    metrics = evaluate_regime(
        daily_features=daily_test,
        daily_classified=daily_classified,
        regime_preds=preds,
        market_15m=market_test,
        hmm=hmm,
        basket_15m=basket,
        n_boot=args.n_boot,
        seed=args.seed,
    )
    title = (
        f"Tier 1 Regime Eval  train={args.train_period}  "
        f"test={args.test_period}  daily=v1"
    )
    print()
    print(format_report(metrics, title))


if __name__ == "__main__":
    main()
