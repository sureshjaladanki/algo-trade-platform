import mlflow
import pandas as pd
import xgboost as xgb
import polars as pl
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import List, Tuple, Optional, Dict
import numpy as np
from .constants import DEFAULT_TARGET_CLASSES

def train_xgboost_model(
    df_train: pl.DataFrame, 
    df_test: pl.DataFrame,
    feature_cols: List[str], 
    target_col: str = "target", 
    *,
    target_classes: Dict = DEFAULT_TARGET_CLASSES,
) -> Tuple[xgb.XGBClassifier, float]:
    """
    Trains an XGBoost classification model using provided train and test sets.
    Logs parameters, metrics, and the model to MLflow.

    Categorical columns (e.g. 'sector') must already be encoded as `pl.Enum`
    or `pl.Categorical` upstream; they are passed to XGBoost via pandas
    `category` dtype so that `enable_categorical=True` can pick them up
    automatically without a separate categorical_features list.
    """
    # Ensure there are no nulls in features or target before training
    df_train = df_train.drop_nulls(subset=feature_cols + [target_col])
    df_test = df_test.drop_nulls(subset=feature_cols + [target_col])

    # Pandas DataFrames preserve per-column dtypes (incl. `category`), which
    # XGBoost reads to decide which columns are categorical.
    X_train = df_train.select(feature_cols).to_pandas()
    y_train = df_train.select(target_col).to_numpy().ravel()

    X_test = df_test.select(feature_cols).to_pandas()
    y_test = df_test.select(target_col).to_numpy().ravel()

    class_weights = {int(v.get("num")): float(v.get("weight")) for v in target_classes.values()}
    sample_weights = np.array([class_weights.get(int(t), 1.0) for t in y_train], dtype=float)

    cat_cols = [c for c in X_train.columns if isinstance(X_train[c].dtype, pd.CategoricalDtype)]

    # MLflow tracking
    mlflow.set_experiment("Algo_Trading_Experiment")
    
    print(f"Training on {len(df_train)} samples, testing on {len(df_test)} samples.")
    if cat_cols:
        print(f"Categorical features (auto-detected from dtype): {cat_cols}")

    with mlflow.start_run():
        # Log target metadata for reproducibility (when provided)
        if target_classes:
            mlflow.log_dict(target_classes, "target_classes.json")


        params = {
            "objective": "multi:softprob",  # Changed from binary:logistic
            "num_class": len(target_classes), # number of classes inferred from data
            "eval_metric": "mlogloss",     # Use multi-class logloss
            "max_depth": 5,
            "learning_rate": 0.05,
            "n_estimators": 100,
            "random_state": 42,
            "subsample": 0.8,           # Critical for generalization
            "colsample_bytree": 0.8,    # Critical for feature robustness
            # Required for native categorical handling in XGBoost 2.x.
            # `hist` is also the default in 2.x but we pin it explicitly
            # because `enable_categorical=True` requires it.
            "enable_categorical": True,
            "tree_method": "hist",
        }
        mlflow.log_params(params)

        # Persist the category->code mapping for each categorical column so
        # downstream inference can rebuild an identical encoding even if the
        # YAML config drifts.
        for c in cat_cols:
            mlflow.log_dict(
                {"column": c, "categories": list(X_train[c].cat.categories)},
                f"categories_{c}.json",
            )

        clf = xgb.XGBClassifier(**params)
        clf.fit(X_train, y_train, sample_weight=sample_weights)

        y_pred = clf.predict(X_test)
        
        # Calculate metrics
        acc = accuracy_score(y_test, y_pred)
        # `long_target` is multiclass (e.g. 0/1/2), so we must use a multiclass average.
        prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
        f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
        
        metrics = {
            "accuracy": acc,
            "precision_macro": prec_macro,
            "recall_macro": rec_macro,
            "f1_macro": f1_macro,
        }
        mlflow.log_metrics(metrics)
        
        # Log the model
        mlflow.xgboost.log_model(clf, "xgboost_model")
        
        print(f"Model trained successfully.")
        print(
            "Accuracy: "
            f"{acc:.4f} | "
            f"Macro P/R/F1: {prec_macro:.4f}/{rec_macro:.4f}/{f1_macro:.4f} "
        )
        
    return clf, acc
