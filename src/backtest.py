from __future__ import annotations

from typing import Dict

import numpy as np
import polars as pl
import vectorbt as vbt


def run_vectorbt_backtest(
    df_test: pl.DataFrame,
    entries: pl.Series,
    exits: pl.Series,
    *,
    backtest_context: Dict = {
        "stop_loss_pct": 0.25,
        "freq": "1min",
        "fees": 0.0004,
        "metric_prefix": "backtest_",
    },
) -> Dict[str, float]:
    """
    Run a simple vectorBT long-only simulation: enter when the model predicts
    the take-profit class with high probability; exits when probability decays
    or SL is hit.

    Returns metrics suitable for MLflow / console (NaN and Inf stripped).
    """

    required = {"date", "symbol", "close"}
    if not required.issubset(set(df_test.columns)):
        return {}

    if len(entries) != len(df_test) or len(exits) != len(df_test):
        return {}

    test_pd = df_test.select(["date", "symbol", "close"]).to_pandas()
    test_pd["entries"] = entries.to_numpy()
    test_pd["exits"] = exits.to_numpy()

    close_df = test_pd.pivot(index="date", columns="symbol", values="close")
    entries_df = test_pd.pivot(index="date", columns="symbol", values="entries")
    exits_df = test_pd.pivot(index="date", columns="symbol", values="exits")

    sl_stop = (backtest_context.get("stop_loss_pct", 0.25) / 100.0)

    pf = vbt.Portfolio.from_signals(
        close=close_df,
        entries=entries_df,
        exits=exits_df,
        sl_stop=sl_stop,
        freq=backtest_context["freq"],
        fees=backtest_context["fees"],
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
