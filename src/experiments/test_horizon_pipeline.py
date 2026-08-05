import argparse
from pathlib import Path

import polars as pl
from scipy.stats import spearmanr

from src.pipelines.build_horizon_features import (
    build_horizon_features,
    load_horizon_data,
)
from src.pipelines.build_regime_features import build_regime_features
from src.pipelines.horizon_pipeline import fit_horizon_gbm, predict_horizon_gbm
from src.pipelines.regime_pipeline import predict_intraday_hmm
from src.regime.intraday import override_intraday_regime
from src.utils.date import filter_by_period, parse_period_range
from src.utils.mlflow_loader import load_hmm_model

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN = REPO_ROOT / "data" / "GOLDEN"


def main():
    parser = argparse.ArgumentParser(description="Test Horizon Pipeline with cascade gates.")
    parser.add_argument(
        "--config",
        type=str,
        default="config/market_sectoral_symbols.yml",
        help="Path to the market / sectoral symbols config",
    )
    parser.add_argument(
        "--train-period",
        type=str,
        default="2015-2017",
        help="Train period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy",
    )
    parser.add_argument(
        "--test-period",
        type=str,
        default="2018-2018",
        help="Test period: yyyy-yyyy (e.g. 2017-2018) or mm/yyyy-mm/yyyy",
    )
    parser.add_argument(
        "--direction",
        type=str,
        default="both",
        choices=["long", "short", "both"],
        help="Direction of the model to train (long, short, or both)",
    )
    parser.add_argument(
        "--regime-run-id",
        type=str,
        default=None,
        help="Optional Regime_Pipeline MLflow run id (default: match train_period / latest)",
    )
    args = parser.parse_args()

    config_path = REPO_ROOT / args.config
    train_start, train_end = parse_period_range(args.train_period)
    test_start, test_end = parse_period_range(args.test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    print(f"1. Building regime features from {load_start} to {load_end}...")
    daily_regime, intraday_regime = build_regime_features(
        data_dir=GOLDEN,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )

    print("2. Pulling fitted HMM from Regime_Pipeline experiment...")
    hmm_model, resolved_run_id = load_hmm_model(
        train_period=args.train_period,
        run_id=args.regime_run_id,
    )
    print(f"   Using Regime Run ID: {resolved_run_id}")

    print("3. Predicting Tier 1 regimes (daily cascade + HMM)...")
    regime_preds = predict_intraday_hmm(
        daily_regime,
        intraday_regime,
        hmm_model,
        apply_hysteresis=True,
    )
    # Intraday hard rules (not inside the HMM).
    regime_preds = override_intraday_regime(regime_preds)
    regime_df = regime_preds.select(["date", "daily_regime", "intraday_regime"])

    print("4. Loading Horizon universe (stocks + sectors + Nifty OHLCV)...")
    stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty = load_horizon_data(
        data_dir=GOLDEN,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )

    print("5. Building Horizon features / labels...")
    horizon_df = build_horizon_features(
        stock_15m,
        nifty_15m,
        sector_15m,
        daily_stock,
        daily_nifty,
        daily_regime_df=daily_regime,
        intraday_regime_df=intraday_regime,
        regime_df=regime_df,
    )

    print(f"6. Splitting into train ({args.train_period}) and test ({args.test_period})...")
    train_df = filter_by_period(horizon_df, train_start, train_end, datetime_col="date")
    test_df = filter_by_period(horizon_df, test_start, test_end, datetime_col="date")
    print(f"   Train shape: {train_df.shape}, Test shape: {test_df.shape}")

    if train_df.height == 0 or test_df.height == 0:
        print("Error: Train or test Horizon dataframe is empty. Check your periods.")
        return

    print("7. Fitting Horizon models on cascade-valid train sleeves...")
    directions = ["long", "short"] if args.direction == "both" else [args.direction]
    scored_dfs = []

    for direction in directions:
        print(f"\n   Fitting Horizon {direction.capitalize()} model...")
        model, fit_stats = fit_horizon_gbm(train_df, direction=direction)

        if model is None:
            print(f"   Warning: No Horizon {direction.capitalize()} model trained.")
            continue

        print(f"8. Predicting Horizon {direction.capitalize()} scores on cascade-valid test bars...")
        scored = predict_horizon_gbm(test_df, model)
        print(f"   Scored {direction} rows: {scored.height}")
        scored_dfs.append(scored)

    if not scored_dfs:
        print("Error: No Horizon models trained/scored. Check cascade filters / train length.")
        return

    scored = pl.concat(scored_dfs, how="diagonal")

    print("\n9. Holdout ICs:")
    if "fwd_excess_ret" in scored.columns:
        for direction in ("long", "short"):
            subset = scored.filter(pl.col("horizon_direction") == direction).drop_nulls(
                subset=["horizon_score", "fwd_excess_ret"]
            )
            if subset.height > 0:
                ic, _ = spearmanr(
                    subset["horizon_score"].to_numpy(),
                    subset["fwd_excess_ret"].to_numpy(),
                )
                ic_val = float(ic) if ic == ic else 0.0
                print(f"   Holdout {direction} Spearman IC: {ic_val:.4f} (n={subset.height})")

    print("\nTest sleeve counts:")
    sleeve_counts = scored.group_by("horizon_direction").len().sort("len", descending=True)
    print(sleeve_counts.to_dict(as_series=False))


if __name__ == "__main__":
    main()
