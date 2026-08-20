"""G3 — T+3 residual restricted to a small overnight gap."""

from __future__ import annotations

import numpy as np
import polars as pl

from src.events.constants import G3_GAP_PERCENTILE, PRIOR_EVENT_SIGMA_BPS
from src.events.g1 import evaluate_trades, render_block
from src.events.g2 import with_net
from src.events.paths import G3_CHARTER_PATH, G3_LOG_PATH, G3_MEMO_PATH
from src.events.stats import mde_bps


def gap_threshold_bps(measured: pl.DataFrame, percentile: float = G3_GAP_PERCENTILE) -> float:
    have = measured.filter(pl.col("overnight_residual_bps").is_not_null())
    if have.height == 0:
        raise RuntimeError("G3: no overnight residuals to set the percentile")
    abs_gap = have["overnight_residual_bps"].abs().to_numpy()
    return float(np.quantile(abs_gap, percentile / 100.0))


def split_by_gap(
    measured: pl.DataFrame,
    threshold_bps: float,
) -> tuple[pl.DataFrame, pl.DataFrame, int]:
    have = measured.filter(pl.col("overnight_residual_bps").is_not_null())
    dropped = measured.height - have.height
    small = have.filter(pl.col("overnight_residual_bps").abs() <= threshold_bps)
    large = have.filter(pl.col("overnight_residual_bps").abs() > threshold_bps)
    return small, large, dropped


def book_g3_sentence(small: dict, large: dict) -> str:
    if small["verdict"] == "PASS":
        return (
            "PASS. The T+3 residual survives on names whose overnight gap sits "
            "at or below the pre-registered percentile. The edge is not only "
            "the already-repriced tail. Book G is a trade on this harness."
        )
    if large["verdict"] == "PASS" and small["verdict"] != "PASS":
        return (
            "STOP. The edge lives only where the overnight gap already repriced "
            "the news. There is no trade. Do not add guidance or sentiment."
        )
    if small["verdict"] == "FAIL":
        return (
            "FAIL. Small-gap T+3 does not clear zero. Stop Book G. "
            "Do not add guidance or sentiment."
        )
    return (
        "INCONCLUSIVE on the small-gap sleeve. Stops Book G. "
        "Do not move the percentile after seeing the print."
    )


def render_g3_memo(
    small: dict,
    large: dict,
    net_small: dict,
    threshold_bps: float,
    n_dropped: int,
) -> str:
    return "\n".join(
        [
            "# G3 — Gap already in",
            "",
            "**Gate:** G3. **Date:** 2026-08-19. Charter: `docs/next/g3-charter.md`.",
            "",
            (
                f"Keep events with |overnight residual| ≤ **{threshold_bps:.1f} bps** "
                f"({G3_GAP_PERCENTILE:.0f}th percentile of the G1 T+3 sample). "
                f"Dropped missing overnight: {n_dropped}."
            ),
            "",
            "## Authority (small overnight gap, cost-free T+3)",
            "",
            *render_block("Small-gap T+3", small),
            "## Companion (not authority)",
            "",
            *render_block("Large-gap T+3 (already repriced)", large),
            *render_block("Small-gap T+3 net of 45 bps and 20.8%", net_small),
            "## Book G",
            "",
            book_g3_sentence(small, large),
            "",
        ]
    )


def run_g3(measured: pl.DataFrame) -> dict:
    if G3_CHARTER_PATH.read_text(encoding="utf-8").find("Written **before**") < 0:
        raise RuntimeError("G3 charter is missing; will not peek")
    threshold = gap_threshold_bps(measured)
    small, large, dropped = split_by_gap(measured, threshold)
    small_mde = (
        mde_bps(PRIOR_EVENT_SIGMA_BPS, small.height) if small.height else float("inf")
    )
    print(
        f"G3 threshold={threshold:.1f} bps p={G3_GAP_PERCENTILE:.0f} "
        f"small_n={small.height} large_n={large.height} dropped={dropped}"
    )
    print(f"G3 small n={small.height} MDE={small_mde:.1f} bps")
    print("--- peek ---")
    small_res = evaluate_trades(small)
    large_res = evaluate_trades(large)
    net_small = evaluate_trades(with_net(small), "net_bps")
    print(
        f"G3 small n={small_res['n']} MDE={small_res['prior_mde_bps']:.1f} bps "
        f"point={small_res['point_bps']} verdict={small_res['verdict']}"
    )
    print(
        f"G3 large n={large_res['n']} MDE={large_res['prior_mde_bps']:.1f} bps "
        f"point={large_res['point_bps']} verdict={large_res['verdict']}"
    )
    memo = render_g3_memo(small_res, large_res, net_small, threshold, dropped)
    G3_MEMO_PATH.write_text(memo, encoding="utf-8")
    G3_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    G3_LOG_PATH.write_text(memo, encoding="utf-8")
    print(memo)
    print(f"wrote {G3_MEMO_PATH}")
    return {
        "threshold_bps": threshold,
        "small": small_res,
        "large": large_res,
        "net_small": net_small,
        "memo": memo,
    }


def main() -> None:
    raise SystemExit("G3 runs from python -m src.events.g_series after a G2 PASS")


if __name__ == "__main__":
    main()
