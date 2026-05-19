import mlflow
import pandas as pd
import xgboost as xgb
import polars as pl
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    precision_recall_fscore_support,
)
from typing import List, Tuple, Dict
import numpy as np

from .backtest import run_vectorbt_backtest
from .constants import DEFAULT_TARGET_CLASSES

# Take-profit probability gates for training-time backtest (see `run_backtest.py` to sweep).
ENTRY_TP_PROB = 0.70
EXIT_TP_PROB = 0.30


def _sector_metric_key(sector: str) -> str:
    """MLflow-safe prefix segment from a sector enum/category value."""
    return (
        str(sector)
        .replace("^", "")
        .replace(".", "_")
        .replace("/", "_")
        .replace(" ", "_")
    )


def _per_class_metrics(
    metrics: Dict[str, float],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_labels: List[int],
    class_num_to_name: Dict[int, str],
    *,
    key_prefix: str = "",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    per_class_prec, per_class_rec, per_class_f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=class_labels,
        average=None,
        zero_division=0,
    )
    for label, precision, recall, f1 in zip(
        class_labels, per_class_prec, per_class_rec, per_class_f1
    ):
        name = class_num_to_name[label]
        metrics[f"{key_prefix}{name}_precision"] = float(precision)
        metrics[f"{key_prefix}{name}_recall"] = float(recall)
        metrics[f"{key_prefix}{name}_f1"] = float(f1)
    return per_class_prec, per_class_rec, per_class_f1


def _generate_metrics(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    X_test: pd.DataFrame,
    class_labels: List[int],
    class_num_to_name: Dict[int, str],
) -> Tuple[float, Dict[str, float], Dict[str, Dict], str, List[str]]:
    """Evaluates metrics and returns formatted summaries."""
    acc = accuracy_score(y_test, y_pred)
    prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
    rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)

    metrics = {
        "accuracy": acc,
        "precision_macro": prec_macro,
        "recall_macro": rec_macro,
        "f1_macro": f1_macro,
    }
    
    per_class_prec, per_class_rec, per_class_f1 = _per_class_metrics(
        metrics,
        y_test,
        y_pred,
        class_labels,
        class_num_to_name,
    )

    sector_summaries: List[str] = []
    sector_metrics: Dict[str, Dict] = {}
    if "sector" in X_test.columns:
        for sector in X_test["sector"].unique():
            mask = (X_test["sector"] == sector).to_numpy()
            y_test_sector = y_test[mask]
            y_pred_sector = y_pred[mask]

            if len(y_test_sector) == 0:
                continue

            sector_key = _sector_metric_key(sector)
            sector_metrics[sector_key] = {
                "n_samples": len(y_test_sector),
                "accuracy": float(accuracy_score(y_test_sector, y_pred_sector)),
                "precision_macro": float(
                    precision_score(
                        y_test_sector, y_pred_sector, average="macro", zero_division=0
                    )
                ),
                "recall_macro": float(
                    recall_score(
                        y_test_sector, y_pred_sector, average="macro", zero_division=0
                    )
                ),
                "f1_macro": float(
                    f1_score(y_test_sector, y_pred_sector, average="macro", zero_division=0)
                ),
            }
            sec_prec, sec_rec, sec_f1 = _per_class_metrics(
                sector_metrics[sector_key],
                y_test_sector,
                y_pred_sector,
                class_labels,
                class_num_to_name,
            )

            sector_per_class = " | ".join(
                f"{class_num_to_name[label]} P/R/F1: {precision:.4f}/{recall:.4f}/{f1:.4f}"
                for label, precision, recall, f1 in zip(class_labels, sec_prec, sec_rec, sec_f1)
            )
            sector_summaries.append(f"  {sector} (n={len(y_test_sector)}): {sector_per_class}")

    per_class_summary = " | ".join(
        f"{class_num_to_name[label]} P/R/F1: {precision:.4f}/{recall:.4f}/{f1:.4f}"
        for label, precision, recall, f1 in zip(
            class_labels, per_class_prec, per_class_rec, per_class_f1
        )
    )
    
    overall_summary = (
        f"Accuracy: {acc:.4f} | "
        f"Macro P/R/F1: {prec_macro:.4f}/{rec_macro:.4f}/{f1_macro:.4f} | "
        f"{per_class_summary}"
    )

    return acc, metrics, sector_metrics, overall_summary, sector_summaries


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
        "early_stopping_rounds": 50,
        "validation_fraction": 0.2,
    },
) -> Tuple[xgb.XGBClassifier, float]:
    """
    Trains an XGBoost classification model using provided train and test sets.
    Logs parameters, metrics, and the model to MLflow.

    By default, the last ``validation_fraction`` of training rows (sorted by
    ``date``, then ``symbol``) is held out for ``eval_metric`` and XGBoost early
    stopping uses ``early_stopping_rounds`` from ``training_context`` (defaults:
    ``constants.DEFAULT_*``). The test set is never used for early stopping. Set
    ``early_stopping_rounds`` to ``0`` to train on the full train set without
    stopping. If the train set is too small or ``date`` is missing, early stopping
    is skipped with a console warning.

    Categorical columns (e.g. 'sector') must already be encoded as `pl.Enum`
    or `pl.Categorical` upstream; they are passed to XGBoost via pandas
    `category` dtype so that `enable_categorical=True` can pick them up
    automatically without a separate categorical_features list.
    """

    # Ensure there are no nulls in features or target before training
    df_train = df_train.drop_nulls(subset=feature_cols + [target_col])
    df_test = df_test.drop_nulls(subset=feature_cols + [target_col])

    patience = int(training_context.get("early_stopping_rounds", 50))
    validation_fraction = float(training_context.get("validation_fraction", 0.2))

    # Chronological split for early stopping validation (80/20 by default)
    sort_keys = ["date"] + (["symbol"] if "symbol" in df_train.columns else [])
    df_sorted = df_train.sort(sort_keys)
    
    validation_size = int(len(df_sorted) * validation_fraction)
    fit_size = len(df_sorted) - validation_size

    df_fit = df_sorted.head(fit_size)
    df_val = df_sorted.tail(validation_size)

    # Pandas DataFrames preserve per-column dtypes (incl. `category`), which
    # XGBoost reads to decide which columns are categorical.
    X_fit = df_fit.select(feature_cols).to_pandas()
    X_val = df_val.select(feature_cols).to_pandas()
    X_test = df_test.select(feature_cols).to_pandas()

    y_fit = df_fit.select(target_col).to_numpy().ravel()
    y_val = df_val.select(target_col).to_numpy().ravel()
    y_test = df_test.select(target_col).to_numpy().ravel()

    class_weights = {int(v.get("num")): float(v.get("weight")) for v in training_context["target_classes"].values()}
    sample_weights = np.array([class_weights.get(int(t), 1.0) for t in y_fit], dtype=float)

    cat_cols = [c for c in X_fit.columns if isinstance(X_fit[c].dtype, pd.CategoricalDtype)]

    # MLflow tracking
    mlflow.set_experiment("Algo_Trading_Experiment")
    # Avoid deprecated model logging behavior in MLflow autolog.
    # We'll log the model ourselves in a version-compatible way.
    mlflow.xgboost.autolog(log_models=False)

    print(f"Training on {fit_size} fit + {validation_size} validation (chronological tail), testing on {len(df_test)} samples.")
    if cat_cols:
        print(f"Categorical features (auto-detected from dtype): {cat_cols}")

    with mlflow.start_run():
        # Log target metadata for reproducibility (when provided)
        mlflow.log_dict(training_context["target_classes"], "target_classes.json")
        print("logged target classes to MLflow.")

        params = {
            "objective": "multi:softprob",
            "num_class": len(training_context["target_classes"]),
            "eval_metric": "mlogloss",
            **training_context.get("xgboost_params", {}),
            "tree_method": "hist",
            "enable_categorical": True,
            "random_state": 42,
        }

        # Persist the category->code mapping for each categorical column so
        # downstream inference can rebuild an identical encoding even if the
        # YAML config drifts.
        for c in cat_cols:
            mlflow.log_dict(
                {"column": c, "categories": list(X_fit[c].cat.categories)},
                f"categories_{c}.json",
            )

        mlflow.log_param("early_stopping_rounds", patience)
        mlflow.log_param("validation_fraction", validation_fraction)

        print("Training XGBoost model.")
        clf = xgb.XGBClassifier(**params, early_stopping_rounds=patience)
        clf.fit(
            X_fit, 
            y_fit, 
            sample_weight=sample_weights,
            eval_set=[(X_val, y_val)],
            verbose=False
        )

        best_iteration = getattr(clf, "best_iteration", getattr(clf, "best_iteration_", None))
        if best_iteration is not None:
            mlflow.log_metric("xgb_best_iteration", int(best_iteration))
        best_score = getattr(clf, "best_score", getattr(clf, "best_score_", None))
        if isinstance(best_score, (int, float)):
            mlflow.log_metric("xgb_best_score", float(best_score))

        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test) 
        
        tp_class = int(training_context["target_classes"]["take_profit"]["num"])
        tp_idx = list(clf.classes_).index(tp_class)
        tp_probs = y_prob[:, tp_idx]
        
        # Calculate metrics
        class_labels = sorted(
            int(v["num"]) for v in training_context["target_classes"].values()
        )
        class_num_to_name = {
            int(v["num"]): name for name, v in training_context["target_classes"].items()
        }
        
        acc, metrics, sector_metrics, overall_summary, sector_summaries = _generate_metrics(
            y_test, y_pred, X_test, class_labels, class_num_to_name
        )

        mlflow.log_metrics(metrics)

        # Log the model
        mlflow.xgboost.log_model(clf, name="model")

        print("Model trained successfully.")
        print(overall_summary)
        if sector_summaries:
            print("Per-sector test metrics:")
            for line in sector_summaries:
                print(line)
        
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
            (pl.col(natr_col) * take_profit_natr > take_profit_pct / 100.0)
            .fill_null(False)
            .alias("natr_tp_ok")
        ).to_series().to_numpy()

        mlflow.log_param("entry_tp_prob", ENTRY_TP_PROB)
        mlflow.log_param("exit_tp_prob", EXIT_TP_PROB)

        entries = pl.Series("entries", (tp_probs > ENTRY_TP_PROB) & take_profit_above_threshold)
        exits = pl.Series("exits", (tp_probs < EXIT_TP_PROB) | stop_loss_exit)
        
        # Run vectorBT backtest
        bt_metrics = run_vectorbt_backtest(df_test, entries, exits, backtest_context={
            "stop_loss_pct": training_context["stop_loss_pct"],
            "metric_prefix": "backtest_",
        })
        mlflow.log_metrics(bt_metrics)
        
        print("Model backtest results logged to MLflow.")
        for k, v in bt_metrics.items():
            print(f"  {k}: {v:.4f}")

        if sector_metrics and "sector" in df_test.columns:
            for sector in df_test["sector"].unique():
                if sector is None:
                    continue
                sector_key = _sector_metric_key(str(sector))
                if sector_key in sector_metrics:
                    mask = df_test["sector"] == sector
                    sector_df_test = df_test.filter(mask)
                    sector_entries = entries.filter(mask)
                    sector_exits = exits.filter(mask)
                    
                    if len(sector_df_test) > 0:
                        sec_bt_metrics = run_vectorbt_backtest(
                            sector_df_test, sector_entries, sector_exits, backtest_context={
                                "stop_loss_pct": training_context["stop_loss_pct"],
                                "metric_prefix": "backtest_",
                            }
                        )
                        sector_metrics[sector_key].update(sec_bt_metrics)
                        
        if sector_metrics:
            mlflow.log_dict(sector_metrics, "sector_test_metrics.json")

    return clf, acc
