"""Stage D — absolute EV admit + book caps (K5).

Top-K after admit is capacity-only, not an economic gate.

M6 authority is **blocked** while the directional cash product is a §14 FAIL.
These helpers stay so an M9 registry can reuse them without remounting M5 Stage C.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from src.utils.eval_common import N_BOOT, session_block_mean_ci


@dataclass(frozen=True)
class BookCaps:
    """Risk caps for the sparse admitted book."""

    max_concurrent: int = 4
    max_per_sector: int = 2
    daily_loss_limit: float = -0.01  # −100 bps of notionals sketch
    kelly_fraction: float = 0.25
    capacity_top_k: int | None = None  # optional post-admit capacity sort


@dataclass(frozen=True)
class ConformalBound:
    point: float
    lower: float
    upper: float
    n: int
    n_sessions: int
    residual_q: float | None = None


def conformal_residual_quantile(
    ev_hat: np.ndarray,
    ev_realized: np.ndarray,
    *,
    alpha: float = 0.05,
) -> float:
    """Lower residual quantile of (realized − hat) on a purged val slice."""
    mask = np.isfinite(ev_hat) & np.isfinite(ev_realized)
    resid = np.asarray(ev_realized, dtype=float)[mask] - np.asarray(ev_hat, dtype=float)[mask]
    if resid.size < 30:
        raise ValueError(f"conformal residual slice too thin n={resid.size}")
    return float(np.quantile(resid, alpha))


def attach_conformal_lower_bound(
    panel: pl.DataFrame,
    residual_q: float,
    *,
    ev_hat_col: str = "ev_net_hat",
    lb_col: str = "ev_net_lb",
) -> pl.DataFrame:
    """Per-row conformal LB = ev_hat + q_lo(val residual). Admit on ``lb_col > 0``."""
    return panel.with_columns(**{lb_col: pl.col(ev_hat_col) + residual_q})


def conformal_ev_lower_bound(
    ev_hat: np.ndarray,
    ev_realized: np.ndarray,
    session_ids: np.ndarray,
    *,
    n_boot: int = N_BOOT,
    seed: int = 0,
    alpha: float = 0.05,
) -> ConformalBound:
    """
    Pool diagnostic: mean(hat) + session-block CI of residuals, plus the
    per-row conformal quantile used for admit.

    ``LB_pool = mean(ev_hat) + CI_lo(realized − hat)``. Per-instance admit
    uses ``attach_conformal_lower_bound`` with ``residual_q``.
    """
    mask = np.isfinite(ev_realized) & np.isfinite(ev_hat)
    hat = np.asarray(ev_hat, dtype=float)[mask]
    realized = np.asarray(ev_realized, dtype=float)[mask]
    sess = np.asarray(session_ids)[mask]
    residual = realized - hat
    rng = np.random.default_rng(seed)
    _mean_res, lo_res, hi_res = session_block_mean_ci(residual, sess, n_boot, rng)
    mean_hat = float(hat.mean())
    q_lo = float(np.quantile(residual, alpha)) if residual.size else float("nan")
    return ConformalBound(
        point=mean_hat + float(residual.mean()),
        lower=mean_hat + lo_res,
        upper=mean_hat + hi_res,
        n=int(mask.sum()),
        n_sessions=int(np.unique(sess).size),
        residual_q=q_lo,
    )


def admit_on_ev(
    panel: pl.DataFrame,
    *,
    ev_hat_col: str = "ev_net_hat",
    lower_bound_col: str | None = None,
) -> pl.DataFrame:
    """Absolute admit: conformal LB > 0 (or hat > 0 if LB column absent)."""
    if lower_bound_col is not None:
        ok = pl.col(lower_bound_col) > 0.0
    else:
        ok = pl.col(ev_hat_col) > 0.0
    return panel.with_columns(admit_ok=ok)


def apply_capacity_top_k(
    admitted: pl.DataFrame,
    *,
    k: int,
    score_col: str = "ev_net_hat",
    bar_col: str = "date",
) -> pl.DataFrame:
    """Post-admit capacity sort — not an economic gate."""
    return (
        admitted.filter(pl.col("admit_ok"))
        .with_columns(
            capacity_rank=pl.col(score_col)
            .rank(method="ordinal", descending=True)
            .over(bar_col)
        )
        .filter(pl.col("capacity_rank") <= k)
    )


def fractional_kelly_size(
    ev: float,
    variance: float,
    *,
    caps: BookCaps = BookCaps(),
) -> float:
    """Simple f* = edge/var clipped by kelly_fraction."""
    if variance <= 0:
        return 0.0
    raw = ev / variance
    return float(max(0.0, min(raw * caps.kelly_fraction, caps.kelly_fraction)))


def enforce_concurrency_cap(
    fires: pl.DataFrame,
    *,
    caps: BookCaps = BookCaps(),
    score_col: str = "ev_net_hat",
    bar_col: str = "date",
) -> pl.DataFrame:
    """Keep top ``max_concurrent`` by score within each decision bar."""
    return (
        fires.with_columns(
            _rk=pl.col(score_col).rank(method="ordinal", descending=True).over(bar_col)
        )
        .filter(pl.col("_rk") <= caps.max_concurrent)
        .drop("_rk")
    )


def enforce_sector_cap(
    fires: pl.DataFrame,
    *,
    caps: BookCaps = BookCaps(),
    score_col: str = "ev_net_hat",
    bar_col: str = "date",
    sector_col: str = "sector",
) -> pl.DataFrame:
    """Keep top ``max_per_sector`` by score within each (bar, sector)."""
    if sector_col not in fires.columns:
        raise ValueError(f"sector cap requires {sector_col!r} column")
    return (
        fires.with_columns(
            _rk=pl.col(score_col)
            .rank(method="ordinal", descending=True)
            .over([bar_col, sector_col])
        )
        .filter(pl.col("_rk") <= caps.max_per_sector)
        .drop("_rk")
    )


def enforce_daily_loss_limit(
    fires: pl.DataFrame,
    *,
    caps: BookCaps = BookCaps(),
    ev_col: str = "ev_net_hat",
    session_col: str = "date_only",
    score_col: str = "ev_net_hat",
) -> pl.DataFrame:
    """
    Within each session, fill highest-score fires until cumulative EV would
    breach ``daily_loss_limit``. Later (worse-score) fires are dropped.
    """
    if session_col not in fires.columns:
        raise ValueError(f"daily loss cap requires {session_col!r} column")
    ranked = fires.sort([session_col, score_col], descending=[False, True])
    return (
        ranked.with_columns(_cum=pl.col(ev_col).cum_sum().over(session_col))
        .filter(pl.col("_cum") >= caps.daily_loss_limit)
        .drop("_cum")
    )
