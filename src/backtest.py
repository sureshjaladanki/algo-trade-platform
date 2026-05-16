from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import numpy as np
import polars as pl
import pandas as pd
import vectorbt as vbt
import itertools

from .utils import load_config

_CONFIG_ROOT = Path(__file__).resolve().parents[1] / "config"
_DEFAULT_BACKTEST_PATH = _CONFIG_ROOT / "backtest.yml"
_DEFAULT_BACKTEST_CONTEXT = load_config(_DEFAULT_BACKTEST_PATH)

def run_vectorbt_backtest(
    df_test: pl.DataFrame,
    entries: pl.Series,
    exits: pl.Series,
    *,
    backtest_context: Dict[str, Any] = None
) -> Dict[str, float]:
    """
    Run a simple vectorBT long-only simulation: enter when the model predicts
    the take-profit class with high probability; exits when probability decays
    or SL is hit.

    Returns metrics suitable for MLflow / console (NaN and Inf stripped).
    """
    backtest_context = backtest_context or {}
    backtest_context = {**_DEFAULT_BACKTEST_CONTEXT, **backtest_context}

    required = {"date", "symbol", "close"}
    if not required.issubset(set(df_test.columns)):
        return {}

    if len(entries) != len(df_test) or len(exits) != len(df_test):
        return {}

    test_pd = df_test.select(["date", "symbol", "close"]).to_pandas()
    test_pd["entries"] = entries.to_numpy()
    test_pd["exits"] = exits.to_numpy()

    # Drop duplicates in case multiple rows have the same date and symbol
    test_pd = test_pd.drop_duplicates(subset=["date", "symbol"], keep="last")

    close_df = test_pd.pivot(index="date", columns="symbol", values="close")
    entries_df = (
        test_pd.pivot(index="date", columns="symbol", values="entries")
        .astype(np.float64)
        .fillna(0.0)
        .astype(bool)
    )
    exits_df = (
        test_pd.pivot(index="date", columns="symbol", values="exits")
        .astype(np.float64)
        .fillna(0.0)
        .astype(bool)
    )

    pf = vbt.Portfolio.from_signals(
        close=close_df,
        entries=entries_df,
        exits=exits_df,
        freq=backtest_context["freq"],
        fees=backtest_context["fees"],
        slippage=backtest_context["slippage"],
    )

    metric_prefix = backtest_context.get("metric_prefix", "backtest_")
    bt_metrics = {
        f"{metric_prefix}total_return": pf.total_return().mean(),
        f"{metric_prefix}win_rate": pf.trades.win_rate().mean(),
        f"{metric_prefix}max_drawdown": pf.max_drawdown().mean(),
        f"{metric_prefix}sharpe_ratio": pf.sharpe_ratio().mean(),
        f"{metric_prefix}total_trades": float(len(pf.trades)),
    }

    return {k: float(v) for k, v in bt_metrics.items() if not np.isnan(v) and not np.isinf(v)}

def run_vectorbt_backtest_sweep(
    df_test: pl.DataFrame,
    tp_probs: np.ndarray,
    entry_thresholds: list[float],
    exit_thresholds: list[float],
    *,
    backtest_context: Dict[str, Any] = None
) -> pd.DataFrame:
    """
    Run a vectorBT long-only simulation sweeping entry/exit probability thresholds.

    Entries and exits follow `train_xgboost_model` / `model.py`: enter only when
    NATR * take_profit_natr exceeds take_profit_pct; exit when probability is
    below the exit threshold or on the NATR-scaled single-bar stop signal.
    NATR settings come from `config/backtest.yml` (merged with optional `backtest_context`).
    """

    backtest_context = backtest_context or {}
    backtest_context = {**_DEFAULT_BACKTEST_CONTEXT, **backtest_context}
    natr_col = backtest_context["natr_col"]

    required = {"date", "symbol", "close", natr_col}
    if not required.issubset(set(df_test.columns)):
        return pd.DataFrame()

    if len(tp_probs) != len(df_test):
        return pd.DataFrame()

    """
    NATR-scaled single-bar stop mask and entry gate
    (natr * take_profit_natr > take_profit_pct). Defaults from `config/backtest.yml`;
    `overrides` can supply training-time values (e.g. `training_context` in `model.py`).
    """
    stop_loss_natr = float(backtest_context["stop_loss_natr"])
    take_profit_natr = float(backtest_context["take_profit_natr"])
    take_profit_pct = float(backtest_context["take_profit_pct"])

    stop_loss_exit = (
        df_test.select(
            (
                (pl.col("close") / pl.col("close").shift(1).over("symbol") - 1.0)
                <= -pl.col(natr_col) * stop_loss_natr
            )
            .fill_null(False)
            .alias("ret_exit")
        )
        .to_series()
        .to_numpy()
    )
    take_profit_above_threshold = (
        df_test.select(
            (pl.col(natr_col) * take_profit_natr > take_profit_pct / 100.0)
            .fill_null(False)
            .alias("natr_tp_ok")
        )
        .to_series()
        .to_numpy()
    )

    test_pd = df_test.select(["date", "symbol", "close"]).to_pandas()
    test_pd["tp_probs"] = tp_probs
    test_pd["stop_loss_exit"] = stop_loss_exit
    test_pd["take_profit_above_threshold"] = take_profit_above_threshold

    # Drop duplicates in case multiple rows have the same date and symbol
    test_pd = test_pd.drop_duplicates(subset=["date", "symbol"], keep="last")

    close_df = test_pd.pivot(index="date", columns="symbol", values="close")
    probs_df = test_pd.pivot(index="date", columns="symbol", values="tp_probs").astype(
        np.float64
    )
    sl_exit_df = (
        test_pd.pivot(index="date", columns="symbol", values="stop_loss_exit")
        .astype(np.float64)
        .fillna(0.0)
        .astype(bool)
    )
    tp_ok_df = (
        test_pd.pivot(index="date", columns="symbol", values="take_profit_above_threshold")
        .astype(np.float64)
        .fillna(0.0)
        .astype(bool)
    )

    combinations = list(itertools.product(entry_thresholds, exit_thresholds))

    entries_list = []
    exits_list = []
    for en, ex in combinations:
        entries_list.append(((probs_df > en) & tp_ok_df).astype(bool))
        exits_list.append(((probs_df < ex) | sl_exit_df).astype(bool))
        
    multi_index = pd.MultiIndex.from_tuples(combinations, names=['entry_threshold', 'exit_threshold'])
    
    entries_df = pd.concat(entries_list, axis=1, keys=multi_index)
    exits_df = pd.concat(exits_list, axis=1, keys=multi_index)
    close_df_sweep = pd.concat([close_df] * len(combinations), axis=1, keys=multi_index)

    pf = vbt.Portfolio.from_signals(
        close=close_df_sweep,
        entries=entries_df,
        exits=exits_df,
        freq=backtest_context["freq"],
        fees=backtest_context["fees"],
        slippage=backtest_context["slippage"],
    )

    metric_prefix = backtest_context.get("metric_prefix", "backtest_")
    
    # Calculate metrics for each parameter combination
    metrics = pd.DataFrame({
        f"{metric_prefix}total_return": pf.total_return(),
        f"{metric_prefix}win_rate": pf.trades.win_rate(),
        f"{metric_prefix}max_drawdown": pf.max_drawdown(),
        f"{metric_prefix}sharpe_ratio": pf.sharpe_ratio(),
        f"{metric_prefix}total_trades": pf.trades.count(),
    })
    
    # Since metrics are calculated per symbol due to our MultiIndex (entry, exit, symbol),
    # we need to group by the thresholds and take the mean across symbols (sum for total_trades)
    sweep_results = metrics.groupby(['entry_threshold', 'exit_threshold']).agg({
        f"{metric_prefix}total_return": "mean",
        f"{metric_prefix}win_rate": "mean",
        f"{metric_prefix}max_drawdown": "mean",
        f"{metric_prefix}sharpe_ratio": "mean",
        f"{metric_prefix}total_trades": "sum",
    }).reset_index()
    
    return sweep_results
