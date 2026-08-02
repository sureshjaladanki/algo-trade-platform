"""Tier 2 Horizon pipeline: features + labels + cascade masks + train / predict."""

from __future__ import annotations

import argparse
import pickle
import sys
import tempfile
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Dict, Iterator

import mlflow
import numpy as np
import polars as pl
from scipy.stats import spearmanr

from src.features.horizon import calculate_horizon_features
from src.horizon.features_regime import add_bars_since_regime_flip
from src.horizon.horizon_model import (
    LONG_FEATURES,
    SHORT_FEATURES,
    HorizonModel,
    episode_balanced_weights,
    get_purged_cv_splits,
    sleeve_sample_diagnostics,
)
from src.horizon.session import (
    auction_bleed_entry_expr,
    long_entry_ok_expr,
    short_entry_ok_expr,
)
from src.labels.horizon import calculate_horizon_labels
from src.labels.triple_barrier import calculate_triple_barrier_labels
from src.pipelines.build_regime_features import build_regime_features
from src.pipelines.load_horizon_universe import load_horizon_universe
from src.pipelines.regime_pipeline import predict_intraday_hmm
from src.regime.intraday import override_intraday_regime
from src.regime.types import DailyRegime, IntradayRegime
from src.utils.date import filter_by_period, parse_period_range
from src.utils.mlflow_loader import load_hmm_from_regime_experiment

TRADEABLE_DAILY_REGIMES = [
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
]

HORIZON_EXPERIMENT = "Horizon_Pipeline"


def prepare_horizon_data(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    sector_df: pl.DataFrame | None,
    daily_stock_df: pl.DataFrame,
    daily_nifty_df: pl.DataFrame,
    regime_df: pl.DataFrame,
    daily_regime_features: pl.DataFrame | None = None,
    include_triple_barrier: bool = True,
) -> pl.DataFrame:
    """
    Build horizon features and labels, join Tier 1 regimes, apply entry filters.

    `regime_df` must include post-hysteresis daily_regime and intraday_regime.
    Optional `daily_regime_features` supplies vol_regime_ratio → vix_regime_ratio.
    """
    features_df = calculate_horizon_features(
        stock_df,
        nifty_df,
        sector_df,
        daily_stock_df,
        daily_nifty_df,
        daily_regime_features=daily_regime_features,
    )
    labels_df = calculate_horizon_labels(stock_df, nifty_df, horizon_bars=4)

    df = features_df.join(labels_df, on=["symbol", "datetime"], how="inner")

    regime_cols = ["datetime", "daily_regime", "intraday_regime"]
    if "symbol" in regime_df.columns:
        df = df.join(
            regime_df.select(["symbol", *regime_cols]),
            on=["symbol", "datetime"],
            how="inner",
        )
    else:
        # Index-level Tier 1 regimes broadcast to all names.
        df = df.join(regime_df.select(regime_cols), on="datetime", how="inner")

    df = add_bars_since_regime_flip(df)

    if include_triple_barrier:
        tb_df = calculate_triple_barrier_labels(
            stock_df, nifty_df, daily_stock_df, horizon_bars=4
        )
        df = df.join(tb_df, on=["symbol", "datetime"], how="left")

    # Exclude 09:15 auction-bleed entries (bar-start convention).
    df = df.filter(~auction_bleed_entry_expr("time_only"))
    return df


def fit_horizon_gbm(
    df: pl.DataFrame, cv_kwargs: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """
    Train Long / Short Horizon models on cascade-valid sleeves with purged WF.

    `cv_kwargs` overrides the walk-forward window sizes (see get_purged_cv_splits).
    """
    long_df = df.filter(
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_UP.value)
        & pl.col("valid_label_long")
    )
    short_df = df.filter(
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_DOWN.value)
        & pl.col("valid_label_short")
    )

    long_df = long_df.drop_nulls(subset=LONG_FEATURES + ["fwd_excess_ret"])
    short_df = short_df.drop_nulls(subset=SHORT_FEATURES + ["fwd_excess_ret"])

    results: Dict[str, Any] = {}

    if long_df.height > 0:
        results.update(
            _fit_sleeve(
                long_df,
                direction="long",
                features=LONG_FEATURES,
                cv_kwargs=cv_kwargs,
            )
        )

    if short_df.height > 0:
        # Short episodes are scarce: balance at episode level, never by row oversampling.
        results.update(
            _fit_sleeve(
                short_df,
                direction="short",
                features=SHORT_FEATURES,
                episode_balanced=True,
                cv_kwargs=cv_kwargs,
            )
        )

    return results


def _fit_sleeve(
    sleeve_df: pl.DataFrame,
    direction: str,
    features: list[str],
    episode_balanced: bool = False,
    cv_kwargs: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    diagnostics = sleeve_sample_diagnostics(sleeve_df)
    print(
        f"{direction.capitalize()} sleeve: {diagnostics['bars']} bars, "
        f"{diagnostics['sessions']} sessions, {diagnostics['episodes']} episodes "
        f"(median {diagnostics['median_episode_bars']:.0f} bars/episode)"
    )

    val_ics: list[float] = []
    test_ics: list[float] = []
    models: list[HorizonModel] = []

    for train_df, val_df, test_df in get_purged_cv_splits(sleeve_df, **(cv_kwargs or {})):
        if min(train_df.height, val_df.height, test_df.height) == 0:
            continue
        model = HorizonModel(direction=direction)
        val_ic = model.train(
            X_train=train_df,
            y_train=train_df["fwd_excess_ret"],
            X_val=val_df,
            y_val=val_df["fwd_excess_ret"],
            features=features,
            train_weight=episode_balanced_weights(train_df) if episode_balanced else None,
        )
        test_ic = model.spearman_ic(test_df, test_df["fwd_excess_ret"])
        val_ics.append(val_ic)
        test_ics.append(test_ic)
        models.append(model)

    mean_val = sum(val_ics) / len(val_ics) if val_ics else 0.0
    mean_test = sum(test_ics) / len(test_ics) if test_ics else 0.0
    print(
        f"{direction.capitalize()} Mean Val IC: {mean_val:.4f} | Test IC: {mean_test:.4f}"
    )
    return {
        f"{direction}_models": models,
        f"{direction}_mean_ic": mean_val,
        f"{direction}_mean_test_ic": mean_test,
        f"{direction}_diagnostics": diagnostics,
    }


def predict_horizon_gbm(
    df: pl.DataFrame,
    long_model: HorizonModel | None,
    short_model: HorizonModel | None,
) -> pl.DataFrame:
    """
    Score cascade-eligible names each bar; rank Long descending / Short ascending.
    """
    # Inference uses entry cutoffs only (labels need future bars; live scores must not).
    long_mask = (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_UP.value)
        & long_entry_ok_expr("time_only")
    )
    short_mask = (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_DOWN.value)
        & short_entry_ok_expr("time_only")
    )

    long_df = df.filter(long_mask)
    short_df = df.filter(short_mask)

    if long_df.height > 0 and long_model is not None:
        long_df = long_df.with_columns(
            horizon_score=pl.Series(long_model.predict(long_df)),
            horizon_direction=pl.lit("long"),
        )
    else:
        long_df = long_df.with_columns(
            horizon_score=pl.lit(None, dtype=pl.Float64),
            horizon_direction=pl.lit(None, dtype=pl.Utf8),
        )

    if short_df.height > 0 and short_model is not None:
        short_df = short_df.with_columns(
            horizon_score=pl.Series(short_model.predict(short_df)),
            horizon_direction=pl.lit("short"),
        )
    else:
        short_df = short_df.with_columns(
            horizon_score=pl.lit(None, dtype=pl.Float64),
            horizon_direction=pl.lit(None, dtype=pl.Utf8),
        )

    scored_df = pl.concat([long_df, short_df], how="diagonal")
    return scored_df.with_columns(
        horizon_rank=pl.when(pl.col("horizon_direction") == "long")
        .then(pl.col("horizon_score").rank(descending=True).over("datetime"))
        .when(pl.col("horizon_direction") == "short")
        .then(pl.col("horizon_score").rank(descending=False).over("datetime"))
        .otherwise(None)
    )


def run_pipeline(
    data_dir: Path,
    config_path: Path,
    train_period: str,
    test_period: str,
    regime_run_id: str | None = None,
):
    train_start, train_end = parse_period_range(train_period)
    test_start, test_end = parse_period_range(test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    with _horizon_mlflow_run(train_period, test_period) as tracking_on:
        if tracking_on:
            mlflow.log_param("train_period", train_period)
            mlflow.log_param("test_period", test_period)
            mlflow.log_param("data_dir", str(data_dir))
            mlflow.log_param("config_path", str(config_path))

        print(f"1. Building regime features from {load_start} to {load_end}...")
        daily_features, intraday_features = build_regime_features(
            data_dir=data_dir,
            config_path=config_path,
            start_period=load_start,
            end_period=load_end,
        )

        print("2. Pulling fitted HMM from Regime_Pipeline experiment...")
        hmm_model, resolved_run_id = load_hmm_from_regime_experiment(
            train_period=train_period,
            run_id=regime_run_id,
        )
        if tracking_on:
            mlflow.log_param("regime_run_id", resolved_run_id)

        print("3. Predicting Tier 1 regimes (daily cascade + HMM)...")
        regime_preds = predict_intraday_hmm(
            daily_features,
            intraday_features,
            hmm_model,
            apply_hysteresis=True,
        )
        # Intraday hard rules (not inside the HMM).
        regime_preds = override_intraday_regime(regime_preds)
        regime_df = regime_preds.rename({"date": "datetime"}).select(
            ["datetime", "daily_regime", "intraday_regime"]
        )

        print("4. Loading Horizon universe (stocks + sectors + Nifty OHLCV)...")
        stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty = load_horizon_universe(
            data_dir=data_dir,
            config_path=config_path,
            start_period=load_start,
            end_period=load_end,
        )

        # Attach Tier 1 emissions used as Horizon pass-throughs.
        emissions = intraday_features.rename({"date": "datetime"}).select(
            ["datetime", "r_15", "vwap_dist"]
        )
        nifty_df = nifty_15m.join(emissions, on="datetime", how="left")

        print("5. Building Horizon features / labels and joining cascade regimes...")
        horizon_df = prepare_horizon_data(
            stock_df=stock_15m,
            nifty_df=nifty_df,
            sector_df=sector_15m,
            daily_stock_df=daily_stock,
            daily_nifty_df=daily_nifty,
            regime_df=regime_df,
            daily_regime_features=daily_features,
            include_triple_barrier=True,
        )

        print(f"6. Splitting into train ({train_period}) and test ({test_period})...")
        train_df = filter_by_period(
            horizon_df, train_start, train_end, datetime_col="datetime"
        )
        test_df = filter_by_period(
            horizon_df, test_start, test_end, datetime_col="datetime"
        )
        print(f"   Train shape: {train_df.shape}, Test shape: {test_df.shape}")
        if tracking_on:
            mlflow.log_metric("train_rows", train_df.height)
            mlflow.log_metric("test_rows", test_df.height)

        if train_df.height == 0 or test_df.height == 0:
            print("Error: Train or test Horizon dataframe is empty. Check your periods.")
            sys.exit(1)

        print("7. Fitting Horizon Long/Short models on cascade-valid train sleeves...")
        fit_results = fit_horizon_gbm(train_df)
        long_models = fit_results.get("long_models") or []
        short_models = fit_results.get("short_models") or []
        long_model = long_models[-1] if long_models else None
        short_model = short_models[-1] if short_models else None

        if tracking_on:
            for key in (
                "long_mean_ic",
                "long_mean_test_ic",
                "short_mean_ic",
                "short_mean_test_ic",
            ):
                if key in fit_results:
                    mlflow.log_metric(key, float(fit_results[key]))
            for direction in ("long", "short"):
                diag = fit_results.get(f"{direction}_diagnostics") or {}
                for metric_key, metric_val in diag.items():
                    if isinstance(metric_val, (int, float)) and np.isfinite(metric_val):
                        mlflow.log_metric(
                            f"{direction}_{metric_key}", float(metric_val)
                        )

        if long_model is None and short_model is None:
            print(
                "Error: No Horizon models trained. Check cascade filters / train length."
            )
            sys.exit(1)

        print("8. Predicting Horizon scores on cascade-valid test bars...")
        scored = predict_horizon_gbm(test_df, long_model, short_model)
        print(f"   Scored rows: {scored.height}")

        _log_holdout_ics(scored, tracking_on=tracking_on)

        print("\nTest sleeve counts:")
        sleeve_counts = (
            scored.group_by("horizon_direction").len().sort("len", descending=True)
        )
        print(sleeve_counts.to_dict(as_series=False))
        if tracking_on:
            for row in sleeve_counts.iter_rows(named=True):
                name = row["horizon_direction"] or "null"
                mlflow.log_metric(f"test_count_{name}", row["len"])

            _log_model_artifacts(long_model, short_model)
            print("\nRun `mlflow ui` in your terminal to view the experiment tracking.")


def _log_holdout_ics(scored: pl.DataFrame, *, tracking_on: bool) -> None:
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
        if tracking_on:
            mlflow.log_metric(f"holdout_{direction}_ic", ic_val)
            mlflow.log_metric(f"holdout_{direction}_n", subset.height)


def _log_model_artifacts(
    long_model: HorizonModel | None,
    short_model: HorizonModel | None,
) -> None:
    payload = {"long_model": long_model, "short_model": short_model}
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
        pickle.dump(payload, tmp)
        tmp_path = tmp.name
    mlflow.log_artifact(tmp_path, "model")
    Path(tmp_path).unlink(missing_ok=True)


@contextmanager
def _horizon_mlflow_run(train_period: str, test_period: str) -> Iterator[bool]:
    """Yield True when an active MLflow run is available; False if tracking is skipped."""
    try:
        mlflow.set_experiment(HORIZON_EXPERIMENT)
        with mlflow.start_run(run_name=f"Horizon_{train_period}_{test_period}"):
            yield True
    except Exception as exc:  # noqa: BLE001 - tolerate broken local tracking DB
        msg = str(exc).lower()
        if "schema" in msg or "out-of-date" in msg or "revision" in msg:
            print(
                "Warning: MLflow tracking unavailable "
                f"({exc}). Continuing without experiment logging."
            )
            with nullcontext():
                yield False
        else:
            raise


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
        regime_run_id=args.regime_run_id,
    )
