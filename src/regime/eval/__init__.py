"""Tier 1 Regime eval harness — see docs/regime-tier1-eval-verdict.md."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.regime.eval.common import N_BOOT, MetricResult, format_report
from src.regime.eval.daily_eval import build_ew_basket_15m, evaluate_daily
from src.regime.eval.intraday_eval import evaluate_intraday
from src.regime.intraday_model import IntradayHMMRegimeModel

__all__ = [
    "N_BOOT",
    "MetricResult",
    "build_ew_basket_15m",
    "evaluate_regime",
    "format_report",
]


def evaluate_regime(
    daily_features: pl.DataFrame,
    daily_classified: pl.DataFrame,
    regime_preds: pl.DataFrame,
    market_15m: pl.DataFrame,
    hmm: IntradayHMMRegimeModel,
    basket_15m: pl.DataFrame,
    n_boot: int,
    seed: int,
) -> list[MetricResult]:
    """Run Daily then Intraday evals; return flat metric list for reporting."""
    rng = np.random.default_rng(seed)
    metrics = evaluate_daily(
        daily_features,
        daily_classified,
        market_15m,
        basket_15m,
        n_boot,
        rng,
    )
    metrics.extend(
        evaluate_intraday(regime_preds, market_15m, hmm, n_boot, rng)
    )
    return metrics
