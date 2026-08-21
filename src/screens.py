"""$0 public screens for Books C, A, and B.

Not C2, A1, or B1. A green A/B screen is permission to buy tape later.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.books.pead import (
    KILL_BPS,
    load_public_events,
    mid_cap_events,
    run_pead_screen,
)
from src.books.pead import (
    screen_declaration as pead_declaration,
)
from src.books.tax_engine import C1_HURDLE_BPS, run_harvest_sim
from src.books.vrp import (
    load_public_inputs,
    nonoverlapping,
    run_vrp_screen,
    vrp_points,
)
from src.books.vrp import (
    screen_declaration as vrp_declaration,
)
from src.harness import MdeGateError, TrialLedger, print_mde, reset, run_declared
from src.vti import fetch_yahoo_bars, load_daily_bars, write_daily_bars

REPO_ROOT = Path(__file__).resolve().parent.parent
VTI_DAILY = REPO_ROOT / "data" / "raw" / "vti_daily.csv"
DOCS = REPO_ROOT / "docs"


def _vti_bars():
    if VTI_DAILY.exists():
        return load_daily_bars(VTI_DAILY)
    bars = fetch_yahoo_bars()
    write_daily_bars(bars, VTI_DAILY)
    return bars


def _ledger() -> TrialLedger:
    return TrialLedger.load()


def _ensure_registered(ledger: TrialLedger, *, spec_id: str, book_id: str, hypothesis: str) -> None:
    if any(trial.spec_id == spec_id for trial in ledger.trials):
        return
    ledger.register(spec_id=spec_id, book_id=book_id, hypothesis=hypothesis)


def run_book_c() -> str:
    reset()
    result = run_harvest_sim(_vti_bars())
    verdict = "pass" if result.passed else "fail"
    return (
        f"C1 {verdict}: {result.excess_bps_per_year:.1f} bps/yr, "
        f"{result.wash_sale_violations} washes, hurdle {C1_HURDLE_BPS:.0f}"
    )


def run_book_a() -> str:
    reset()
    vix, spx, putw, vti_points, put_index = load_public_inputs()
    decl = vrp_declaration(len(nonoverlapping(vrp_points(vix, spx))))
    ledger = _ledger()
    _ensure_registered(
        ledger,
        spec_id=decl.spec_id,
        book_id="A",
        hypothesis="VIX minus subsequent 21-day SPX RV exceeds expensive-end SPX cost",
    )
    try:
        print_mde(decl)
    except MdeGateError:
        body = f"""# A0 — $0 VIX–RV / PUTW screen

**Date:** 2026-08-21
**Spec:** `{decl.spec_id}`
**Gate:** **closed without a peek** — MDE {decl.mde:.2f} vol points, ratio {decl.mde_ratio:.2f}.

"""
        (DOCS / "a0-public-vrp-screen.md").write_text(body, encoding="utf-8")
        return f"A0 MDE closed: n={decl.n:g} ratio={decl.mde_ratio:.2f}"
    screen = run_declared(
        lambda: run_vrp_screen(
            vix, spx, putw=putw, vti_points=vti_points, put_index=put_index
        )
    )
    ledger.mark_run(decl.spec_id)
    rows = "\n".join(
        f"| {start.isoformat()} – {stop.isoformat()} | {mean:.2f} | {n} |"
        for start, stop, mean, n in screen.subperiods_high
    )
    stress = "\n".join(
        f"| {year} | {value:.2f} |"
        for year, value in screen.stress_raw.items()
        if value is not None
    )
    putw_block = "_PUTW series unavailable._"
    if screen.putw:
        p = screen.putw
        put_dd = (
            f"{100 * p.put_index_max_dd:.1f}%"
            if p.put_index_max_dd is not None
            else "n/a"
        )
        stress_putw = ", ".join(
            f"{year}: {100 * ret:.1f}%" for year, ret in sorted(p.stress_putw.items())
        )
        putw_block = f"""Source: `{p.source}` (PUTW Yahoo history is unusable; CBOE PUT index is the packaged put-write path). Ordinary-income column taxes index year-returns at the working 40% rate when the series has no distributions.

| Window | {p.start.isoformat()} – {p.end.isoformat()} |
| PUTW/PUT before-tax CAGR | {100 * p.putw_before_tax:.2f}% |
| After-tax packaged (ordinary) | {100 * p.putw_after_tax_ordinary:.2f}% |
| After-tax VTI (same window) | {100 * p.vti_after_tax:.2f}% |
| DIY 1256 marked CAGR | {100 * p.diy_1256_marked:.2f}% |
| 1256 vs ordinary wedge | {p.tax_wedge_bps:.0f} bps/yr |
| Packaged max drawdown (window) | {100 * p.putw_max_dd:.1f}% |
| CBOE PUT index max drawdown (full) | {put_dd} |
| Stress years | {stress_putw or "n/a"} |"""
    verdict = "buy CBOE tape" if screen.buy_cboe else "skip CBOE"
    body = f"""# A0 — $0 VIX–RV / PUTW screen

**Date:** 2026-08-21
**Spec:** `{decl.spec_id}`
**Spend:** $0 (Yahoo VIX, SPX, PUTW, VTI; working SPX ATM 30–45 cost)
**Not A1.** A green screen is permission to buy CBOE SPX EOD. It does not certify the 20–25Δ put-spread.

## VIX minus subsequent 21-day SPX RV

Non-overlapping {screen.n} windows. Cost haircut from `src.costs` SPX ATM 30–45 (mid and all-in high).

| | vol points |
|---|---|
| Mean raw VIX–RV | {screen.mean_raw:.2f} |
| Net of mid cost | {screen.mean_net_mid:.2f} |
| Net of expensive-end cost | {screen.mean_net_high:.2f} |
| Sign stable in ≥ 4 of 5 sub-periods (expensive) | {screen.sign_stable_high} |
| Gate | **{verdict}** |

### Sub-periods (net of expensive-end cost)

| Window | Mean | n |
|---|---|---|
{rows}

### Stress years (raw VIX–RV)

| Year | Mean |
|---|---|
{stress}

## PUTW vs after-tax VTI

{putw_block}

PUTW max drawdown is cash-secured puts, not the defined-risk spread, so it is an upper bound on short-vol pain, not an A2 kill.

"""
    (DOCS / "a0-public-vrp-screen.md").write_text(body, encoding="utf-8")
    return (
        f"A0 {verdict}: net-high {screen.mean_net_high:.2f} vol pts, "
        f"n={screen.n}, sign_stable={screen.sign_stable_high}"
    )


def run_book_b() -> str:
    reset()
    events = load_public_events()
    mid = mid_cap_events(events)
    if not mid:
        body = """# B0 — $0 listed PEAD screen

**Date:** 2026-08-21
**Spec:** `B.public-listed-pead`
**Gate:** **inconclusive** — no mid-cap listed events after ADV and long-only filters.

"""
        (DOCS / "b0-public-pead-screen.md").write_text(body, encoding="utf-8")
        return "B0 inconclusive: no mid-cap events"
    decl = pead_declaration(len(mid))
    ledger = _ledger()
    _ensure_registered(
        ledger,
        spec_id=decl.spec_id,
        book_id="B",
        hypothesis="Listed mid-cap 8-K long-only 20-day net drift ≥ 40 bps",
    )
    try:
        print_mde(decl)
    except MdeGateError:
        body = f"""# B0 — $0 listed PEAD screen

**Date:** 2026-08-21
**Spec:** `{decl.spec_id}`
**Spend:** $0 (EDGAR master.idx + Yahoo listed names)
**Not B1.** MDE gate closed the book without a peek.

n={len(mid)} mid-cap events, n_eff={decl.n_effective:g}, MDE={decl.mde:.1f} bps, hypothesized={decl.hypothesized_effect:g}. Ratio {decl.mde_ratio:.2f} > 0.5.

"""
        (DOCS / "b0-public-pead-screen.md").write_text(body, encoding="utf-8")
        return f"B0 MDE closed: n={len(mid)} ratio={decl.mde_ratio:.2f}"
    screen = run_declared(lambda: run_pead_screen(mid))
    ledger.mark_run(decl.spec_id)
    if screen.kill:
        verdict = "skip Polygon"
    elif screen.buy_polygon:
        verdict = "buy Polygon PIT panel"
    else:
        verdict = "inconclusive"
    mid_txt = (
        f"{screen.mean_mid_bps:.1f}" if screen.mean_mid_bps is not None else "n/a"
    )
    body = f"""# B0 — $0 listed PEAD screen

**Date:** 2026-08-21
**Spec:** `{decl.spec_id}`
**Spend:** $0 (EDGAR 8-K dates + Yahoo bars on names that still trade)
**Not B1.** Survivorship can only help a long-only drift. A miss kills Polygon spend. A hit is permission to buy a delisted PIT panel.

MDE printed first: n={screen.n_mid}, n_eff={decl.n_effective:g}, MDE={decl.mde:.1f} bps.

| | |
|---|---|
| Universe | Current S&P 400 listed names, 2010–2026 |
| Mid-cap events ($20–100M ADV at event) | {screen.n_mid} |
| Mean net-of-cost 20-day drift | **{mid_txt} bps** |
| Kill threshold | {KILL_BPS:.0f} bps |
| Working cost | mid-cap all-in high from `src.costs` (25 bps) |
| Gate | **{verdict}** |

Long-only: positive announcement-window return only. Forward window starts at t+1. Events are all 8-Ks, not Item 2.02 only, so non-earnings filings dilute the mean toward zero. This is not a PIT panel (delisted names are missing).

"""
    (DOCS / "b0-public-pead-screen.md").write_text(body, encoding="utf-8")
    return f"B0 {verdict}: mid {mid_txt} bps on n={screen.n_mid}"


def write_summary(lines: list[str]) -> None:
    body = """# $0 feasibility screens — Books C, A, B

**Date:** 2026-08-21
**Spend:** $0 (public data + working `costs` / `tax`). No CBOE, Polygon, IBKR, or fills.

These are go/no-go screens for *whether to spend later*. They are not the plan’s certified exits.

Run: `poetry run python -m src.screens`

"""
    for line in lines:
        body += f"- {line}\n"
    body += """
| Still blocked | Why |
|---|---|
| C2 | Funded IBKR year + 1099-B |
| A1 / A2 | CBOE SPX EOD |
| A3 | IBKR paper (free) after A1 |
| B1 | Polygon delisted PIT panel |
| B3 | IBKR paper (free) after B1 |

Detail: [c1-tax-location-proof.md](c1-tax-location-proof.md), [a0-public-vrp-screen.md](a0-public-vrp-screen.md), [b0-public-pead-screen.md](b0-public-pead-screen.md).
"""
    (DOCS / "zero-spend-feasibility.md").write_text(body, encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run $0 C/A/B screens")
    parser.add_argument(
        "books",
        nargs="*",
        default=["C", "A", "B"],
        help="Books to run: C A B (default all)",
    )
    args = parser.parse_args(argv)
    wanted = [book.upper() for book in args.books]
    lines: list[str] = []
    runners = {"C": run_book_c, "A": run_book_a, "B": run_book_b}
    for book in wanted:
        print(f"=== Book {book} ===")
        line = runners[book]()
        print(line)
        lines.append(line)
    write_summary(lines)
    print("wrote docs/zero-spend-feasibility.md")


if __name__ == "__main__":
    main()
