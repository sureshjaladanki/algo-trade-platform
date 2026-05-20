import argparse
import sys
from pathlib import Path


from .trade_features import build_all_features
from .utils.date import filter_by_period, parse_period_range
from .model import train_xgboost_model
from .utils import load_config
from .constants import MODEL_FEATURE_COLS

# Filtering the final final_df is correct logically, 
# but it’s slower because you compute features for years you’ll throw away.
def run_pipeline(
    data_dir: Path,
    symbols_config_path: Path,
    training_config_path: Path,
    train_period: str,
    test_period: str,
):
    train_start, train_end = parse_period_range(train_period)
    test_start, test_end = parse_period_range(test_period)

    # Filter raw inputs early for speed/memory, but keep a warmup window so
    # rolling features (EMA/BB/RSI/ADX/etc.) have enough history
    
    print(f"Loading training configuration from {training_config_path}...")
    training_config = load_config(training_config_path)

    final_df = build_all_features(
        data_dir=data_dir,
        symbols_config_path=symbols_config_path,
        training_config_path=training_config_path,
        start_period=train_start,
        end_period=test_end,
    )
    
    print(f"4. Splitting data into train ({train_period}) and test ({test_period})...")
    df_train = filter_by_period(final_df, train_start, train_end)
    df_test = filter_by_period(final_df, test_start, test_end)
    
    print(f"   Train shape: {df_train.shape}, Test shape: {df_test.shape}")
    
    if len(df_train) == 0 or len(df_test) == 0:
        print("Error: Train or test dataframe is empty. Check your periods.")
        sys.exit(1)
    
    print("5. Training XGBoost model and logging to MLflow...")
    feature_cols = MODEL_FEATURE_COLS
    
    # Ensure all feature columns exist
    missing_cols = [col for col in feature_cols if col not in final_df.columns]
    if missing_cols:
        print(f"Warning: Missing feature columns: {missing_cols}")
        feature_cols = [col for col in feature_cols if col in final_df.columns]
    
    clf, acc = train_xgboost_model(
        df_train,
        df_test,
        feature_cols=feature_cols,
        target_col="long_target",
        training_context=training_config,
    )
    print("====================================")
    print(f"Pipeline finished. Final test accuracy: {acc:.4f}")
    print("Run `mlflow ui` in your terminal to view the experiment tracking.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Algo Trading ML Platform pipeline")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN", help="Path to the GOLDEN data directory")
    parser.add_argument("--config", type=str, default="config/trade_sectoral_symbols.yml", help="Path to the sectoral symbols config")
    parser.add_argument("--training-config", type=str, default="config/model_training.yml", help="Path to the model training config")
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
    training_config_path = Path(args.training_config)
    
    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist.")
        sys.exit(1)
        
    if not symbols_config_path.exists():
        print(f"Error: Config file {symbols_config_path} does not exist.")
        sys.exit(1)

    if not training_config_path.exists():
        print(f"Error: Training config file {training_config_path} does not exist.")
        sys.exit(1)
         
    run_pipeline(data_dir, symbols_config_path, training_config_path, args.train_period, args.test_period)
