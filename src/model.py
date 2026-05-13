import mlflow
import pandas as pd
import xgboost as xgb
import polars as pl
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import List, Tuple, Dict
import numpy as np

from .backtest import run_vectorbt_backtest
from .constants import DEFAULT_TARGET_CLASSES


def train_xgboost_model(
    df_train: pl.DataFrame, 
    df_test: pl.DataFrame,
    feature_cols: List[str], 
    target_col: str = "target", 
    *,
    training_context: Dict = {
        "target_classes": DEFAULT_TARGET_CLASSES,
        "take_profit_natr": 2.0,
        "take_profit_pct": 0.35,
        "stop_loss_natr": 1.5,
        "natr_col": "natr_5m",
        "stop_loss_pct": 0.25,
    },
) -> Tuple[xgb.XGBClassifier, float]:
    """
    Trains an XGBoost classification model using provided train and test sets.
    Logs parameters, metrics, and the model to MLflow.

    Categorical columns (e.g. 'sector') must already be encoded as `pl.Enum`
    or `pl.Categorical` upstream; they are passed to XGBoost via pandas
    `category` dtype so that `enable_categorical=True` can pick them up
    automatically without a separate categorical_features list.
    """

    # Replace inf and -inf with nulls in float feature columns so they get dropped
    float_feature_cols = [c for c in feature_cols if df_train[c].dtype in (pl.Float32, pl.Float64)]
    if float_feature_cols:
        exprs = [
            pl.when(pl.col(c).is_infinite()).then(None).otherwise(pl.col(c)).alias(c)
            for c in float_feature_cols
        ]
        df_train = df_train.with_columns(exprs)
        df_test = df_test.with_columns(exprs)

    # Ensure there are no nulls in features or target before training
    df_train = df_train.drop_nulls(subset=feature_cols + [target_col])
    df_test = df_test.drop_nulls(subset=feature_cols + [target_col])

    # Pandas DataFrames preserve per-column dtypes (incl. `category`), which
    # XGBoost reads to decide which columns are categorical.
    X_train = df_train.select(feature_cols).to_pandas()
    X_test = df_test.select(feature_cols).to_pandas()

    # Cast integer columns to float64 to avoid MLflow schema warnings about missing values
    int_cols = X_train.select_dtypes(include=['int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64']).columns
    if len(int_cols) > 0:
        X_train[int_cols] = X_train[int_cols].astype("float64")
        X_test[int_cols] = X_test[int_cols].astype("float64")

    y_train = df_train.select(target_col).to_numpy().ravel()
    y_test = df_test.select(target_col).to_numpy().ravel()

    class_weights = {int(v.get("num")): float(v.get("weight")) for v in training_context["target_classes"].values()}
    sample_weights = np.array([class_weights.get(int(t), 1.0) for t in y_train], dtype=float)

    cat_cols = [c for c in X_train.columns if isinstance(X_train[c].dtype, pd.CategoricalDtype)]

    # MLflow tracking
    mlflow.set_experiment("Algo_Trading_Experiment")
    # Avoid deprecated model logging behavior in MLflow autolog.
    # We'll log the model ourselves in a version-compatible way.
    mlflow.xgboost.autolog(log_models=False)

    print(f"Training on {len(df_train)} samples, testing on {len(df_test)} samples.")
    if cat_cols:
        print(f"Categorical features (auto-detected from dtype): {cat_cols}")

    with mlflow.start_run():
        # Log target metadata for reproducibility (when provided)
        mlflow.log_dict(training_context["target_classes"], "target_classes.json")
        print(f"logged target classes to MLflow.")

        params = {
            "objective": "multi:softprob",  # Changed from binary:logistic
            "num_class": len(training_context["target_classes"]), # number of classes inferred from data
            "eval_metric": "mlogloss",     # Use multi-class logloss
            "max_depth": 7,
            "learning_rate": 0.02,
            "n_estimators": 300,
            "random_state": 42,
            "subsample": 0.8,           # Critical for generalization
            "colsample_bytree": 0.8,    # Critical for feature robustness
            # Required for native categorical handling in XGBoost 2.x.
            # `hist` is also the default in 2.x but we pin it explicitly
            # because `enable_categorical=True` requires it.
            "enable_categorical": True,
            "tree_method": "hist",
        }

        # Persist the category->code mapping for each categorical column so
        # downstream inference can rebuild an identical encoding even if the
        # YAML config drifts.
        for c in cat_cols:
            mlflow.log_dict(
                {"column": c, "categories": list(X_train[c].cat.categories)},
                f"categories_{c}.json",
            )

        print(f"Training XGBoost model.")
        clf = xgb.XGBClassifier(**params)
        clf.fit(X_train, y_train, sample_weight=sample_weights)

        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)
        
        tp_class = int(training_context["target_classes"]["take_profit"]["num"])
        tp_idx = list(clf.classes_).index(tp_class)
        tp_probs = y_prob[:, tp_idx]
        
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
        mlflow.xgboost.log_model(clf, name="model")

        print(f"Model trained successfully.")
        print(
            "Accuracy: "
            f"{acc:.4f} | "
            f"Macro P/R/F1: {prec_macro:.4f}/{rec_macro:.4f}/{f1_macro:.4f} "
        )
        
        natr_col = training_context["natr_col"]
        stop_loss_natr = float(training_context["stop_loss_natr"])
        take_profit_natr = float(training_context["take_profit_natr"])
        take_profit_pct = float(training_context.get("take_profit_pct", 0.35))

        # NATR-scaled stop-loss exit: previous-bar return breaches -stop_loss_natr * NATR.
        # Shift is partitioned by symbol so the lag never crosses instrument boundaries.
        stop_loss_exit = df_test.select(
            (
                (pl.col("close") / pl.col("close").shift(1).over("symbol") - 1.0)
                <= -pl.col(natr_col) * stop_loss_natr
            )
            .fill_null(False)
            .alias("ret_exit")
        ).to_series().to_numpy()

        take_profit_above_threshold = df_test.select(
            (pl.col(natr_col) * take_profit_natr > take_profit_pct)
            .fill_null(False)
            .alias("natr_tp_ok")
        ).to_series().to_numpy()

        entries = pl.Series("entries", (tp_probs > 0.65) & take_profit_above_threshold)
        exits = pl.Series("exits", (tp_probs < 0.4) | stop_loss_exit)
        
        # Run vectorBT backtest
        bt_metrics = run_vectorbt_backtest(df_test, entries, exits, backtest_context={
            "stop_loss_pct": training_context["stop_loss_pct"],
            "metric_prefix": "backtest_",
        })
        mlflow.log_metrics(bt_metrics)
        
        print(f"Model backtest results logged to MLflow.")
        for k, v in bt_metrics.items():
            print(f"  {k}: {v:.4f}")

    return clf, acc
