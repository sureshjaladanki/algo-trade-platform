"""Selection-ceiling and label diagnostics (M1 — report-only, no model ship)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from src.horizon.fresh.friction import BPS, C_STAR
from src.utils.eval_common import N_BOOT, session_block_mean_ci


@dataclass(frozen=True)
class CeilingReport:
    pool: str
    fold: str
    n_pool: int
    n_sessions: int
    mean_ev_net: float
    ci_lo: float
    ci_hi: float
    pos_mass: float
    top_decile_mean: float
    top_decile_n: int
    p_tp: float
    p_sl: float
    p_to: float


def _outcome_mix(labels: pl.Series) -> tuple[float, float, float]:
    arr = labels.drop_nulls().to_numpy()
    if arr.size == 0:
        return float("nan"), float("nan"), float("nan")
    return (
        float((arr == 1).mean()),
        float((arr == -1).mean()),
        float((arr == 0).mean()),
    )


def selection_ceiling(
    pool: pl.DataFrame,
    *,
    fold: str,
    pool_name: str,
    ev_col: str = "ev_net_abs",
    label_col: str = "tb_label",
    session_col: str = "date_only",
    n_boot: int = N_BOOT,
    seed: int = 0,
) -> CeilingReport:
    """
    Oracle top-decile ``EV_net`` on a defined pool (report-only).

    Rank by realized absolute ``ev_net``; publish top-decile mean, pos-mass, TP/SL/TO.
    """
    eligible = pool.filter(pl.col(ev_col).is_finite() & pl.col(ev_col).is_not_null())
    n = eligible.height
    if n == 0:
        return CeilingReport(
            pool=pool_name,
            fold=fold,
            n_pool=0,
            n_sessions=0,
            mean_ev_net=float("nan"),
            ci_lo=float("nan"),
            ci_hi=float("nan"),
            pos_mass=float("nan"),
            top_decile_mean=float("nan"),
            top_decile_n=0,
            p_tp=float("nan"),
            p_sl=float("nan"),
            p_to=float("nan"),
        )

    values = eligible[ev_col].to_numpy().astype(float)
    sess_series = eligible[session_col]
    if sess_series.dtype == pl.Date:
        sessions = sess_series.cast(pl.Int32).to_numpy().astype(np.int64)
    else:
        sessions = (
            sess_series.cast(pl.Datetime)
            .dt.timestamp("ms")
            .to_numpy()
            .astype(np.int64)
        )

    rng = np.random.default_rng(seed)
    mean, lo, hi = session_block_mean_ci(values, sessions, n_boot, rng)
    pos_mass = float((values > 0).mean())

    ranked = eligible.with_columns(
        _rk=pl.col(ev_col).rank(method="average", descending=True)
    )
    cut = max(1, n // 10)
    top = ranked.filter(pl.col("_rk") <= cut)
    top_mean = float(top[ev_col].mean())
    p_tp, p_sl, p_to = _outcome_mix(eligible[label_col])

    return CeilingReport(
        pool=pool_name,
        fold=fold,
        n_pool=n,
        n_sessions=int(eligible[session_col].n_unique()),
        mean_ev_net=mean,
        ci_lo=lo,
        ci_hi=hi,
        pos_mass=pos_mass,
        top_decile_mean=top_mean,
        top_decile_n=top.height,
        p_tp=p_tp,
        p_sl=p_sl,
        p_to=p_to,
    )


def format_ceiling_report(r: CeilingReport) -> str:
    return (
        f"ceiling pool={r.pool} fold={r.fold} n={r.n_pool} sess={r.n_sessions} "
        f"mean={r.mean_ev_net * BPS:.1f}bps "
        f"CI[{r.ci_lo * BPS:.1f},{r.ci_hi * BPS:.1f}] "
        f"pos={r.pos_mass:.1%} top10%={r.top_decile_mean * BPS:.1f}bps "
        f"(n={r.top_decile_n}) TP/SL/TO="
        f"{r.p_tp:.1%}/{r.p_sl:.1%}/{r.p_to:.1%} c*={C_STAR:.4f}"
    )


def production_long_eligible_mask() -> list[pl.Expr]:
    """Boolean filters for production-shaped Long eligible pool (fresh labels)."""
    return [
        pl.col("tb_eligible"),
        pl.col("entry_ok"),
        pl.col("ev_net_abs").is_finite(),
        pl.col("tb_label").is_not_null(),
    ]
