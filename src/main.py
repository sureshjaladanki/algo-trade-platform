import argparse
import sys
from pathlib import Path

# Add src to path if needed or just use relative imports assuming running from src
from data import load_csv_data
from symbol_features import build_symbol_features
from target import generate_target
from model import train_xgboost_model

def run_pipeline(csv_path: str):
    print(f"1. Loading CSV data from {csv_path}...")
    df = load_csv_data(csv_path, datetime_col="timestamp")
    print(f"   Loaded {len(df)} rows.")

    print("2. Building 1m and 5m features...")
    df = build_symbol_features(df, datetime_col="timestamp")
    print(f"   Features built. Data shape: {df.shape}")
    
    print("3. Generating classification target (Next 5-min direction)...")
    df = generate_target(df, lookahead_minutes=5)
    print(f"   Target generated. Data shape after removing target nulls: {df.shape}")
    
    print("4. Training XGBoost model and logging to MLflow...")
    feature_cols = [
        "vwap", "ema_14", "minute_of_day", "bb_pct_b", "vol_z_score", 
        "rsi_5m", "adx_5m"
    ]
    
    clf, acc = train_xgboost_model(df, feature_cols=feature_cols, target_col="target")
    print("====================================")
    print(f"Pipeline finished. Final test accuracy: {acc:.4f}")
    print("Run `mlflow ui` in your terminal to view the experiment tracking.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Algo Trading ML Platform pipeline")
    parser.add_argument("--data", type=str, required=True, help="Path to the 1-minute candle CSV data")
    args = parser.parse_args()
    
    if not Path(args.data).exists():
        print(f"Error: Data file {args.data} does not exist.")
        sys.exit(1)
         
    run_pipeline(args.data)
