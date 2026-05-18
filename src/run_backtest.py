import argparse
import sys
from pathlib import Path
from typing import Optional

import mlflow

from .trade_features import build_all_features
from .utils.date import filter_by_period, parse_period
from .utils import load_config
from .constants import MODEL_FEATURE_COLS
from .backtest import run_vectorbt_backtest_sweep

def run_backtest_pipeline(
    data_dir: Path,
    symbols_config_path: Path,
    training_config_path: Path,
    test_period: str,
    model_uri: Optional[str] = None,
):
    start_year, end_year = parse_period(test_period)

    final_df = build_all_features(
        data_dir=data_dir,
        symbols_config_path=symbols_config_path,
        training_config_path=training_config_path,
        start_year=start_year,
        end_year=end_year,
    )

    print(f"Filtering data for test period ({test_period})...")
    df_test = filter_by_period(final_df, start_year, end_year)

    if len(df_test) == 0:
        print("Error: Test dataframe is empty. Check your periods.")
        sys.exit(1)

    mlflow.set_experiment("Algo_Trading_Experiment")
    experiment = mlflow.get_experiment_by_name("Algo_Trading_Experiment")
    if experiment is None:
        print("Error: MLflow experiment 'Algo_Trading_Experiment' not found.")
        sys.exit(1)

    if model_uri is None:
        print("Loading the latest model from MLflow...")
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=1,
        )
        if runs.empty:
            print("Error: No runs found in the experiment.")
            sys.exit(1)

        latest_run_id = runs.iloc[0].run_id
        print(f"Latest run ID: {latest_run_id}")
        model_uri = f"runs:/{latest_run_id}/model"
    else:
        print(f"Loading model from {model_uri}...")

    clf = mlflow.xgboost.load_model(model_uri)

    training_config = load_config(training_config_path)
    target_classes = training_config.get("target", {}).get("classes", {})

    feature_cols = [col for col in MODEL_FEATURE_COLS if col in df_test.columns]
    
    target_col = training_config.get("target", {}).get("column", "long_target")
    subset_cols = feature_cols + [target_col] if target_col in df_test.columns else feature_cols
    
    # Drop nulls as done in training
    df_test = df_test.drop_nulls(subset=subset_cols)

    X_test = df_test.select(feature_cols).to_pandas()

    print("Generating predictions...")
    y_prob = clf.predict_proba(X_test)

    tp_class = int(target_classes.get("take_profit", {}).get("num", 2))
    tp_idx = list(clf.classes_).index(tp_class)
    tp_probs = y_prob[:, tp_idx]

    entry_thresholds = [0.6, 0.65, 0.7, 0.75]
    exit_thresholds = [0.3, 0.35, 0.4, 0.45]

    print(f"Running vectorBT backtest sweep over "
          f"{len(entry_thresholds) * len(exit_thresholds)} combinations...")

    sweep_results = run_vectorbt_backtest_sweep(
        df_test,
        tp_probs,
        entry_thresholds,
        exit_thresholds,
        backtest_context=training_config
    )

    if sweep_results.empty:
        print("Backtest returned no results.")
        sys.exit(0)

    # Convert results dataframe to a list of dicts for printing
    results = sweep_results.to_dict("records")
    metric_keys = [k for k in results[0].keys()
                   if k not in ("entry_threshold", "exit_threshold")]

    print("====================================")
    print("Backtest Sweep Results:")
    header = f"{'entry':>6} {'exit':>6}  " + "  ".join(f"{k:>22}" for k in metric_keys)
    print(header)
    print("-" * len(header))
    for row in results:
        cells = "  ".join(f"{row.get(k, float('nan')):>22.4f}" for k in metric_keys)
        print(f"{row['entry_threshold']:>6.2f} {row['exit_threshold']:>6.2f}  {cells}")

    sort_key = next((k for k in metric_keys if k.endswith("sharpe_ratio")), metric_keys[0])
    best = max(results, key=lambda r: r.get(sort_key, float("-inf")))
    print("------------------------------------")
    print(f"Best by {sort_key}: entry={best['entry_threshold']}, exit={best['exit_threshold']}")
    for k in metric_keys:
        if k in best:
            print(f"  {k}: {best[k]:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run backtest using an MLflow model (latest run by default)"
    )
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN", help="Path to the GOLDEN data directory")
    parser.add_argument("--config", type=str, default="config/trade_sectoral_symbols.yml", help="Path to the sectoral symbols config")
    parser.add_argument("--training-config", type=str, default="config/model_training.yml", help="Path to the model training config")
    parser.add_argument("--test-period", type=str, required=True, help="Test period: yyyy or yyyy-yy (ex: 2015, 2015-18)")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        metavar="URI",
        help="MLflow model URI (e.g. runs:/<run_id>/model). Default: latest run in Algo_Trading_Experiment",
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
         
    run_backtest_pipeline(
        data_dir,
        symbols_config_path,
        training_config_path,
        args.test_period,
        model_uri=args.model,
    )
