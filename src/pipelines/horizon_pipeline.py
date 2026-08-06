"""Tier 2 Horizon pipeline: features + labels + cascade masks + train / predict."""

from __future__ import annotations

import argparse
import pickle
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

import mlflow
import numpy as np
import polars as pl
from scipy.stats import spearmanr

from src.horizon.horizon_model import (
    DEFAULT_EMBARGO_DAYS,
    DEFAULT_TEST_DAYS,
    DEFAULT_TRAIN_DAYS,
    DEFAULT_VAL_DAYS,
    LONG_FEATURES,
    SHORT_FEATURES,
    GBMHorizonModel,
    episode_balanced_weights,
    get_purged_cv_splits,
    sleeve_sample_diagnostics,
)
from src.horizon.session import (
    long_entry_ok_expr,
    short_entry_ok_expr,
)
from src.pipelines.build_horizon_features import (
    build_horizon_features,
    load_horizon_data,
)
from src.pipelines.build_regime_features import (
    build_regime_features,
    load_regime_data,
)
from src.pipelines.regime_pipeline import predict_intraday_hmm
from src.regime.intraday import override_intraday_regime
from src.regime.types import DailyRegime, IntradayRegime
from src.utils.date import filter_by_period, parse_period_range
from src.utils.mlflow_loader import load_hmm_model

TRADEABLE_DAILY_REGIMES = [
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
]

HORIZON_EXPERIMENT = "Horizon_Pipeline"

@dataclass(frozen=True)
class SleeveConfig:
    features: list[str]
    intraday_regime: str
    valid_label_col: str
    episode_balanced: bool
    entry_ok: Callable[[str], pl.Expr]
    rank_descending: bool


SLEEVES: dict[str, SleeveConfig] = {
    "long": SleeveConfig(
        features=LONG_FEATURES,
        intraday_regime=IntradayRegime.TREND_UP.value,
        valid_label_col="valid_label_long",
        episode_balanced=False,
        entry_ok=long_entry_ok_expr,
        rank_descending=True,
    ),
    "short": SleeveConfig(
        features=SHORT_FEATURES,
        intraday_regime=IntradayRegime.TREND_DOWN.value,
        valid_label_col="valid_label_short",
        episode_balanced=True,
        entry_ok=short_entry_ok_expr,
        rank_descending=False,
    ),
}


def _sleeve_config(direction: str) -> SleeveConfig:
    if direction not in SLEEVES:
        raise ValueError("direction must be 'long' or 'short'")
    return SLEEVES[direction]


def _fit_sleeve_mask(cfg: SleeveConfig) -> pl.Expr:
    return (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == cfg.intraday_regime)
        & pl.col(cfg.valid_label_col)
    )


def _predict_sleeve_mask(cfg: SleeveConfig) -> pl.Expr:
    return (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == cfg.intraday_regime)
        & cfg.entry_ok("time_only")
    )


def fit_horizon_gbm(
    df: pl.DataFrame, direction: str, cv_kwargs: Dict[str, Any] | None = None
) -> tuple[GBMHorizonModel | None, Dict[str, Any]]:
    """
    Train a single Horizon model (Long or Short) on cascade-valid sleeves with purged WF.

    Returns (model, fit_stats). `fit_stats` holds CV ICs and sleeve diagnostics for
    the caller to log (e.g. via log_horizon_mlflow); fit itself does not touch MLflow.
    """
    cfg = _sleeve_config(direction)
    # drop_nulls alone is not enough: float NaNs survive and blow up LGBM y-checks.
    sleeve_df = (
        df.filter(_fit_sleeve_mask(cfg))
        .drop_nulls(subset=cfg.features + ["fwd_excess_ret"])
        .filter(pl.col("fwd_excess_ret").is_finite())
    )

    if sleeve_df.height == 0:
        print(f"No valid data to train {direction} model.")
        return None, {}

    diagnostics = sleeve_sample_diagnostics(sleeve_df)
    print(
        f"{direction.capitalize()} sleeve: {diagnostics['bars']} bars, "
        f"{diagnostics['sessions']} sessions, {diagnostics['episodes']} episodes "
        f"(median {diagnostics['median_episode_bars']:.0f} bars/episode)"
    )

    # Walk-forward on full-period trading days so train_days≈21 calendar months,
    # not sparse sleeve-only sessions (TREND_UP/DOWN fire on a subset of days).
    calendar_dates = (
        df.select("date_only").unique().sort("date_only").to_series().to_list()
    )
    cv = dict(cv_kwargs or {})
    train_days = cv.get("train_days", DEFAULT_TRAIN_DAYS)
    val_days = cv.get("val_days", DEFAULT_VAL_DAYS)
    test_days = cv.get("test_days", DEFAULT_TEST_DAYS)
    embargo_days = cv.get("embargo_days", DEFAULT_EMBARGO_DAYS)
    block = train_days + embargo_days + val_days + embargo_days + test_days
    if len(calendar_dates) < block:
        print(
            f"Cannot build purged CV for {direction}: {len(calendar_dates)} calendar "
            f"sessions < block {block} "
            f"(train={train_days}, val={val_days}, test={test_days}, "
            f"embargo={embargo_days}×2). Extend train_period or pass smaller cv_kwargs."
        )
        return None, {"diagnostics": diagnostics, "n_splits": 0}

    val_ics: list[float] = []
    test_ics: list[float] = []
    models: list[GBMHorizonModel] = []

    for fold_train, fold_val, fold_test in get_purged_cv_splits(
        sleeve_df, calendar_dates=calendar_dates, **cv
    ):
        if min(fold_train.height, fold_val.height, fold_test.height) == 0:
            continue
        model = GBMHorizonModel(direction=direction)
        val_ic = model.fit(
            X_train=fold_train,
            y_train=fold_train["fwd_excess_ret"],
            X_val=fold_val,
            y_val=fold_val["fwd_excess_ret"],
            features=cfg.features,
            train_weight=(
                episode_balanced_weights(fold_train) if cfg.episode_balanced else None
            ),
        )
        test_ic = model.spearman_ic(fold_test, fold_test["fwd_excess_ret"])
        val_ics.append(val_ic)
        test_ics.append(test_ic)
        models.append(model)

    if not models:
        print(
            f"No non-empty purged CV folds for {direction} "
            f"(calendar sessions={len(calendar_dates)}, sleeve sessions="
            f"{diagnostics['sessions']})."
        )
        return None, {"diagnostics": diagnostics, "n_splits": 0}

    mean_val = sum(val_ics) / len(val_ics)
    mean_test = sum(test_ics) / len(test_ics)
    print(
        f"{direction.capitalize()} Mean Val IC: {mean_val:.4f} | "
        f"Test IC: {mean_test:.4f} ({len(models)} folds)"
    )

    fit_stats = {
        "mean_ic": mean_val,
        "mean_test_ic": mean_test,
        "diagnostics": diagnostics,
        "n_splits": len(models),
        "calendar_sessions": len(calendar_dates),
    }
    return models[-1], fit_stats


def log_horizon_mlflow(direction: str, fit_stats: Dict[str, Any]) -> None:
    """Log sleeve CV ICs and sample diagnostics to the active MLflow run."""
    if not fit_stats:
        return
    mlflow.log_metric(f"{direction}_mean_ic", float(fit_stats["mean_ic"]))
    mlflow.log_metric(f"{direction}_mean_test_ic", float(fit_stats["mean_test_ic"]))
    for metric_key, metric_val in (fit_stats.get("diagnostics") or {}).items():
        if isinstance(metric_val, (int, float)) and np.isfinite(metric_val):
            mlflow.log_metric(f"{direction}_{metric_key}", float(metric_val))


def predict_horizon_gbm(
    df: pl.DataFrame,
    model: GBMHorizonModel,
) -> pl.DataFrame:
    """
    Score cascade-eligible names each bar; rank descending / ascending depending on direction.
    """
    cfg = _sleeve_config(model.direction)
    sleeve_df = df.filter(_predict_sleeve_mask(cfg))

    if sleeve_df.height > 0:
        sleeve_df = sleeve_df.with_columns(
            horizon_score=pl.Series(model.predict(sleeve_df)),
            horizon_direction=pl.lit(model.direction),
        )
    else:
        sleeve_df = sleeve_df.with_columns(
            horizon_score=pl.lit(None, dtype=pl.Float64),
            horizon_direction=pl.lit(None, dtype=pl.Utf8),
        )

    return sleeve_df.with_columns(
        horizon_rank=pl.col("horizon_score")
        .rank(descending=cfg.rank_descending)
        .over("date")
    )


def run_pipeline(
    data_dir: Path,
    config_path: Path,
    train_period: str,
    test_period: str,
    direction: str = "both",
    regime_run_id: str | None = None,
):
    mlflow.set_experiment(HORIZON_EXPERIMENT)
    with mlflow.start_run(run_name=f"Horizon_{train_period}_{test_period}"):
        mlflow.log_param("train_period", train_period)
        mlflow.log_param("test_period", test_period)
        mlflow.log_param("data_dir", str(data_dir))
        mlflow.log_param("config_path", str(config_path))

        train_start, train_end = parse_period_range(train_period)
        test_start, test_end = parse_period_range(test_period)
        load_start = min(train_start, test_start)
        load_end = max(train_end, test_end)

        print(f"1. Loading regime data from {load_start} to {load_end}...")
        vix_daily, market_daily, market_15m, nifty100_daily_dfs = load_regime_data(
            data_dir=data_dir,
            config_path=config_path,
            start_period=load_start,
            end_period=load_end,
        )
        print("   Building regime features...")
        daily_regime, intraday_regime = build_regime_features(
            vix_daily, market_daily, market_15m, nifty100_daily_dfs
        )

        print("2. Pulling fitted HMM from Regime_Pipeline experiment...")
        hmm_model, resolved_run_id = load_hmm_model(
            train_period=train_period,
            run_id=regime_run_id,
        )
        mlflow.log_param("regime_run_id", resolved_run_id)

        print("3. Predicting Tier 1 regimes (daily cascade + HMM)...")
        regime_preds = predict_intraday_hmm(
            daily_regime,
            intraday_regime,
            hmm_model,
            apply_hysteresis=True,
        )
        # Intraday hard rules (not inside the HMM).
        regime_preds = override_intraday_regime(regime_preds)
        regime_df = regime_preds.select(
            ["date", "daily_regime", "intraday_regime"]
        )

        print("4. Loading Horizon universe (stocks + sectors + Nifty OHLCV)...")
        stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty = load_horizon_data(
            data_dir=data_dir,
            config_path=config_path,
            start_period=load_start,
            end_period=load_end,
        )

        print("5. Building Horizon features / labels...")
        # Auction-bleed / NO_TRADE bars stay in the frame (same as daily NO_TRADE);
        # fit_horizon_gbm / predict_horizon_gbm sleeve masks exclude them.
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

        print(f"6. Splitting into train ({train_period}) and test ({test_period})...")
        train_df = filter_by_period(
            horizon_df, train_start, train_end, datetime_col="date"
        )
        test_df = filter_by_period(
            horizon_df, test_start, test_end, datetime_col="date"
        )
        print(f"   Train shape: {train_df.shape}, Test shape: {test_df.shape}")
        mlflow.log_metric("train_rows", train_df.height)
        mlflow.log_metric("test_rows", test_df.height)

        if train_df.height == 0 or test_df.height == 0:
            print("Error: Train or test Horizon dataframe is empty. Check your periods.")
            sys.exit(1)

        print("7. Fitting Horizon models on cascade-valid train sleeves...")
        
        directions = ["long", "short"] if direction == "both" else [direction]
        models: dict[str, GBMHorizonModel] = {}
        scored_dfs = []

        for direction in directions:
            print(f"\n   Fitting Horizon {direction.capitalize()} model...")
            model, fit_stats = fit_horizon_gbm(train_df, direction=direction)
            log_horizon_mlflow(direction, fit_stats)

            if model is None:
                print(f"   Warning: No Horizon {direction.capitalize()} model trained.")
                continue

            models[direction] = model
            print(f"8. Predicting Horizon {direction.capitalize()} scores on cascade-valid test bars...")
            scored = predict_horizon_gbm(test_df, model)
            print(f"   Scored {direction} rows: {scored.height}")
            scored_dfs.append(scored)

        if not scored_dfs:
            print("Error: No Horizon models trained/scored. Check cascade filters / train length.")
            sys.exit(1)

        scored = pl.concat(scored_dfs, how="diagonal")
        _log_holdout_ics(scored)

        print("\nTest sleeve counts:")
        sleeve_counts = (
            scored.group_by("horizon_direction").len().sort("len", descending=True)
        )
        print(sleeve_counts.to_dict(as_series=False))
        for row in sleeve_counts.iter_rows(named=True):
            name = row["horizon_direction"] or "null"
            mlflow.log_metric(f"test_count_{name}", row["len"])

        # One artifact per sleeve so MLflow UI shows long and short separately.
        with tempfile.TemporaryDirectory() as tmpdir:
            for sleeve, model in models.items():
                path = Path(tmpdir) / f"{sleeve}_model.pkl"
                with open(path, "wb") as f:
                    pickle.dump(model, f)
                mlflow.log_artifact(str(path), f"model/{sleeve}")


        print("\nRun `mlflow ui` in your terminal to view the experiment tracking.")


def _log_holdout_ics(scored: pl.DataFrame) -> None:
    if "fwd_excess_ret" not in scored.columns:
        return
    for direction in ("long", "short"):
        subset = scored.filter(pl.col("horizon_direction") == direction).drop_nulls(
            subset=["horizon_score", "fwd_excess_ret"]
        )
        if subset.height == 0:
            continue
        ic, _ = spearmanr(
            subset["horizon_score"].to_numpy(),
            subset["fwd_excess_ret"].to_numpy(),
        )
        ic_val = float(ic) if ic == ic else 0.0
        print(f"   Holdout {direction} Spearman IC: {ic_val:.4f} (n={subset.height})")
        mlflow.log_metric(f"holdout_{direction}_ic", ic_val)
        mlflow.log_metric(f"holdout_{direction}_n", subset.height)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the Algo Trading Horizon Pipeline workflow"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/GOLDEN",
        help="Path to the GOLDEN data directory",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/market_sectoral_symbols.yml",
        help="Path to the symbols config",
    )
    parser.add_argument(
        "--train-period",
        type=str,
        required=True,
        help="Training period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy",
    )
    parser.add_argument(
        "--test-period",
        type=str,
        required=True,
        help="Test period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy",
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

    data_dir = Path(args.data_dir)
    config_path = Path(args.config)

    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist.")
        sys.exit(1)

    if not config_path.exists():
        print(f"Error: Config file {config_path} does not exist.")
        sys.exit(1)

    run_pipeline(
        data_dir=data_dir,
        config_path=config_path,
        train_period=args.train_period,
        test_period=args.test_period,
        direction=args.direction,
        regime_run_id=args.regime_run_id,
    )
