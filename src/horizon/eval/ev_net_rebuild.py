"""AUDIT-ONLY (fresh M0 quarantine) — EV-net rebuild Step 0 (STOP ledger).

Baseline reprint for M0 is allowed. See docs/archive/horizon-fresh-quarantine-index.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from src.horizon.eval.constants import (
    MIN_BARS_LONG,
    MIN_SESSIONS,
    N_BOOT,
    MetricResult,
    _TRADEABLE_DAILY,
)
from src.labels.ev_net_geometry import (
    GEOMETRY_CANDIDATES,
    HARD_STOP_EV_NET_UB,
    HARD_STOP_EV_NET_UB_BPS,
    LongGeometry,
    calculate_long_geometry_labels,
)
from src.labels.triple_barrier import BPS, ROUND_TRIP_COST
from src.regime.types import IntradayRegime
from src.utils.eval_common import session_block_mean_ci

# E0 CI scheme frozen at Step 0b (charter NICE) — session-block bootstrap.
E0_CI_METHOD = "session_block_bootstrap"
E0_CI_BLOCK = "trading_session"  # date_only
E0_N_BOOT = N_BOOT


@dataclass(frozen=True)
class GeometryFoldStat:
    geometry: str
    fold: str
    n_eligible: int
    n_sessions: int
    n_pos: int  # eligible bars with realized EV_net > 0 (oracle admit proxy)
    n_pos_sessions: int
    p_tp: float
    p_sl: float
    p_to: float
    mean_mfe_bps: float
    mean_to_ret_bps: float
    mean_ev_net: float
    ci_lo: float
    ci_hi: float
    feasible_fold: bool  # CI UB > hard-stop cut


def _long_hard_eligible(labeled: pl.DataFrame, regime_df: pl.DataFrame) -> pl.DataFrame:
    """Hygiene → hard eligibility (session + regime soft overlay + TB eligible)."""
    joined = labeled.join(
        regime_df.select(["date", "daily_regime", "intraday_regime"]),
        on="date",
        how="inner",
    )
    return joined.filter(
        pl.col("tb_eligible")
        & pl.col("entry_ok")
        & pl.col("ev_net").is_finite()
        & pl.col("tb_label").is_not_null()
        & pl.col("daily_regime").is_in(list(_TRADEABLE_DAILY))
        & (pl.col("intraday_regime") == IntradayRegime.TREND_UP.value)
    )


def summarize_geometry_fold(
    stock_df: pl.DataFrame,
    regime_df: pl.DataFrame,
    geometry: LongGeometry,
    fold: str,
    n_boot: int,
    rng: np.random.Generator,
) -> tuple[GeometryFoldStat, list[MetricResult]]:
    """Unconditional-eligible EV_net + travel/timeout mix for one geometry × fold."""
    labeled = calculate_long_geometry_labels(stock_df, geometry)
    eligible = _long_hard_eligible(labeled, regime_df)
    side = f"{geometry.name}|{fold}"

    if eligible.height == 0:
        stat = GeometryFoldStat(
            geometry=geometry.name,
            fold=fold,
            n_eligible=0,
            n_sessions=0,
            n_pos=0,
            n_pos_sessions=0,
            p_tp=float("nan"),
            p_sl=float("nan"),
            p_to=float("nan"),
            mean_mfe_bps=float("nan"),
            mean_to_ret_bps=float("nan"),
            mean_ev_net=float("nan"),
            ci_lo=float("nan"),
            ci_hi=float("nan"),
            feasible_fold=False,
        )
        metrics = [
            MetricResult(
                "EVnet",
                side,
                None,
                None,
                None,
                0,
                False,
                "empty eligible",
            )
        ]
        return stat, metrics

    values = eligible["ev_net"].to_numpy()
    sessions = eligible["date_only"].to_list()
    uniq = {s: i for i, s in enumerate(sorted(set(sessions)))}
    session_ids = np.array([uniq[s] for s in sessions], dtype=np.int64)

    point, ci_lo, ci_hi = session_block_mean_ci(values, session_ids, n_boot, rng)
    n_sess = int(len(uniq))
    pos_mask = values > 0
    n_pos = int(pos_mask.sum())
    n_pos_sess = int(len({sessions[i] for i in range(len(sessions)) if pos_mask[i]}))
    labels = eligible["tb_label"].to_numpy()
    p_tp = float((labels == 1).mean())
    p_sl = float((labels == -1).mean())
    p_to = float((labels == 0).mean())
    mean_mfe = float(eligible["mfe_bps"].mean())
    to_rows = eligible.filter(pl.col("tb_label") == 0)
    mean_to = (
        float(to_rows["path_ret"].mean() * BPS) if to_rows.height else float("nan")
    )
    feasible = bool(np.isfinite(ci_hi) and ci_hi > HARD_STOP_EV_NET_UB)

    stat = GeometryFoldStat(
        geometry=geometry.name,
        fold=fold,
        n_eligible=eligible.height,
        n_sessions=n_sess,
        n_pos=n_pos,
        n_pos_sessions=n_pos_sess,
        p_tp=p_tp,
        p_sl=p_sl,
        p_to=p_to,
        mean_mfe_bps=mean_mfe,
        mean_to_ret_bps=mean_to,
        mean_ev_net=point,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        feasible_fold=feasible,
    )
    metrics = [
        MetricResult(
            "EVnet",
            side,
            point,
            ci_lo,
            ci_hi,
            eligible.height,
            feasible,
            (
                f"UB_cut={HARD_STOP_EV_NET_UB_BPS:.0f}bps "
                f"TP/SL/TO={p_tp:.3f}/{p_sl:.3f}/{p_to:.3f} "
                f"mfe={mean_mfe:.1f}bps sess={n_sess}"
            ),
        ),
        MetricResult(
            "travel",
            side,
            mean_mfe / BPS if np.isfinite(mean_mfe) else None,
            None,
            None,
            eligible.height,
            None,
            f"mean_mfe_bps={mean_mfe:.1f}",
        ),
        MetricResult(
            "timeout",
            side,
            p_to,
            None,
            None,
            eligible.height,
            None,
            f"mean_to_ret_bps={mean_to:.1f}",
        ),
        MetricResult(
            "pos_mass",
            side,
            float(pos_mask.mean()),
            None,
            None,
            n_pos,
            None,
            f"oracle EV_net>0 bars; pos_sess={n_pos_sess}",
        ),
    ]
    return stat, metrics


def evaluate_step0_geometries(
    stock_df: pl.DataFrame,
    regime_df: pl.DataFrame,
    fold: str,
    *,
    geometries: tuple[LongGeometry, ...] = GEOMETRY_CANDIDATES,
    n_boot: int = E0_N_BOOT,
    seed: int = 42,
) -> tuple[list[GeometryFoldStat], list[MetricResult]]:
    """Run all pre-registered geometries on one holdout fold."""
    rng = np.random.default_rng(seed)
    stats: list[GeometryFoldStat] = []
    metrics: list[MetricResult] = []
    for geo in geometries:
        print(
            f"   Geometry {geo.name}: H={geo.horizon_bars} "
            f"TP={geo.tp_floor * BPS:.0f}bps SL={geo.sl_floor * BPS:.0f}bps "
            f"mult={geo.tp_vol_mult}/{geo.sl_vol_mult}"
        )
        stat, m = summarize_geometry_fold(
            stock_df, regime_df, geo, fold, n_boot, rng
        )
        stats.append(stat)
        metrics.extend(m)
    return stats, metrics


def candidate_dual_fold_feasible(stats: list[GeometryFoldStat], geometry: str) -> bool:
    """Infeasible iff both folds have CI UB ≤ hard-stop cut (dual-fold)."""
    folds = [s for s in stats if s.geometry == geometry]
    if len(folds) < 2:
        return False
    return all(s.feasible_fold for s in folds)


def hard_stop_fires(stats: list[GeometryFoldStat]) -> bool:
    """STOP @ 0/3 when every pre-registered candidate is dual-fold infeasible."""
    names = {s.geometry for s in stats}
    return bool(names) and all(
        not candidate_dual_fold_feasible(stats, name) for name in names
    )


def select_freeze_geometry(
    stats: list[GeometryFoldStat],
    geometries: tuple[LongGeometry, ...] = GEOMETRY_CANDIDATES,
) -> LongGeometry | None:
    """
    Freeze rule (pre-registered): among dual-fold feasible candidates, pick
    highest min(point_A, point_B); ties → lower H, then higher TP/SL floor gap.
    """
    by_name = {g.name: g for g in geometries}
    scored: list[tuple[float, int, float, LongGeometry]] = []
    for name, geo in by_name.items():
        if not candidate_dual_fold_feasible(stats, name):
            continue
        pts = [s.mean_ev_net for s in stats if s.geometry == name]
        if len(pts) < 2 or not all(np.isfinite(pts)):
            continue
        scored.append(
            (
                float(min(pts)),
                -geo.horizon_bars,  # prefer lower H on tie (sort descending)
                geo.tp_floor - geo.sl_floor,
                geo,
            )
        )
    if not scored:
        return None
    scored.sort(reverse=True)
    return scored[0][3]


def e2_floors_for_geometry(
    stats: list[GeometryFoldStat],
    geometry: str,
) -> dict[str, int | float | str]:
    """
    Step 0b E2 formula (charter MUST_FIX #6).

    projected_adm_* = eligible bars/sessions with realized EV_net>0 (oracle proxy);
    dual-fold lock = min across A/B.
    """
    fold_stats = [s for s in stats if s.geometry == geometry]
    if not fold_stats:
        return {
            "min_bars": MIN_BARS_LONG,
            "min_sessions": MIN_SESSIONS,
            "projected_adm_bars": 0,
            "projected_adm_sess": 0,
            "cost": ROUND_TRIP_COST,
            "ci_method": E0_CI_METHOD,
            "ci_block": E0_CI_BLOCK,
            "n_boot": E0_N_BOOT,
        }
    dual_bars = int(min(s.n_pos for s in fold_stats))
    dual_sess = int(min(s.n_pos_sessions for s in fold_stats))
    return {
        "min_bars": max(MIN_BARS_LONG, dual_bars // 2),
        "min_sessions": max(MIN_SESSIONS, dual_sess // 2),
        "projected_adm_bars": dual_bars,
        "projected_adm_sess": dual_sess,
        "cost": ROUND_TRIP_COST,
        "ci_method": E0_CI_METHOD,
        "ci_block": E0_CI_BLOCK,
        "n_boot": E0_N_BOOT,
    }


__all__ = [
    "E0_CI_BLOCK",
    "E0_CI_METHOD",
    "E0_N_BOOT",
    "GeometryFoldStat",
    "candidate_dual_fold_feasible",
    "e2_floors_for_geometry",
    "evaluate_step0_geometries",
    "hard_stop_fires",
    "select_freeze_geometry",
    "summarize_geometry_fold",
]
