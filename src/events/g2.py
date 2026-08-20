"""G2 — 45 bps then 20.8% STCG on a passing G1 residual."""

from __future__ import annotations

import polars as pl

from src.events.constants import (
    DELIVERY_ROUND_TRIP_BPS,
    G2_ACTIVE_WEIGHT,
    PRIOR_EVENT_SIGMA_BPS,
    STCG_RATE,
)
from src.events.g1 import evaluate_trades, render_block
from src.events.paths import G2_CHARTER_PATH, G2_LOG_PATH, G2_MEMO_PATH
from src.events.stats import clip_disaster, mde_bps


def net_of_delivery_and_stcg(gross_bps: float) -> float:
    """Locked identity: net = (1 − 20.8%) × (gross − 45)."""
    return (1.0 - STCG_RATE) * (gross_bps - DELIVERY_ROUND_TRIP_BPS)


def with_net(measured: pl.DataFrame) -> pl.DataFrame:
    raw = measured["trade_residual_bps"].to_numpy()
    clipped = clip_disaster(raw)
    net = (1.0 - STCG_RATE) * (clipped - DELIVERY_ROUND_TRIP_BPS)
    return measured.with_columns(
        trade_clipped_bps=pl.Series(clipped),
        net_bps=pl.Series(net),
    )


def annual_contribution_bps(n: int, n_years: int, net_point_bps: float) -> float:
    """Unadjusted: active weight × events/year × per-event net. Ignores overlap."""
    if n_years <= 0:
        raise ValueError("n_years must be positive")
    return G2_ACTIVE_WEIGHT * (n / n_years) * net_point_bps


def book_g2_sentence(verdict: str, *, gross_bps: float | None) -> str:
    economic = ""
    if gross_bps is not None:
        economic = (
            f" G1 clipped gross {gross_bps:.1f} bps vs 45 bps delivery."
        )
    if verdict == "PASS":
        return (
            "PASS. T+3 residual clears 45 bps and 20.8% STCG. G3 is the next spend."
        )
    if verdict == "FAIL":
        return (
            "FAIL. Edge is below friction after 45 bps and 20.8%. Stop Book G. "
            "Do not open G3. Do not promote a G1 companion."
            + economic
        )
    return (
        "INCONCLUSIVE on the net statistic. Stops Book G. Do not open G3. "
        "Do not move the window, promote T+5, or buy a vendor calendar."
        + economic
    )


def render_g2_memo(result: dict, n_years: int, *, gross_bps: float | None) -> str:
    per_year = result["n"] / n_years if n_years and result["n"] else 0.0
    annual = (
        annual_contribution_bps(result["n"], n_years, result["point_bps"])
        if result["n"] and n_years
        else None
    )
    annual_txt = f"{annual:.1f}" if annual is not None else "n/a"
    gross_txt = f"{gross_bps:.1f}" if gross_bps is not None else "n/a"
    return "\n".join(
        [
            "# G2 — Net of delivery and STCG",
            "",
            "**Gate:** G2. **Date:** 2026-08-19. Charter: `docs/next/g2-charter.md`.",
            "",
            "net bps = 0.792 × (gross − 45), applied to the disaster-clipped G1 T+3 residual.",
            "Comparator is the after-tax passive hold: the residual is already vs Nifty;",
            "this gate charges STCG and delivery on the active excess.",
            "",
            f"G1 clipped gross mean **{gross_txt} bps** vs **45 bps** delivery.",
            "",
            "## Authority (T+3 net)",
            "",
            *render_block("T+3 after 45 bps and 20.8%", result),
            (
                f"Events/year {per_year:.1f} over {n_years} years. "
                f"Unadjusted annual contribution at {100 * G2_ACTIVE_WEIGHT:.0f}% "
                f"active weight: **{annual_txt} bps** of that sleeve (ignores overlap)."
            ),
            "",
            "## Book G",
            "",
            book_g2_sentence(result["verdict"], gross_bps=gross_bps),
            "",
        ]
    )


def run_g2(measured: pl.DataFrame) -> dict:
    if G2_CHARTER_PATH.read_text(encoding="utf-8").find("Written **before**") < 0:
        raise RuntimeError("G2 charter is missing; will not peek")
    netted = with_net(measured)
    n = netted.height
    prior_mde = mde_bps(PRIOR_EVENT_SIGMA_BPS, n) if n else float("inf")
    n_years = netted["year"].n_unique() if n else 0
    print(
        f"G2 n={n} MDE={prior_mde:.1f} bps hurdle=0 (net of 45 bps and 20.8%)"
    )
    print("--- peek ---")
    result = evaluate_trades(netted, "net_bps")
    if result["n"] == 0:
        print("G2 verdict=INCONCLUSIVE")
    else:
        print(
            f"G2 point={result['point_bps']:.1f} "
            f"CI=[{result['ci_low_bps']:.1f}, {result['ci_high_bps']:.1f}] "
            f"verdict={result['verdict']}"
        )
    memo = render_g2_memo(
        result,
        n_years,
        gross_bps=float(netted["trade_clipped_bps"].mean()) if n else None,
    )
    G2_MEMO_PATH.write_text(memo, encoding="utf-8")
    G2_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    G2_LOG_PATH.write_text(memo, encoding="utf-8")
    print(memo)
    print(f"wrote {G2_MEMO_PATH}")
    return {"measured": netted, "authority": result, "memo": memo}


def main() -> None:
    raise SystemExit("G2 runs from python -m src.events.g_series after a G1 PASS")


if __name__ == "__main__":
    main()
