"""Stage B — opportunity / remaining-range gate (K1, K2).

Separate trainer from production ``GBMHorizonModel``. Feature hygiene reuses
``src.features.core`` primitives; Regime columns are consumed, not re-fit.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import polars as pl

from src.features.core import range_pct
from src.horizon.fresh.friction import OPPORTUNITY_MIN_RANGE
from src.horizon.session import MIS_EXIT_BAR_END
from src.utils.eval_common import BAR_MINUTES

# Minimal HAR-style feature set for M3 scaffolding (earnings flag = TODO).
# ``volume_z`` is for equities with real volume. Index-only harnesses
# (e.g. V1-index on ^NSEI) must omit it — cash-index volume ≡ 0.
OPPORTUNITY_FEATURES: tuple[str, ...] = (
    "open_30m_range",
    "gap_bps",
    "rv_5d",
    "volume_z",
    "tod_range_med",
    "bars_to_mis",
)


@dataclass
class OpportunityModel:
    """Quantile GBDT on log remaining-session range."""

    quantiles: tuple[float, ...] = (0.25, 0.50, 0.75)
    models: dict[float, lgb.LGBMRegressor] | None = None

    def fit(self, x: np.ndarray, y_range: np.ndarray) -> OpportunityModel:
        mask = np.isfinite(x).all(axis=1) & np.isfinite(y_range) & (y_range > 0)
        x = x[mask]
        y = np.log(np.clip(y_range[mask], 1e-6, None))
        self.models = {}
        for q in self.quantiles:
            m = lgb.LGBMRegressor(
                objective="quantile",
                alpha=q,
                n_estimators=200,
                learning_rate=0.05,
                num_leaves=31,
                min_child_samples=50,
                verbosity=-1,
            )
            m.fit(x, y)
            self.models[q] = m
        return self

    def predict_quantiles(self, x: np.ndarray) -> dict[str, np.ndarray]:
        if self.models is None:
            raise RuntimeError("OpportunityModel.fit required before predict")
        out: dict[str, np.ndarray] = {}
        for q, m in self.models.items():
            out[f"range_q{int(q * 100):02d}"] = np.exp(m.predict(x))
        return out


def remaining_session_range(
    bars: pl.DataFrame,
    *,
    mis_exit: object = MIS_EXIT_BAR_END,
) -> pl.DataFrame:
    """
    Realized remaining range from each bar to MIS flatten (same session).

    ``remaining_range = (max_high_to_mis - min_low_to_mis) / close``.
    """
    df = bars.sort(["symbol", "date"]).with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
    )
    # Reverse cum max/min within session for "remaining" extrema.
    df = df.with_columns(
        _rev_hi=pl.col("high").reverse().cum_max().reverse().over(
            ["symbol", "date_only"]
        ),
        _rev_lo=pl.col("low").reverse().cum_min().reverse().over(
            ["symbol", "date_only"]
        ),
    )
    # dt.hour()/dt.minute() are Int8 — cast before ×60 or the product wraps.
    minute_of_day = pl.col("date").dt.hour().cast(pl.Int32) * 60 + pl.col(
        "date"
    ).dt.minute().cast(pl.Int32)
    return df.with_columns(
        remaining_range=(pl.col("_rev_hi") - pl.col("_rev_lo")) / pl.col("close"),
        bars_to_mis=(
            (pl.lit(mis_exit.hour * 60 + mis_exit.minute, dtype=pl.Int32) - minute_of_day)
            / BAR_MINUTES
        ).cast(pl.Int32),
    ).drop(["_rev_hi", "_rev_lo"])


def attach_opportunity_features(bars: pl.DataFrame) -> pl.DataFrame:
    """Causal opportunity features (no look-ahead). Earnings/event flag = TODO."""
    df = bars.sort(["symbol", "date"]).with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
        _rng=range_pct(),
    )
    # Opening 30m: bars with time_only <= 09:45 (bar-end of 09:30–09:45).
    open_cut = dt.time(9, 45)
    daily_open = (
        df.filter(pl.col("time_only") <= open_cut)
        .group_by(["symbol", "date_only"])
        .agg(
            open_30m_range=(pl.col("high").max() - pl.col("low").min())
            / pl.col("close").last(),
            session_open=pl.col("open").first(),
        )
    )
    prev_close = (
        df.group_by(["symbol", "date_only"])
        .agg(prev_close=pl.col("close").last())
        .sort(["symbol", "date_only"])
        .with_columns(
            prev_close=pl.col("prev_close").shift(1).over("symbol"),
        )
    )
    df = (
        df.join(daily_open, on=["symbol", "date_only"], how="left")
        .join(prev_close, on=["symbol", "date_only"], how="left")
        .with_columns(
            gap_bps=(
                (pl.col("session_open") - pl.col("prev_close"))
                / pl.col("prev_close")
                * 1e4
            ),
            rv_5d=pl.col("_rng")
            .shift(1)
            .rolling_mean(window_size=5 * 25, min_samples=20)
            .over("symbol"),
            # Indices often have no volume (all zeros) → z-score is 0/0 NaN.
            # Neutralize; names with real volume keep a proper z.
            volume_z=(
                (
                    pl.col("volume")
                    - pl.col("volume").shift(1).rolling_mean(20).over("symbol")
                )
                / pl.col("volume").shift(1).rolling_std(20).over("symbol")
            )
            .fill_nan(0.0)
            .fill_null(0.0),
            tod_range_med=pl.col("_rng")
            .shift(1)
            .rolling_median(window_size=60, min_samples=10)
            .over(["symbol", "time_only"]),
        )
    )
    return df


def opportunity_ok_expr(
    q25_col: str = "range_q25",
    min_range: float = OPPORTUNITY_MIN_RANGE,
) -> pl.Expr:
    return pl.col(q25_col) >= min_range


def attach_opportunity_ok(
    panel: pl.DataFrame,
    *,
    q25_col: str = "range_q25",
    min_range: float = OPPORTUNITY_MIN_RANGE,
) -> pl.DataFrame:
    return panel.with_columns(
        opportunity_ok=opportunity_ok_expr(q25_col, min_range),
    )
