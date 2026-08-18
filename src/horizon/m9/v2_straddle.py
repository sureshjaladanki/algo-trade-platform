"""M9 V2 stub — gross ATM-straddle PnL from EOD FO settle marks.

Clock is weaker than the remaining-session product: the signal is a morning
15m residual; the mark is T settle → T+1 settle on the held strike/expiry.
Cost-free. Bid-ask / STT belong to V3.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from src.utils.eval_common import N_BOOT, session_block_mean_ci

BPS = 1.0e4


@dataclass(frozen=True)
class V2StubResult:
    n: int
    n_sessions: int
    mean_bps: float
    ci_lo: float
    ci_hi: float
    mde: float
    verdict: str
    held_share: float
    note: str = ""


def morning_long_vol_sessions(panel: pl.DataFrame) -> pl.DataFrame:
    """
    First bar of each (symbol, session) with q50 > implied remaining range.

    Pre-registered long-vol default (charter: long premium when forecast says
    implied is cheap). Requires ``range_q50`` and ``range_imp_atm``.
    """
    first = (
        panel.sort("date")
        .group_by(["symbol", "date_only"], maintain_order=True)
        .first()
    )
    return first.filter(pl.col("range_q50") > pl.col("range_imp_atm")).select(
        ["symbol", "date_only"]
    )


def held_straddle_pnl(
    selected: pl.DataFrame,
    atm: pl.DataFrame,
    marks: pl.DataFrame,
) -> pl.DataFrame:
    """
    Enter ATM straddle on session T, exit same expiry/strike on the next
    marks session. PnL in bps of T underlying settle.
    """
    entry = (
        selected.join(
            atm.select(
                [
                    "symbol",
                    "date_only",
                    "atm_strike",
                    "expiry",
                    "straddle",
                    "underlying_close",
                ]
            ),
            on=["symbol", "date_only"],
            how="inner",
        )
        .filter(pl.col("straddle").is_not_null() & (pl.col("straddle") > 0.0))
        .rename(
            {
                "straddle": "straddle_entry",
                "atm_strike": "strike",
                "underlying_close": "spot_entry",
            }
        )
    )
    nxt = (
        marks.select(["symbol", "date_only", "expiry", "strike", "straddle"])
        .rename({"date_only": "date_exit", "straddle": "straddle_exit"})
    )
    held = entry.join(nxt, on=["symbol", "expiry", "strike"], how="inner").filter(
        pl.col("date_exit") > pl.col("date_only")
    )
    if held.height == 0:
        return held.with_columns(pnl_bps=pl.lit(None, dtype=pl.Float64))
    first_exit = held.group_by(["symbol", "date_only"]).agg(
        date_exit=pl.col("date_exit").min()
    )
    held = held.join(first_exit, on=["symbol", "date_only", "date_exit"], how="inner")
    return held.with_columns(
        pnl_bps=(pl.col("straddle_exit") - pl.col("straddle_entry"))
        / pl.col("spot_entry")
        * BPS
    )


def v2_session_block_gate(pnl: pl.DataFrame, *, fold: str) -> V2StubResult:
    """PASS if session-block CI LB > 0; FAIL if UB < 0; else INCONCLUSIVE."""
    if pnl.height == 0:
        return V2StubResult(
            n=0,
            n_sessions=0,
            mean_bps=float("nan"),
            ci_lo=float("nan"),
            ci_hi=float("nan"),
            mde=float("nan"),
            verdict="THIN",
            held_share=float("nan"),
            note=f"fold={fold} no held contracts",
        )
    values = pnl["pnl_bps"].to_numpy()
    sessions = pnl["date_only"].to_physical().to_numpy()
    rng = np.random.default_rng(0)
    point, lo, hi = session_block_mean_ci(values, sessions, N_BOOT, rng)
    mde = (hi - lo) / 2.0
    if lo > 0.0:
        verdict = "PASS"
    elif hi < 0.0:
        verdict = "FAIL"
    else:
        verdict = "INCONCLUSIVE"
    return V2StubResult(
        n=int(pnl.height),
        n_sessions=int(pnl["date_only"].n_unique()),
        mean_bps=point,
        ci_lo=lo,
        ci_hi=hi,
        mde=mde,
        verdict=verdict,
        held_share=1.0,
        note=f"fold={fold} held-contract T→T+1 settle stub",
    )
