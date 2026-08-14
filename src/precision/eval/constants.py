"""Tier 3 Precision eval — locked constants and sleeve helpers."""

from __future__ import annotations

import numpy as np

from src.horizon.eval.constants import K_LONG, K_SHORT, k_for, side_sign
from src.horizon.session import LONG_LAST_ENTRY, SHORT_LAST_ENTRY
from src.labels.triple_barrier import ARCHIVE_ROUND_TRIP_COST, ROUND_TRIP_COST
from src.utils.eval_common import (
    H_BARS,
    MIN_SESSIONS,
    N_BOOT,
    MetricResult,
    format_report,
    session_block_mean_ci,
)

# Locked K matches live Precision emit (LONG_TOP_K=5 / SHORT_TOP_K=3).
MIN_FIRES_LONG = 100
MIN_FIRES_SHORT = 60

# Polars dt.weekday: Monday=1 … Sunday=7 (ISO). Fold A/B era weekly expiry = Thursday.
_EXPIRY_WEEKDAY = 4

_STRUCTURAL_SKIPS = frozenset({"MISSING_PATH", "EMPTY_WAIT"})


def min_fires_for(direction: str) -> int:
    return MIN_FIRES_LONG if direction == "long" else MIN_FIRES_SHORT


def last_entry_for(direction: str):
    return LONG_LAST_ENTRY if direction == "long" else SHORT_LAST_ENTRY


def tb_label_col(direction: str) -> str:
    return "tb_label_long" if direction == "long" else "tb_label_short"


def session_ids(dates: list) -> np.ndarray:
    """Map session dates to dense integer ids (stable order of first appearance)."""
    sess_idx = {d: i for i, d in enumerate(dict.fromkeys(dates))}
    return np.array([sess_idx[d] for d in dates], dtype=int)


def session_block_diff_ci(
    a: np.ndarray,
    a_dates: list,
    b: np.ndarray,
    b_dates: list,
    n_boot: int,
    rng: np.random.Generator,
) -> tuple[float, float, float]:
    """
    Session-block bootstrap 95% CI on mean(a) − mean(b).

    Session ids are assigned from the union of dates so fired and skipped
    share the same calendar mapping. Empty-side draws fall back to the point.
    """
    point = float(a.mean() - b.mean())
    sess_idx = {d: i for i, d in enumerate(dict.fromkeys([*a_dates, *b_dates]))}
    a_sess = np.array([sess_idx[d] for d in a_dates], dtype=int)
    b_sess = np.array([sess_idx[d] for d in b_dates], dtype=int)
    sessions = np.unique(np.concatenate([a_sess, b_sess]))
    a_map = {int(s): np.flatnonzero(a_sess == s) for s in np.unique(a_sess)}
    b_map = {int(s): np.flatnonzero(b_sess == s) for s in np.unique(b_sess)}
    boot = np.empty(n_boot)
    for i in range(n_boot):
        drawn = rng.choice(sessions, size=sessions.size, replace=True)
        a_idx = np.concatenate(
            [a_map.get(int(s), np.empty(0, dtype=int)) for s in drawn]
        )
        b_idx = np.concatenate(
            [b_map.get(int(s), np.empty(0, dtype=int)) for s in drawn]
        )
        if a_idx.size == 0 or b_idx.size == 0:
            boot[i] = point
            continue
        boot[i] = float(a[a_idx].mean() - b[b_idx].mean())
    return point, float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


__all__ = [
    "H_BARS",
    "N_BOOT",
    "MIN_SESSIONS",
    "K_LONG",
    "K_SHORT",
    "MIN_FIRES_LONG",
    "MIN_FIRES_SHORT",
    "ROUND_TRIP_COST",
    "ARCHIVE_ROUND_TRIP_COST",
    "_EXPIRY_WEEKDAY",
    "_STRUCTURAL_SKIPS",
    "MetricResult",
    "format_report",
    "session_block_mean_ci",
    "session_block_diff_ci",
    "session_ids",
    "k_for",
    "side_sign",
    "min_fires_for",
    "last_entry_for",
    "tb_label_col",
]
