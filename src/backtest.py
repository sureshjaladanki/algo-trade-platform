from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import numpy as np
import polars as pl
import pandas as pd
import vectorbt as vbt

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

    sl_stop = (backtest_context.get("stop_loss_pct", 0.25) / 100.0)

    pf = vbt.Portfolio.from_signals(
        close=close_df,
        entries=entries_df,
        exits=exits_df,
        sl_stop=sl_stop,
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
    Run a vectorBT long-only simulation sweeping across multiple entry and exit thresholds.
    """
    import itertools
    import pandas as pd

    backtest_context = backtest_context or {}
    backtest_context = {**_DEFAULT_BACKTEST_CONTEXT, **backtest_context}

    required = {"date", "symbol", "close"}
    if not required.issubset(set(df_test.columns)):
        return pd.DataFrame()

    if len(tp_probs) != len(df_test):
        return pd.DataFrame()

    test_pd = df_test.select(["date", "symbol", "close"]).to_pandas()
    test_pd["tp_probs"] = tp_probs

    # Drop duplicates in case multiple rows have the same date and symbol
    test_pd = test_pd.drop_duplicates(subset=["date", "symbol"], keep="last")

    close_df = test_pd.pivot(index="date", columns="symbol", values="close")
    probs_df = test_pd.pivot(index="date", columns="symbol", values="tp_probs").astype(np.float64).fillna(0.0)

    combinations = list(itertools.product(entry_thresholds, exit_thresholds))
    
    entries_list = []
    exits_list = []
    for en, ex in combinations:
        entries_list.append((probs_df > en).astype(bool))
        exits_list.append((probs_df < ex).astype(bool))
        
    multi_index = pd.MultiIndex.from_tuples(combinations, names=['entry_threshold', 'exit_threshold'])
    
    entries_df = pd.concat(entries_list, axis=1, keys=multi_index)
    exits_df = pd.concat(exits_list, axis=1, keys=multi_index)
    close_df_sweep = pd.concat([close_df] * len(combinations), axis=1, keys=multi_index)

    sl_stop = (backtest_context.get("stop_loss_pct", 0.25) / 100.0)

    pf = vbt.Portfolio.from_signals(
        close=close_df_sweep,
        entries=entries_df,
        exits=exits_df,
        sl_stop=sl_stop,
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
    # we need to group by the thresholds and take the mean across symbols
    sweep_results = metrics.groupby(['entry_threshold', 'exit_threshold']).mean().reset_index()
    
    return sweep_results
