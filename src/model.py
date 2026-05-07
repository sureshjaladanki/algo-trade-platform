import mlflow
import xgboost as xgb
import polars as pl
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import List, Tuple

def train_xgboost_model(
    df: pl.DataFrame, 
    feature_cols: List[str], 
    target_col: str = "target", 
    test_size: float = 0.2
) -> Tuple[xgb.XGBClassifier, float]:
    """
    Trains an XGBoost classification model using a time-series split.
    Logs parameters, metrics, and the model to MLflow.
    """
    # Ensure there are no nulls in features or target before training
    df = df.drop_nulls(subset=feature_cols + [target_col])
    
    n_rows = len(df)
    train_size = int(n_rows * (1 - test_size))
    
    # Time-series split: earlier data for training, later data for testing
    df_train = df.head(train_size)
    df_test = df.tail(n_rows - train_size)
    
    # Convert to numpy arrays for sklearn/xgboost
    X_train = df_train.select(feature_cols).to_numpy()
    y_train = df_train.select(target_col).to_numpy().ravel()
    
    X_test = df_test.select(feature_cols).to_numpy()
    y_test = df_test.select(target_col).to_numpy().ravel()
    
    # MLflow tracking
    mlflow.set_experiment("Algo_Trading_Experiment")
    
    print(f"Training on {train_size} samples, testing on {len(df_test)} samples.")
    
    with mlflow.start_run():
        params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "max_depth": 5,
            "learning_rate": 0.05,
            "n_estimators": 100,
            "random_state": 42
        }
        mlflow.log_params(params)
        
        clf = xgb.XGBClassifier(**params)
        clf.fit(X_train, y_train)
        
        y_pred = clf.predict(X_test)
        
        # Calculate metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        metrics = {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1_score": f1
        }
        mlflow.log_metrics(metrics)
        
        # Log the model
        mlflow.xgboost.log_model(clf, "xgboost_model")
        
        print(f"Model trained successfully.")
        print(f"Accuracy: {acc:.4f}, Precision: {prec:.4f}, Recall: {rec:.4f}, F1: {f1:.4f}")
        
    return clf, acc
