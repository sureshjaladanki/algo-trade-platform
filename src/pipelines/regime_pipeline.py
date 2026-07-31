import argparse
import pickle
import sys
import tempfile
from pathlib import Path

import mlflow
import polars as pl

from src.pipelines.build_regime_features import build_regime_features
from src.regime.daily import classify_daily_regime
from src.regime.intraday import IntradayHMMRegime
from src.regime.types import DailyRegime
from src.utils.date import filter_by_period, parse_period_range


def fit_intraday_hmm(
    daily_features: pl.DataFrame, 
    intraday_features: pl.DataFrame,
    random_state: int = 42,
    n_iter: int = 100
) -> IntradayHMMRegime:
    """
    Fits the intraday HMM model only on data that passes the daily regime filter.
    Returns the fitted IntradayHMMRegime model, which can be logged to MLflow.
    """
    # 1. Classify daily regime
    daily_classified = classify_daily_regime(daily_features)
    
    # 2. Filter days that are SUPPORTIVE or AMBIGUOUS
    valid_days = daily_classified.filter(
        pl.col("daily_regime").is_in([DailyRegime.SUPPORTIVE.value, DailyRegime.AMBIGUOUS.value])
    ).select(["date", "symbol"])
    
    # 3. Join with intraday features to filter
    valid_intraday = intraday_features.join(valid_days, on=["date", "symbol"], how="inner")
    
    hmm = IntradayHMMRegime(random_state=random_state, n_iter=n_iter)
    
    if valid_intraday.height == 0:
        print("No valid intraday data to fit HMM. Check daily features and thresholds.")
        return hmm
        
    # 4. Fit HMM on valid intraday data
    hmm.fit(valid_intraday)
    return hmm

def predict_intraday_hmm(
    daily_features: pl.DataFrame, 
    intraday_features: pl.DataFrame,
    hmm_model: IntradayHMMRegime,
    apply_hysteresis: bool = True
) -> pl.DataFrame:
    """
    Predicts both daily and intraday regimes.
    Applies cascade gates: if daily is HOSTILE or NO_TRADE, intraday is nullified.
    Optimized to only run HMM prediction on SUPPORTIVE or AMBIGUOUS days.
    """
    # 1. Classify daily regime
    daily_classified = classify_daily_regime(daily_features)
    
    # 2. Join daily regime to intraday features to apply cascade gate
    result = intraday_features.join(
        daily_classified.select(["date", "symbol", "daily_regime"]), 
        on=["date", "symbol"], 
        how="left"
    )
    
    # 3. Filter intraday features to only those where daily regime is SUPPORTIVE or AMBIGUOUS
    valid_mask = pl.col("daily_regime").is_in([DailyRegime.SUPPORTIVE.value, DailyRegime.AMBIGUOUS.value])
    valid_intraday = result.filter(valid_mask)
    
    # 4. Predict intraday regime ONLY for valid data
    if valid_intraday.height > 0:
        valid_preds = hmm_model.predict(valid_intraday, apply_hysteresis=apply_hysteresis)
        
        # 5. Join predictions back to the main result
        result = result.join(
            valid_preds.select(["datetime", "symbol", "intraday_regime"]),
            on=["datetime", "symbol"],
            how="left"
        )
    else:
        # If no valid data, just add a null intraday_regime column
        result = result.with_columns(pl.lit(None).alias("intraday_regime"))
        
    return result

def run_pipeline(
    data_dir: Path,
    symbols_config_path: Path,
    train_period: str,
    test_period: str,
):
    mlflow.set_experiment("Regime_Pipeline")
    with mlflow.start_run(run_name=f"Regime_{train_period}_{test_period}"):
        # Log parameters
        mlflow.log_param("train_period", train_period)
        mlflow.log_param("test_period", test_period)
        mlflow.log_param("data_dir", str(data_dir))
        mlflow.log_param("symbols_config_path", str(symbols_config_path))
        
        train_start, train_end = parse_period_range(train_period)
        test_start, test_end = parse_period_range(test_period)
        
        # Combine start and end to load data once
        load_start = min(train_start, test_start)
        load_end = max(train_end, test_end)
        
        print(f"Loading data and building features from {load_start} to {load_end}...")
        daily_features, intraday_features = build_regime_features(
            data_dir=data_dir,
            symbols_config_path=symbols_config_path,
            start_period=load_start,
            end_period=load_end
        )
        
        print(f"Splitting data into train ({train_period}) and test ({test_period})...")
        
        # Using filter_by_period needs datetime column for intraday, and date for daily
        daily_features_train = filter_by_period(daily_features, train_start, train_end, datetime_col="date")
        daily_features_test = filter_by_period(daily_features, test_start, test_end, datetime_col="date")
        
        intraday_features_train = filter_by_period(intraday_features, train_start, train_end, datetime_col="datetime")
        intraday_features_test = filter_by_period(intraday_features, test_start, test_end, datetime_col="datetime")
        
        print(f"   Train daily shape: {daily_features_train.shape}, Test daily shape: {daily_features_test.shape}")
        print(f"   Train intraday shape: {intraday_features_train.shape}, Test intraday shape: {intraday_features_test.shape}")
        
        mlflow.log_metric("train_daily_size", daily_features_train.height)
        mlflow.log_metric("test_daily_size", daily_features_test.height)
        mlflow.log_metric("train_intraday_size", intraday_features_train.height)
        mlflow.log_metric("test_intraday_size", intraday_features_test.height)
        
        if len(daily_features_train) == 0 or len(daily_features_test) == 0:
            print("Error: Train or test daily dataframe is empty. Check your periods.")
            sys.exit(1)
            
        print("Fitting Intraday HMM on train data (applying daily cascade filter)...")
        hmm_model = fit_intraday_hmm(daily_features_train, intraday_features_train, random_state=42, n_iter=100)
        
        mlflow.log_param("hmm_n_components", hmm_model.n_components)
        
        # Save model as artifact
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp:
            pickle.dump(hmm_model, tmp)
            tmp_path = tmp.name
        mlflow.log_artifact(tmp_path, "model")
        Path(tmp_path).unlink()
        
        print("Predicting Regimes on test data (applying cascade gates)...")
        results = predict_intraday_hmm(daily_features_test, intraday_features_test, hmm_model)
        
        print("\nPipeline finished. Test Set Stats:")
        print("Daily Regime Counts:")
        daily_counts = results.group_by("daily_regime").len().sort("len", descending=True)
        print(daily_counts.to_dict(as_series=False))
        
        for row in daily_counts.iter_rows(named=True):
            regime_name = row["daily_regime"] if row["daily_regime"] else "null"
            mlflow.log_metric(f"daily_count_{regime_name}", row["len"])
        
        print("\nIntraday Regime Counts:")
        intraday_counts = results.group_by("intraday_regime").len().sort("len", descending=True)
        print(intraday_counts.to_dict(as_series=False))
        
        for row in intraday_counts.iter_rows(named=True):
            regime_name = row["intraday_regime"] if row["intraday_regime"] else "null"
            mlflow.log_metric(f"intraday_count_{regime_name}", row["len"])
        
        print("\nCross-tabulation (Daily vs Intraday):")
        cross_tab = results.group_by(["daily_regime", "intraday_regime"]).len().sort(["daily_regime", "len"], descending=[False, True])
        print(cross_tab.to_dict(as_series=False))
        
        print("\nSector-wise Intraday Regimes (non-null):")
        sector_tab = results.filter(pl.col("intraday_regime").is_not_null()).group_by(["sector", "intraday_regime"]).len().sort(["sector", "len"], descending=[False, True])
        print(sector_tab.to_dict(as_series=False))
        
        print("\nRun `mlflow ui` in your terminal to view the experiment tracking.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Algo Trading Regime Pipeline workflow")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN", help="Path to the GOLDEN data directory")
    parser.add_argument("--config", type=str, default="config/trade_sectoral_symbols.yml", help="Path to the sectoral symbols config")
    parser.add_argument(
        "--train-period",
        type=str,
        required=True,
        help="Training period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy (e.g. 03/2020-03/2021)",
    )
    parser.add_argument(
        "--test-period",
        type=str,
        required=True,
        help="Test period: yyyy-yyyy (e.g. 2015-2018) or mm/yyyy-mm/yyyy (e.g. 03/2020-03/2021)",
    )
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    symbols_config_path = Path(args.config)
    
    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist.")
        sys.exit(1)
        
    if not symbols_config_path.exists():
        print(f"Error: Config file {symbols_config_path} does not exist.")
        sys.exit(1)
         
    run_pipeline(
        data_dir=data_dir, 
        symbols_config_path=symbols_config_path,
        train_period=args.train_period, 
        test_period=args.test_period
    )
