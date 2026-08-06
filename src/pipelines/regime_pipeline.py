import argparse
import pickle
import sys
import tempfile
from pathlib import Path

import mlflow
import numpy as np
import polars as pl

from src.pipelines.build_regime_features import (
    build_regime_features,
    load_regime_data,
)
from src.regime.daily import classify_daily_regime
from src.regime.intraday_model import DEFAULT_FEATURE_COLS, IntradayHMMRegimeModel
from src.regime.intraday import open_auction_bleed_expr, override_intraday_regime
from src.regime.types import DailyRegime
from src.utils.date import filter_by_period, parse_period_range

TRADEABLE_DAILY_REGIMES = [
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
]


def cascade_valid_intraday(
    daily_features: pl.DataFrame,
    intraday_features: pl.DataFrame,
) -> pl.DataFrame:
    """
    Keep intraday bars eligible for HMM fit/score/decode.

    Gates:
    - daily regime is SUPPORTIVE or AMBIGUOUS (skip HOSTILE / NO_TRADE days)
    - not open-auction bleed (skip 09:15 → intraday NO_TRADE)
    """
    daily_classified = classify_daily_regime(daily_features)
    valid_days = daily_classified.filter(
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
    ).select(["date"])
    valid_intraday = intraday_features.filter(~open_auction_bleed_expr('date'))

    # Intraday `date` is a bar timestamp; daily `date` is calendar day.
    return (
        valid_intraday.with_columns(_session_day=pl.col("date").dt.date())
        .join(valid_days, left_on="_session_day", right_on="date", how="inner")
        .drop("_session_day")
    )


def fit_intraday_hmm(
    daily_features: pl.DataFrame,
    intraday_features: pl.DataFrame,
    random_state: int = 42,
    n_iter: int = 100,
) -> IntradayHMMRegimeModel:
    """
    Fits the intraday HMM only on cascade-gated rows (tradeable daily + non-bleed).
    Returns the fitted IntradayHMMRegimeModel, which can be logged to MLflow.
    """
    valid_intraday = cascade_valid_intraday(daily_features, intraday_features)
    hmm = IntradayHMMRegimeModel(random_state=random_state, n_iter=n_iter)

    if valid_intraday.height == 0:
        print("No valid intraday data to fit HMM. Check daily features and thresholds.")
        return hmm

    hmm.fit(valid_intraday)
    return hmm


def predict_intraday_hmm(
    daily_features: pl.DataFrame,
    intraday_features: pl.DataFrame,
    hmm_model: IntradayHMMRegimeModel,
    apply_hysteresis: bool = True,
) -> pl.DataFrame:
    """
    Predicts both daily and intraday regimes.

    Cascade gates (HMM never sees these rows):
    - daily HOSTILE / NO_TRADE → intraday nullified
    - open_auction_bleed → skipped (null); callers apply override_intraday_regime
    """
    daily_classified = classify_daily_regime(daily_features)

    result = (
        intraday_features.with_columns(_session_day=pl.col("date").dt.date())
        .join(
            daily_classified.select(["date", "daily_regime"]),
            left_on="_session_day",
            right_on="date",
            how="left",
        )
        .drop("_session_day")
    )

    # Same gate as fit: tradeable daily days and non-bleed bars only.
    valid_mask = pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES) & ~open_auction_bleed_expr('date')
    valid_intraday = result.filter(valid_mask)

    if valid_intraday.height > 0:
        valid_preds = hmm_model.predict(valid_intraday, apply_hysteresis=apply_hysteresis)
        result = result.join(
            valid_preds.select(["date", "intraday_regime_raw", "intraday_regime"]),
            on="date",
            how="left",
        )
    else:
        result = result.with_columns(
            pl.lit(None).alias("intraday_regime_raw"),
            pl.lit(None).alias("intraday_regime"),
        )

    return result


def log_hmm_mlflow(
    hmm_model: IntradayHMMRegimeModel,
    *,
    train_valid: pl.DataFrame,
    test_valid: pl.DataFrame,
    apply_hysteresis: bool,
) -> None:
    """
    Log Gemini-approved HMM params/metrics to the active MLflow run.

    Autolog is intentionally not used — hmmlearn is not covered usefully by
    mlflow.sklearn.autolog (it only captures nested KMeans init noise).
    """
    m = hmm_model.model
    mlflow.log_params(
        {
            "hmm_n_components": hmm_model.n_components,
            "hmm_covariance_type": m.covariance_type,
            "hmm_n_iter_config": hmm_model.n_iter,
            "hmm_random_state": hmm_model.random_state,
            "hmm_init_params": m.init_params,
            "feature_cols": ",".join(DEFAULT_FEATURE_COLS),
            "apply_hysteresis": apply_hysteresis,
        }
    )

    if not hmm_model.is_fitted:
        return

    metrics = hmm_model.fit_diagnostics()

    train_ll, n_train = hmm_model.score(train_valid)
    test_ll, n_test = hmm_model.score(test_valid)

    if n_train > 0 and np.isfinite(train_ll):
        metrics["train_loglik_total"] = train_ll
        metrics["train_loglik_per_sample"] = train_ll / n_train
        k = int(metrics["hmm_n_free_params"])
        # AIC/BIC use total log-likelihood; only comparable under same features/data.
        metrics["hmm_aic"] = -2.0 * train_ll + 2.0 * k
        metrics["hmm_bic"] = -2.0 * train_ll + k * float(np.log(n_train))

    if n_test > 0 and np.isfinite(test_ll):
        metrics["test_loglik_per_sample"] = test_ll / n_test

    # Trend flip rate on raw decoded test states (pre-hysteresis), session-aware.
    # test_valid is already cascade-gated (no open-auction bleed / non-tradeable days).
    if test_valid.height > 0:
        ordered, _, lengths = IntradayHMMRegimeModel.prepare_sequences(
            test_valid, drop_nonfinite=False
        )
        if ordered.height > 0:
            preds = hmm_model.predict(ordered, apply_hysteresis=False)
            decoded = preds.filter(pl.col("intraday_regime_raw").is_not_null())
            metrics["test_trend_flip_rate"] = IntradayHMMRegimeModel.trend_flip_rate(
                decoded["intraday_regime_raw"].to_list(), lengths
            )

    for key, value in metrics.items():
        if value is not None and np.isfinite(value):
            mlflow.log_metric(key, float(value))


def run_pipeline(
    data_dir: Path,
    config_path: Path,
    train_period: str,
    test_period: str,
):
    mlflow.set_experiment("Regime_Pipeline")
    apply_hysteresis = True
    with mlflow.start_run(run_name=f"Regime_{train_period}_{test_period}"):
        mlflow.log_param("train_period", train_period)
        mlflow.log_param("test_period", test_period)
        mlflow.log_param("data_dir", str(data_dir))
        mlflow.log_param("config_path", str(config_path))

        train_start, train_end = parse_period_range(train_period)
        test_start, test_end = parse_period_range(test_period)

        load_start = min(train_start, test_start)
        load_end = max(train_end, test_end)

        print(f"Loading regime data from {load_start} to {load_end}...")
        vix_daily, market_daily, market_15m, nifty100_daily_dfs = load_regime_data(
            data_dir=data_dir,
            config_path=config_path,
            start_period=load_start,
            end_period=load_end,
        )

        print("Building regime features...")
        daily_features, intraday_features = build_regime_features(
            vix_daily, market_daily, market_15m, nifty100_daily_dfs
        )

        print(f"Splitting data into train ({train_period}) and test ({test_period})...")

        daily_features_train = filter_by_period(
            daily_features, train_start, train_end, datetime_col="date"
        )
        daily_features_test = filter_by_period(
            daily_features, test_start, test_end, datetime_col="date"
        )

        intraday_features_train = filter_by_period(
            intraday_features, train_start, train_end, datetime_col="date"
        )
        intraday_features_test = filter_by_period(
            intraday_features, test_start, test_end, datetime_col="date"
        )

        print(
            f"   Train daily shape: {daily_features_train.shape}, "
            f"Test daily shape: {daily_features_test.shape}"
        )
        print(
            f"   Train intraday shape: {intraday_features_train.shape}, "
            f"Test intraday shape: {intraday_features_test.shape}"
        )

        mlflow.log_metric("train_daily_size", daily_features_train.height)
        mlflow.log_metric("test_daily_size", daily_features_test.height)
        mlflow.log_metric("train_intraday_size", intraday_features_train.height)
        mlflow.log_metric("test_intraday_size", intraday_features_test.height)

        if len(daily_features_train) == 0 or len(daily_features_test) == 0:
            print("Error: Train or test daily dataframe is empty. Check your periods.")
            sys.exit(1)

        print("Fitting Intraday HMM on train data (applying daily cascade filter)...")
        hmm_model = fit_intraday_hmm(
            daily_features_train,
            intraday_features_train,
            random_state=42,
            n_iter=100,
        )

        train_valid = cascade_valid_intraday(daily_features_train, intraday_features_train)
        test_valid = cascade_valid_intraday(daily_features_test, intraday_features_test)
        log_hmm_mlflow(
            hmm_model,
            train_valid=train_valid,
            test_valid=test_valid,
            apply_hysteresis=apply_hysteresis,
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
            pickle.dump(hmm_model, tmp)
            tmp_path = tmp.name
        mlflow.log_artifact(tmp_path, "model")
        Path(tmp_path).unlink()

        print("Predicting Regimes on test data (applying cascade gates)...")
        results = predict_intraday_hmm(
            daily_features_test,
            intraday_features_test,
            hmm_model,
            apply_hysteresis=apply_hysteresis,
        )

        # Open-auction hard rule applied here (not inside the HMM), like daily filters.
        results = override_intraday_regime(results)

        print("\nPipeline finished. Test Set Stats:")
        print("Daily Regime Counts:")
        daily_counts = results.group_by("daily_regime").len().sort("len", descending=True)
        print(daily_counts.to_dict(as_series=False))

        for row in daily_counts.iter_rows(named=True):
            regime_name = row["daily_regime"] if row["daily_regime"] else "null"
            mlflow.log_metric(f"daily_count_{regime_name}", row["len"])

        print("\nIntraday Regime Counts:")
        intraday_counts = (
            results.group_by("intraday_regime").len().sort("len", descending=True)
        )
        print(intraday_counts.to_dict(as_series=False))

        for row in intraday_counts.iter_rows(named=True):
            regime_name = row["intraday_regime"] if row["intraday_regime"] else "null"
            mlflow.log_metric(f"intraday_count_{regime_name}", row["len"])

        print("\nCross-tabulation (Daily vs Intraday):")
        cross_tab = results.group_by(["daily_regime", "intraday_regime"]).len().sort(
            ["daily_regime", "len"], descending=[False, True]
        )
        print(cross_tab.to_dict(as_series=False))

        print("\nRun `mlflow ui` in your terminal to view the experiment tracking.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the Algo Trading Regime Pipeline workflow"
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
    )
