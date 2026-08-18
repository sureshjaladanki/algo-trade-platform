"""P1 V2 — remaining-session short Nifty ATM straddle (gross, mid–mid).

Not the name-level EOD stub in ``v2_straddle.py``. Entry 09:45, flatten 15:15.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from src.horizon.fresh.friction import BPS
from src.horizon.fresh.gates import GateResult, mde_from_ci
from src.horizon.m9.index_option_store import (
    STT_OPTIONS_SELL,
    TICK_INR,
)
from src.utils.eval_common import N_BOOT, session_block_mean_ci

V2_THIN_N = 30
V2_THIN_SESSIONS = 20


def attach_short_straddle_pnl(session_marks: pl.DataFrame) -> pl.DataFrame:
    """
    Gross short-straddle PnL in fraction of entry spot (mid–mid).

    ``pnl = (mid_entry − mid_exit) / spot_entry``. V3 columns are attached
    but not used by the V2 gate.
    """
    return session_marks.with_columns(
        pnl=(pl.col("mid_entry") - pl.col("mid_exit")) / pl.col("spot_entry"),
        spread_cost=(
            (pl.col("mid_entry") - pl.col("bid_entry"))
            + (pl.col("ask_exit") - pl.col("mid_exit"))
        )
        / pl.col("spot_entry"),
        stt_cost=pl.lit(STT_OPTIONS_SELL) * pl.col("mid_entry") / pl.col("spot_entry"),
        tick_cost=pl.lit(4.0 * TICK_INR) / pl.col("spot_entry"),
    )


def v2_selected_pnl(
    selected: pl.DataFrame,
    session_marks: pl.DataFrame,
) -> pl.DataFrame:
    """Inner-join frozen V2p-c dates onto marked sessions."""
    dates = selected.select("date_only").unique()
    marked = attach_short_straddle_pnl(session_marks)
    return dates.join(marked, on="date_only", how="inner")


def v2_session_gate(
    pnl: pl.DataFrame,
    *,
    fold: str,
    n_boot: int = N_BOOT,
    seed: int = 0,
) -> GateResult:
    """Cost-free session-block CI on mean short-straddle PnL. PASS if LB > 0."""
    y = pnl["pnl"].to_numpy().astype(float)
    sess = pnl["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    m = np.isfinite(y)
    n = int(m.sum())
    n_sess = int(np.unique(sess[m]).size) if n else 0
    if n < V2_THIN_N or n_sess < V2_THIN_SESSIONS:
        return GateResult(
            "V2",
            fold,
            float("nan"),
            0.0,
            False,
            f"thin n={n} sess={n_sess}",
            verdict="INCONCLUSIVE",
        )
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(y[m], sess[m], n_boot, rng)
    mde = mde_from_ci(lo, hi)
    passed = lo > 0.0
    return GateResult(
        "V2",
        fold,
        point,
        0.0,
        passed,
        f"CI=[{lo * BPS:+.1f},{hi * BPS:+.1f}]bps "
        f"mde={mde * BPS:.1f}bps n={n} sess={n_sess}",
        mde=mde,
        ci_lo=lo,
        ci_hi=hi,
        verdict="PASS" if passed else "FAIL",
    )
