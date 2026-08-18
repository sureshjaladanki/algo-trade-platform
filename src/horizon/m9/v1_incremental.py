"""M9 V1 helpers — incremental information of range_q50 over implied range."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class IncrementalResult:
    """OLS: realized ~ a + b1·implied [+ controls] + bq·range_q50."""

    n: int
    coef_implied: float
    coef_q50: float
    se_q50: float
    t_q50: float
    p_q50: float
    r2: float
    passed: bool
    note: str = ""
    coef_controls: tuple[float, ...] = ()


def incremental_range_ols(
    realized: np.ndarray,
    implied: np.ndarray,
    range_q50: np.ndarray,
    *,
    extra_controls: np.ndarray | None = None,
    require_positive: bool = True,
    alpha: float = 0.05,
) -> IncrementalResult:
    """
    Test whether ``range_q50`` has incremental explanatory power for realized
    remaining range after controlling for implied range (and optional extras).

    Design matrix is ``[1, implied, extra…, q50]``. PASS if coef_q50 > 0 and
    two-sided p < alpha. Extra columns are *controls*, not the tested coefficient.
    """
    x_imp = np.asarray(implied, dtype=float)
    x_q = np.asarray(range_q50, dtype=float)
    y = np.asarray(realized, dtype=float)
    m = np.isfinite(x_imp) & np.isfinite(x_q) & np.isfinite(y)
    if require_positive:
        m &= (y > 0) & (x_imp > 0)
    extras: np.ndarray | None = None
    if extra_controls is not None:
        extras = np.asarray(extra_controls, dtype=float)
        if extras.ndim == 1:
            extras = extras.reshape(-1, 1)
        m &= np.isfinite(extras).all(axis=1)
        if require_positive:
            m &= (extras > 0).all(axis=1)
    n = int(m.sum())
    n_ctrl = 0 if extras is None else int(extras.shape[1])
    n_params = 2 + n_ctrl + 1  # intercept + implied + extras + q50
    if n < max(100, n_params * 20):
        return IncrementalResult(
            n=n,
            coef_implied=float("nan"),
            coef_q50=float("nan"),
            se_q50=float("nan"),
            t_q50=float("nan"),
            p_q50=float("nan"),
            r2=float("nan"),
            passed=False,
            note="thin",
        )
    cols = [np.ones(n), x_imp[m]]
    if extras is not None:
        cols.append(extras[m])
    cols.append(x_q[m])
    x = np.column_stack(cols)
    y_m = y[m]
    beta, _, _, _ = np.linalg.lstsq(x, y_m, rcond=None)
    resid = y_m - x @ beta
    dof = max(n - n_params, 1)
    sigma2 = float(resid @ resid) / dof
    q_idx = x.shape[1] - 1
    try:
        xtx_inv = np.linalg.inv(x.T @ x)
    except np.linalg.LinAlgError:
        return IncrementalResult(
            n=n,
            coef_implied=float(beta[1]),
            coef_q50=float(beta[q_idx]),
            se_q50=float("nan"),
            t_q50=float("nan"),
            p_q50=float("nan"),
            r2=float("nan"),
            passed=False,
            note="singular",
            coef_controls=tuple(float(v) for v in beta[2:q_idx]),
        )
    se = np.sqrt(np.diag(xtx_inv) * sigma2)
    t_q = float(beta[q_idx] / se[q_idx]) if se[q_idx] > 0 else float("nan")
    p_q = float(2 * stats.t.sf(abs(t_q), dof)) if np.isfinite(t_q) else float("nan")
    ss_tot = float(((y_m - y_m.mean()) ** 2).sum())
    r2 = 1.0 - float(resid @ resid) / ss_tot if ss_tot > 0 else float("nan")
    passed = bool(beta[q_idx] > 0 and np.isfinite(p_q) and p_q < alpha)
    return IncrementalResult(
        n=n,
        coef_implied=float(beta[1]),
        coef_q50=float(beta[q_idx]),
        se_q50=float(se[q_idx]),
        t_q50=t_q,
        p_q50=p_q,
        r2=r2,
        passed=passed,
        note=f"alpha={alpha} n_ctrl={n_ctrl}",
        coef_controls=tuple(float(v) for v in beta[2:q_idx]),
    )


def demean_within_clock(values: np.ndarray, clock: np.ndarray) -> np.ndarray:
    """Subtract per-clock means so a nested OLS is not a TOD artefact."""
    y = np.asarray(values, dtype=float).copy()
    g = np.asarray(clock)
    for key in np.unique(g):
        mask = g == key
        mu = np.nanmean(y[mask])
        if np.isfinite(mu):
            y[mask] = y[mask] - mu
    return y
