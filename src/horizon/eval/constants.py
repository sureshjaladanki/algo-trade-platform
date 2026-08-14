"""Tier 2 Horizon eval — locked constants and sleeve helpers."""

from __future__ import annotations

from src.horizon.session import long_entry_ok_expr, short_entry_ok_expr
from src.precision.session import LONG_TOP_K as K_LONG, SHORT_TOP_K as K_SHORT
from src.regime.types import DailyRegime, IntradayRegime
from src.utils.eval_common import (
    H_BARS,
    MIN_BARS,
    MIN_SESSIONS,
    N_BOOT,
    MetricResult,
    format_report,
    session_block_mean_ci,
)

# Locked K — live Precision registry (docs/horizon-tier2-eval-verdict.md).

MIN_BARS_LONG = MIN_BARS
MIN_BARS_SHORT = 150
MIN_NAMES_PER_BAR = 5

# Null IC must not show spurious positive skill (H10).
H10_NULL_ABS_MAX = 0.02

# Eval-only flat-bar proxy for circuit / UC (D1 / H7). Not a training feature.
CIRCUIT_RANGE_EPS = 1e-4

# Diagnostic K-sweep only — never silently changes gated K_LONG / K_SHORT.
K_SWEEP = (3, 5, 8)

# S1 Short circuit/UC hygiene — measured FAIL on A+B (see v1.1 revision); leave off.
APPLY_S1_SHORT = False

# L1 Long inference-time rank-3 floor — measured FAIL dual-fold soft-H3; leave off.
APPLY_L1_LONG = False

_TRADEABLE_DAILY = (
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
)

_SLEEVE = {
    "long": {
        "intraday": IntradayRegime.TREND_UP.value,
        "valid_label": "valid_label_long",
        "entry_ok": long_entry_ok_expr,
        "tb_col": "tb_label_long",
        "mfe_col": "mfe_frac_long",
        "mfe_bps_col": "mfe_bps_long",
        "abs_peak_bar_col": "mfe_abs_peak_bar_long",
        "mfe50_first_bar_col": "mfe50_first_bar_long",
        "peak_bar_col": "mfe_peak_bar_long",
        "giveback_col": "giveback_frac_long",
        "exit_h_col": "tb_exit_h_long",
    },
    "short": {
        "intraday": IntradayRegime.TREND_DOWN.value,
        "valid_label": "valid_label_short",
        "entry_ok": short_entry_ok_expr,
        "tb_col": "tb_label_short",
        "mfe_col": "mfe_frac_short",
        "mfe_bps_col": "mfe_bps_short",
        "abs_peak_bar_col": "mfe_abs_peak_bar_short",
        "mfe50_first_bar_col": None,  # Long-only TP-floor ledger
        "peak_bar_col": "mfe_peak_bar_short",
        "giveback_col": "giveback_frac_short",
        "exit_h_col": "tb_exit_h_short",
    },
}

# Polars dt.weekday: Monday=1 … Sunday=7 (ISO). Fold A/B era weekly expiry = Thursday.
_EXPIRY_WEEKDAY = 4


def min_bars_for(direction: str) -> int:
    return MIN_BARS_LONG if direction == "long" else MIN_BARS_SHORT


def k_for(direction: str) -> int:
    return K_LONG if direction == "long" else K_SHORT


def side_sign(direction: str) -> float:
    return 1.0 if direction == "long" else -1.0


__all__ = [
    "H_BARS",
    "N_BOOT",
    "MIN_SESSIONS",
    "MIN_BARS",
    "MIN_BARS_LONG",
    "MIN_BARS_SHORT",
    "MIN_NAMES_PER_BAR",
    "H10_NULL_ABS_MAX",
    "CIRCUIT_RANGE_EPS",
    "K_SWEEP",
    "APPLY_S1_SHORT",
    "APPLY_L1_LONG",
    "K_LONG",
    "K_SHORT",
    "_TRADEABLE_DAILY",
    "_SLEEVE",
    "_EXPIRY_WEEKDAY",
    "MetricResult",
    "format_report",
    "session_block_mean_ci",
    "min_bars_for",
    "k_for",
    "side_sign",
]
