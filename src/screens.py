"""Screens for Books C, A, and B. A1/A2 use the OptionsDX dump after A0.5."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from src.books.pead import (
    KILL_BPS,
    W_KILL,
    item_202_declaration,
    load_delist_identifiers,
    load_item_202_events,
    load_or_fetch_sp400_history,
    load_public_events,
    mid_cap_events,
    run_bound_screen,
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
from src.books.vrp_existence import (
    THETA_TAIL_START,
    collect_observations,
    collect_theta_tail,
    monthly_expiries,
    quote_dates,
    run_existence_screen,
    tenor_entry,
    theta_monthly_expiries,
)
from src.books.vrp_existence import (
    screen_declaration as existence_declaration,
)
from src.books.vrp_sleeve import (
    C1_MEASURED_BPS,
    PUTW_HURDLE_BPS,
    construct_cycles,
    run_sleeve_screen,
)
from src.books.vrp_sleeve import (
    screen_declaration as sleeve_declaration,
)
from src.books.vrp_spread import (
    CREDIT_RETAIN_MIN,
    DTE_HIGH,
    DTE_LOW,
    load_spreads,
    run_spread_screen,
)
from src.books.vrp_spread import (
    screen_declaration as spread_declaration,
)
from src.harness import MdeGateError, TrialLedger, print_mde, reset, run_declared
from src.optionsdx import OptionsDxDumpMissing, load_put_panel
from src.theta import ThetaUnavailable, list_expirations, puts_on_date
from src.tiingo import EOD_VERIFY_N, TiingoUnavailable, dump_usable_eod, eod_file_count, run_coverage
from src.vti import fetch_yahoo_bars, load_daily_bars, write_daily_bars
from src.yahoo import load_or_fetch

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


def run_book_a05() -> str:
    reset()
    decl = spread_declaration()
    ledger = _ledger()
    _ensure_registered(
        ledger,
        spec_id=decl.spec_id,
        book_id="A",
        hypothesis="SPX 20-25d 50-100-wide put-spread round-trip leaves >= 25% of credit",
    )
    mde_line = (
        f"n={decl.n:g} MDE={decl.mde:.1f} bps ratio={decl.mde_ratio:.2f} "
        f"(H3 closes A1 certification on the FREE window)"
    )
    try:
        print_mde(decl)
        mde_closed = False
    except MdeGateError:
        mde_closed = True
        print(mde_line, flush=True)
        ledger.abandon(decl.spec_id, "H3: FREE window cannot certify A1; cost screen only")
    try:
        spx = load_or_fetch("^GSPC")
        spreads, n_expiries = load_spreads(spx)
    except ThetaUnavailable as exc:
        body = f"""# A0.5 — $0 spread-cost kill screen

**Date:** 2026-08-21
**Spec:** `{decl.spec_id}`
**Spend:** $0 (ThetaData FREE). **Not A1.**

MDE printed first: {mde_line}.

**Blocked:** {exc}. Confirm `THETADATA_API_KEY` in `.env`, then re-run
`poetry run python -m src.screens A0.5`.

Do not buy CBOE until this screen authorizes A1.
"""
        (DOCS / "a05-spread-cost-screen.md").write_text(body, encoding="utf-8")
        return f"A0.5 blocked: {exc}"
    screen = run_spread_screen(spreads, n_expiries=n_expiries)
    if screen.authorize_a1:
        verdict = "authorize A1 CBOE dump"
    elif screen.sparse:
        verdict = "Book A STOP (chains too sparse to build the structure)"
    else:
        verdict = "Book A STOP (spread round-trip eats 25% credit retention)"
    body = f"""# A0.5 — $0 spread-cost kill screen

**Date:** 2026-08-21
**Spec:** `{decl.spec_id}`
**Spend:** $0 (ThetaData FREE EOD SPX chains from 2023-06-01 + Yahoo `^GSPC`)
**Not A1.** {mde_line}. This peek is a kill screen on *spread cost*, not implied-minus-realized.

| | |
|---|---|
| Monthly expiries attempted | {screen.n_expiries} |
| Spreads reconstructed (30–45 DTE, 20–25Δ, 50–100 wide) | {screen.n} |
| Mean credit (points) | {screen.mean_credit:.2f} |
| Mean bid–ask both legs / credit | {screen.mean_bid_ask_pct_of_credit:.1f}% |
| Mean all-in round-trip / credit | {screen.mean_all_in_pct_of_credit:.1f}% |
| Mean credit retained after all-in | {100 * screen.mean_retained:.1f}% |
| Retention hurdle | {100 * CREDIT_RETAIN_MIN:.0f}% |
| ATM `costs` bucket all-in high | {screen.atm_all_in_high:.1f}% of premium |
| Sparse / unbuildable | {screen.sparse} |
| Gate | **{verdict}** |

Fees from `src.costs.vertical_spread_round_trip` (two legs, open+close). Delta from bid/ask mid + SPX close, European Black–Scholes, working r=5% q=1.3%.
"""
    (DOCS / "a05-spread-cost-screen.md").write_text(body, encoding="utf-8")
    if not mde_closed:
        ledger.mark_run(decl.spec_id)
    return (
        f"A0.5 {verdict}: retained {100 * screen.mean_retained:.1f}% "
        f"on n={screen.n}/{screen.n_expiries}"
    )


def run_book_b05() -> str:
    reset()
    events, universe, _prices = load_item_202_events()
    listed, n_form25, yahoo_gone = load_delist_identifiers()
    ever = load_or_fetch_sp400_history()
    mid = mid_cap_events(events)
    if not mid:
        body = """# B0.5 — $0 Item 2.02 bound

**Date:** 2026-08-21
**Spec:** `B.item-202-listed-bound`
**Gate:** **inconclusive** — no mid-cap Item 2.02 events after ADV and long-only filters.
"""
        (DOCS / "b05-item-202-bound.md").write_text(body, encoding="utf-8")
        return "B0.5 inconclusive: no mid-cap Item 2.02 events"
    decl = item_202_declaration(len(mid))
    ledger = _ledger()
    _ensure_registered(
        ledger,
        spec_id=decl.spec_id,
        book_id="B",
        hypothesis="Listed Item 2.02 mid-cap 20-day net drift ≥ 40 bps; publish w",
    )
    try:
        print_mde(decl)
    except MdeGateError:
        body = f"""# B0.5 — $0 Item 2.02 bound

**Date:** 2026-08-21
**Spec:** `{decl.spec_id}`
**Gate:** **closed without a peek** — n={len(mid)} n_eff={decl.n_effective:g} MDE={decl.mde:.1f} bps ratio={decl.mde_ratio:.2f}.
"""
        (DOCS / "b05-item-202-bound.md").write_text(body, encoding="utf-8")
        return f"B0.5 MDE closed: n={len(mid)} ratio={decl.mde_ratio:.2f}"
    screen = run_declared(
        lambda: run_bound_screen(
            events=mid,
            listed=listed,
            ever=ever,
            delisted=yahoo_gone,
            n_form25=n_form25,
        )
    )
    ledger.mark_run(decl.spec_id)
    if screen.kill:
        verdict = "Book B STOP (Item 2.02 listed mid-cap net < 40 bps)"
    elif screen.b0_informs:
        verdict = "B0 still informs B1; Norgate trial authorized only if you proceed"
    else:
        verdict = "B0 buy-panel gate revoked (w ≥ 50.6% or bound < 40); B1 trial is the only honest test"
    mid_txt = (
        f"{screen.mean_mid_bps:.1f}" if screen.mean_mid_bps is not None else "n/a"
    )
    body = f"""# B0.5 — $0 Item 2.02 bound

**Date:** 2026-08-22
**Spec:** `{decl.spec_id}`
**Spend:** $0 (EDGAR EFTS Item 2.02 + Form 25/15 + Wikipedia S&P 400 history + Yahoo / Tiingo / successor bars)
**Not B1.** Lock 5: listed-only mean; free stitch shrinks `w`. A miss closes Book B. A hit does not certify the panel.

MDE printed first: n={screen.n_mid}, n_eff={decl.n_effective:g}, MDE={decl.mde:.1f} bps, ratio={decl.mde_ratio:.2f}.

| | |
|---|---|
| Universe | Listed names Yahoo still serves, $ADV > $20M, top ~1,500 (S&P 1500 candidates: {len(universe)}) |
| Item 2.02 mid-cap events | {screen.n_mid} |
| Mean net-of-cost 20-day drift | **{mid_txt} bps** |
| Kill threshold | {KILL_BPS:.0f} bps |
| Current S&P 400 (N_listed) | {screen.n_listed} |
| Yahoo-missing / unrecovered former members (N_missing) | {screen.n_missing} |
| Left the index (promoted/demoted/delisted) | {screen.n_left_index} |
| Form 25/15 unique CIKs 2010– | {screen.n_form25} |
| w = N_missing / (N_listed + N_missing) | **{100 * screen.w:.1f}%** |
| w that pulls B0's 80.9 bps to 40 at zero delisted drift | {100 * W_KILL:.1f}% |
| Membership missing mass | {100 * screen.w_membership:.1f}% |
| Zero-drift bound (1−w) × Item 2.02 mean | **{screen.bound_bps:.1f} bps** |
| Gate | **{verdict}** |

Long-only, t+1 start, mid-cap $20–100M ADV, working 25 bps cost. `w` is the share of the S&P 400 cohort with no free price tape (Yahoo, Tiingo EOD, or curated successor). Dirty identity (AHL, SIVB, CHK, …) stays in N_missing. Form 25/15 is the identifier count, including names that were never in the index.
"""
    (DOCS / "b05-item-202-bound.md").write_text(body, encoding="utf-8")
    return f"B0.5 {verdict}: mid {mid_txt} bps, w={100 * screen.w:.1f}%"


_A1_PASSED = False


def _cached_theta_expiries() -> list[date]:
    folder = REPO_ROOT / "data" / "raw" / "theta" / "SPX"
    if not folder.exists():
        return []
    days: list[date] = []
    for path in folder.glob("*.json"):
        stamp = path.stem.split("_")[0]
        days.append(date(int(stamp[:4]), int(stamp[4:6]), int(stamp[6:8])))
    return sorted(set(days))


def _theta_expiry_list() -> list[date]:
    try:
        return list_expirations("SPX")
    except ThetaUnavailable:
        return _cached_theta_expiries()


def _theta_puts(expiry: date, trade: date):
    try:
        return puts_on_date(root="SPX", expiry=expiry, trade_date=trade)
    except ThetaUnavailable:
        return []


def run_book_a1() -> str:
    global _A1_PASSED
    reset()
    try:
        panel = load_put_panel()
    except OptionsDxDumpMissing as exc:
        body = f"""# A1 — VRP existence

**Date:** 2026-08-21
**Spec:** `A.spx-put-spread-20-25d-30-45dte`
**Blocked:** {exc}. Place OptionsDX SPX EOD 7z files in `data/raw/optionsdx/SPX`.
"""
        (DOCS / "a1-vrp-existence.md").write_text(body, encoding="utf-8")
        return f"A1 blocked: {exc}"
    days = quote_dates(panel)
    dx_expiries = [day for day in monthly_expiries(panel) if day < THETA_TAIL_START]
    spx = load_or_fetch("^GSPC")
    last_bar = spx[-1].date
    theta_expiries = theta_monthly_expiries(_theta_expiry_list(), last_bar=last_bar)
    spx_days = [bar.date for bar in spx]
    n_plan = sum(
        1
        for expiry in dx_expiries
        if tenor_entry(expiry, days, lo=DTE_LOW, hi=DTE_HIGH, target=37) is not None
    ) + sum(
        1
        for expiry in theta_expiries
        if tenor_entry(expiry, spx_days, lo=DTE_LOW, hi=DTE_HIGH, target=37) is not None
    )
    decl = existence_declaration(max(n_plan, 1))
    ledger = _ledger()
    _ensure_registered(
        ledger,
        spec_id=decl.spec_id,
        book_id="A",
        hypothesis="20-25d 30-45 DTE IV-RV exceeds spread round-trip cost by 2x",
    )
    try:
        print_mde(decl)
    except MdeGateError:
        body = f"""# A1 — VRP existence

**Date:** 2026-08-21
**Spec:** `{decl.spec_id}`
**Gate:** **closed without a peek** — n={decl.n:g} MDE={decl.mde:.1f} bps ratio={decl.mde_ratio:.2f}.
"""
        (DOCS / "a1-vrp-existence.md").write_text(body, encoding="utf-8")
        return f"A1 MDE closed: n={decl.n:g} ratio={decl.mde_ratio:.2f}"
    n_expiries = len(dx_expiries) + len(theta_expiries)

    def _collect():
        gate_dx, grid_dx = collect_observations(panel, spx)
        gate_th, grid_th = collect_theta_tail(
            spx, expiries=theta_expiries, chain_loader=_theta_puts
        )
        return gate_dx + gate_th, grid_dx + grid_th

    gate, grid = run_declared(_collect)
    screen = run_existence_screen(gate, grid, n_expiries=n_expiries)
    ledger.mark_run(decl.spec_id)
    _A1_PASSED = screen.passed
    if screen.passed:
        verdict = "A1 pass — proceed to A2 on the same tape"
    elif not screen.exceed_2x:
        verdict = "Book A STOP (IV-RV <= 2x spread round-trip)"
    else:
        verdict = "Book A STOP (net sign unstable in sub-periods)"
    rows = "\n".join(
        f"| {start.isoformat()} – {stop.isoformat()} | {mean:.2f} | {n} |"
        for start, stop, mean, n in screen.subperiods_net
    )
    stress = "\n".join(
        f"| {year} | {'n/a' if value is None else f'{value:.2f}'} |"
        for year, value in screen.stress_raw.items()
    )
    grid_rows = "\n".join(
        f"| {bucket}Δ | {tenor} DTE | {mean:.2f} | {n} |"
        for bucket, tenor, mean, n in screen.grid
    )
    window = (
        f"{screen.first.isoformat()} – {screen.last.isoformat()}"
        if screen.first and screen.last
        else "n/a"
    )
    dx_gate = [row for row in gate if row.expiry < THETA_TAIL_START]
    dx_n = len(dx_gate)
    dx_raw = (
        sum(row.raw for row in dx_gate) / dx_n if dx_gate else float("nan")
    )
    dx_cost = (
        sum(row.cost_vol for row in dx_gate) / dx_n if dx_gate else float("nan")
    )
    dx_mult = dx_raw / dx_cost if dx_gate and dx_cost > 0 else float("nan")
    tail_n = screen.n - dx_n
    body = f"""# A1 — VRP existence

**Date:** 2026-08-22
**Spec:** `{decl.spec_id}`
**Spend:** $0 OptionsDX SPX EOD 2012–2023 + ThetaData FREE 2024–present (Cboe DataShop historical cart $580, above the $100 stop)
**Tape:** bid/ask + Yahoo `^GSPC`. Vendor IV/greeks unused. Splice at expiry 2024-01-01 (OptionsDX before, ThetaData FREE after). Completes the pre-registered 2012–present window, including the named 2024 stress year. Not an extension to 2005–2011.

MDE printed first: n={decl.n:g} MDE={decl.mde:.1f} bps ratio={decl.mde_ratio:.2f}.

OptionsDX-only (already published): n={dx_n} IV−RV {dx_raw:.2f} vs cost {dx_cost:.2f} ({dx_mult:.2f}×). Theta tail gate n={tail_n}.

| | |
|---|---|
| Monthly expiries | {screen.n_expiries} |
| Gate observations (20–25Δ, 30–45 DTE) | {screen.n} |
| Window | {window} |
| Mean IV−RV (vol pts) | {screen.mean_raw:.2f} |
| Mean spread round-trip (vol pts) | {screen.mean_cost:.2f} |
| Multiple (IV−RV / cost) | **{screen.multiple:.2f}×** (hurdle 2×) |
| Mean net of cost | {screen.mean_net:.2f} |
| Spread-cost (not ATM fallback) | {screen.n_spread_cost}/{screen.n} |
| Sign stable net in ≥ 4 of 5 sub-periods | {screen.sign_stable_net} |
| Gate | **{verdict}** |

### Sub-periods (net of spread cost)

| Window | Mean | n |
|---|---|---|
{rows}

### Stress years (raw IV−RV)

| Year | Mean |
|---|---|
{stress}

### Pre-registered grid (raw IV−RV, ATM cost not applied)

| Delta | Tenor | Mean IV−RV | n |
|---|---|---|---|
{grid_rows}

0DTE and 7DTE rows document the Blueprint closure of 0DTE as an alpha book. They are not an A1 search. Do not extend to 2005–2011.
"""
    (DOCS / "a1-vrp-existence.md").write_text(body, encoding="utf-8")
    if not screen.passed:
        archive = DOCS / "archive"
        archive.mkdir(exist_ok=True)
        stop = f"""# STOP — Book A

**Date:** 2026-08-22
**Milestone:** A1
**Reason:** {verdict}

Mean IV−RV {screen.mean_raw:.2f} vol pts vs spread cost {screen.mean_cost:.2f} ({screen.multiple:.2f}×). Sign stable net: {screen.sign_stable_net}. Splice: OptionsDX through 2023, ThetaData FREE 2024–present. A2/A3 are not run. Do not buy Cboe. Do not search other delta buckets.

Detail: [a1-vrp-existence.md](../a1-vrp-existence.md)
"""
        (archive / "book-a-stop.md").write_text(stop, encoding="utf-8")
    return (
        f"A1 {verdict}: IV-RV {screen.mean_raw:.2f} vs cost {screen.mean_cost:.2f} "
        f"({screen.multiple:.2f}×) n={screen.n}/{screen.n_expiries}"
    )


def run_book_a2() -> str:
    if not _A1_PASSED:
        return "A2 skipped: A1 did not pass"
    reset()
    panel = load_put_panel()
    spx = load_or_fetch("^GSPC")
    built = construct_cycles(panel, spx)
    cycles = [cycle for _, cycle in built]
    decl = sleeve_declaration(max(len(cycles), 1))
    ledger = _ledger()
    _ensure_registered(
        ledger,
        spec_id=decl.spec_id,
        book_id="A",
        hypothesis="Sleeve after-tax beats PUTW by 75 bps, Sharpe>=0.4, DD<=25%, no Book C dilution",
    )
    try:
        print_mde(decl)
    except MdeGateError:
        return f"A2 MDE closed: n={decl.n:g} ratio={decl.mde_ratio:.2f}"
    _, _, putw, vti_points, put_index = load_public_inputs()
    screen = run_declared(
        lambda: run_sleeve_screen(
            cycles, putw=putw, vti_points=vti_points, put_index=put_index
        )
    )
    ledger.mark_run(decl.spec_id)
    if screen.passed:
        verdict = "A2 pass — paper A3 next"
    else:
        misses = []
        if not screen.beat_putw:
            misses.append("PUTW +75 bps")
        if not screen.sharpe_ok:
            misses.append("Sharpe")
        if not screen.dd_ok:
            misses.append("max DD")
        if not screen.no_dilute:
            misses.append("Book C dilution")
        verdict = "Book A STOP (" + ", ".join(misses) + ")"
    blends = "\n".join(
        f"| {100 * w:.0f}% | {bps:.1f} |" for w, bps in sorted(screen.blends.items())
    )
    body = f"""# A2 — sleeve economics

**Date:** 2026-08-21
**Spec:** `{decl.spec_id}`
**Tape:** same OptionsDX SPX EOD 2012–2023 as A1. No second purchase.

MDE printed first: n={decl.n:g} MDE={decl.mde:.1f} bps ratio={decl.mde_ratio:.2f}.

| | |
|---|---|
| Cycles | {screen.n} |
| Window | {screen.start.isoformat()} – {screen.end.isoformat()} ({screen.years:.2f}y) |
| Sleeve after-tax CAGR | {100 * screen.sleeve_after_tax:.2f}% |
| Packaged PUT after-tax | {100 * screen.putw_after_tax:.2f}% |
| Sleeve vs PUT | **{screen.vs_putw_bps:.0f} bps/yr** (hurdle {PUTW_HURDLE_BPS:.0f}) |
| After-tax VTI (same window) | {100 * screen.vti_after_tax:.2f}% |
| Sleeve Sharpe | {screen.sharpe:.2f} (hurdle 0.4) |
| Sleeve max DD / notional | {100 * screen.max_dd:.1f}% (hurdle 25%) |
| 20% blend excess vs VTI | **{screen.blend_20_bps:.1f} bps** (Book C {C1_MEASURED_BPS:.1f}) |
| Gate | **{verdict}** |

### Blend weights (after-tax excess vs VTI, bps/yr)

| Sleeve weight | Excess |
|---|---|
{blends}

Rule: short 20–25Δ / 50–100 wide, 30–45 DTE, close at 50% credit or 14 DTE. Sized to 8% of $250k max loss. Tax: Section 1256 28% with a December fraction mark. VTI comparison is reported honestly and is not by itself an A2 kill; dilution of Book C at 20% weight is.
"""
    (DOCS / "a2-vrp-sleeve.md").write_text(body, encoding="utf-8")
    if not screen.passed:
        archive = DOCS / "archive"
        archive.mkdir(exist_ok=True)
        stop = f"""# STOP — Book A

**Date:** 2026-08-21
**Milestone:** A2
**Reason:** {verdict}

A3 is not run. Do not re-optimize width or exit rule.

Detail: [a2-vrp-sleeve.md](../a2-vrp-sleeve.md)
"""
        (archive / "book-a-stop.md").write_text(stop, encoding="utf-8")
    return (
        f"A2 {verdict}: vs PUT {screen.vs_putw_bps:.0f} bps, Sharpe {screen.sharpe:.2f}, "
        f"DD {100 * screen.max_dd:.1f}%, blend20 {screen.blend_20_bps:.1f} bps"
    )


def run_book_a3() -> str:
    if not _A1_PASSED:
        return "A3 skipped: A1 did not pass"
    body = """# A3 — tradability

**Date:** 2026-08-21
**Status:** **Not started.** A3 is 60 sessions of paper fills of the exact A2 rule (mid + 25% of spread cap, no chasing). It needs a funded IBKR paper account, not more tape.

Do not run live capital. Lock 7.
"""
    (DOCS / "a3-tradability.md").write_text(body, encoding="utf-8")
    return "A3 not started: 60 IBKR paper sessions after A2"


def run_tiingo_coverage() -> str:
    try:
        report = run_coverage(verify=True)
    except TiingoUnavailable as exc:
        return f"Tiingo blocked: {exc}"
    usable = report.n_recovered + report.n_otc_history
    samples = [hit for hit in report.hits if hit.n_bars > 0 or hit.eod_error]
    sample_rows = "\n".join(
        f"| {hit.symbol} | {hit.status} | {hit.exchange} | {hit.start} | {hit.end} | "
        f"{hit.n_bars or hit.eod_error} | {hit.first} | {hit.last} |"
        for hit in samples
    )
    absent = ", ".join(hit.symbol for hit in report.hits if hit.status == "absent")
    body = f"""# Tiingo $0 coverage — Yahoo-missing S&P 400

**Date:** 2026-08-22
**Spend:** $0 (Tiingo Starter, 500 unique symbols/mo)
**Not B1.** Lock 5: ticker-keyed, no licensed index PIT. A hit tightens the B0.5 bound; it does not certify the panel.

| | |
|---|---|
| Current S&P 400 | {report.n_listed} |
| Left the index (ever − current) | {report.n_left} |
| Yahoo-missing leavers | {report.n_missing} |
| In Tiingo ticker file | {report.n_in_file} ({100 * report.file_coverage:.1f}%) |
| Recovered (major exchange, series ended) | {report.n_recovered} |
| OTC with history back to 2010 | {report.n_otc_history} |
| Usable (recovered + OTC history) | **{usable} ({100 * report.usable_coverage:.1f}%)** |
| OTC stub (short history) | {report.n_stub} |
| Reject (known splice / ticker reuse) | {report.n_reject} |
| Absent from Tiingo | {report.n_absent} |
| EOD series on disk | {eod_file_count()} |
| EOD verified this run | {report.n_eod_ok} ok / {report.n_eod_fail} fail (cap {EOD_VERIFY_N}) |

EOD sample (adj close, cached under `data/raw/tiingo`):

| Symbol | Status | Exchange | File start | File end | Bars / error | First bar | Last bar |
|---|---|---|---|---|---|---|---|
{sample_rows}

Absent from Tiingo ticker file: {absent or "none"}.

EOD/file disagreements in the sample are possible (ticker reuse, late starts). Treat usable % as an upper bound until remaining names are dumped. Tiingo Starter allows 50 requests/hour. This is not Norgate: no PERMNO, no licensed S&P 400 PIT, CHK/JAVA/PCS rejected on identity.
"""
    (DOCS / "b075-tiingo-coverage.md").write_text(body, encoding="utf-8")
    return (
        f"Tiingo coverage: {usable}/{report.n_missing} usable "
        f"({100 * report.usable_coverage:.1f}%); EOD {report.n_eod_ok} ok"
    )


def run_tiingo_dump() -> str:
    try:
        dump = dump_usable_eod()
    except TiingoUnavailable as exc:
        return f"Tiingo dump blocked: {exc}"
    coverage = run_tiingo_coverage()
    failed = f"; failed {', '.join(dump.failures)}" if dump.failures else ""
    return (
        f"{coverage}; dump cached {dump.n_cached}/{dump.n_usable}, "
        f"fetched {dump.n_fetched}, failed {dump.n_failed}{failed}"
    )


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
    parser = argparse.ArgumentParser(description="Run $0 C/A/B and A0.5/B0.5 screens")
    parser.add_argument(
        "books",
        nargs="*",
        default=["A0.5", "B0.5"],
        help="Books to run: C A B A0.5 B0.5 A1 A2 A3 TIINGO TIINGO-DUMP (default next kill-ladders)",
    )
    args = parser.parse_args(argv)
    wanted = [book.upper() for book in args.books]
    lines: list[str] = []
    runners = {
        "C": run_book_c,
        "A": run_book_a,
        "B": run_book_b,
        "A0.5": run_book_a05,
        "B0.5": run_book_b05,
        "A1": run_book_a1,
        "A2": run_book_a2,
        "A3": run_book_a3,
        "TIINGO": run_tiingo_coverage,
        "TIINGO-DUMP": run_tiingo_dump,
    }
    for book in wanted:
        print(f"=== Book {book} ===")
        line = runners[book]()
        print(line)
        lines.append(line)
    if any(book in {"C", "A", "B"} for book in wanted):
        write_summary(lines)
        print("wrote docs/zero-spend-feasibility.md")


if __name__ == "__main__":
    main()
