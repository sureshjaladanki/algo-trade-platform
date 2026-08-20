"""G1 — cost-free T+3 earnings residual vs Nifty on the G0 calendar.

Charter is written from complete-window n, then the residual is computed.
Skip overnight-repriced names is G3, not this gate.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import polars as pl

from src.events.constants import (
    BOOT_SEED,
    G1_AUTHORITY_SESSIONS,
    G1_ERA_SPLIT_YEAR,
    G1_FAR_SESSIONS,
    G1_NEAR_SESSIONS,
    MIN_FOLD_EVENTS,
    N_BOOT,
    NSE_EQUITY_CLOSE,
    PRIOR_EVENT_SIGMA_BPS,
)
from src.events.daily_panel import load_nifty_daily, load_or_build_daily_panel
from src.events.g0 import load_or_build_results_calendar
from src.events.paths import (
    G1_CHARTER_PATH,
    G1_LOG_PATH,
    G1_MEMO_PATH,
    GOLDEN_DIR,
)
from src.events.residual import (
    first_close_containing,
    offset_date,
    residual_bps,
    session_index,
)
from src.events.stats import (
    clip_disaster,
    fold_sign_pass,
    mde_bps,
    session_block_mean_ci,
    three_way_verdict,
)

_EVENT_SCHEMA = {
    "symbol": pl.String,
    "period_end": pl.Date,
    "event_at": pl.Datetime,
    "entry_date": pl.Date,
    "prev_date": pl.Date,
    "announcement_residual_bps": pl.Float64,
    "side": pl.Float64,
    "overnight_residual_bps": pl.Float64,
    "year": pl.Int32,
    "era": pl.String,
}


@dataclass(frozen=True)
class HoldSpec:
    name: str
    sessions: int
    role: str


AUTHORITY = HoldSpec(
    name="T_to_Tp3",
    sessions=G1_AUTHORITY_SESSIONS,
    role="authority — T close → T+3 close",
)
COMPANION_NEAR = HoldSpec(
    name="T_to_Tp1",
    sessions=G1_NEAR_SESSIONS,
    role="companion — T close → T+1 close",
)
COMPANION_FAR = HoldSpec(
    name="T_to_Tp5",
    sessions=G1_FAR_SESSIONS,
    role="companion — T close → T+5 close",
)


def _as_datetime(value: object) -> dt.datetime:
    if isinstance(value, dt.datetime):
        return value
    raise TypeError(f"event_at must be datetime, got {type(value)!r}")


def _close_map(panel: pl.DataFrame) -> dict[tuple[str, dt.date], float]:
    return {
        (row["symbol"], row["date"]): float(row["close"])
        for row in panel.iter_rows(named=True)
    }


def _open_map(panel: pl.DataFrame) -> dict[tuple[str, dt.date], float]:
    return {
        (row["symbol"], row["date"]): float(row["open"])
        for row in panel.iter_rows(named=True)
    }


def _date_close_map(daily: pl.DataFrame) -> dict[dt.date, float]:
    return {row["date"]: float(row["close"]) for row in daily.iter_rows(named=True)}


def _date_open_map(daily: pl.DataFrame) -> dict[dt.date, float]:
    return {row["date"]: float(row["open"]) for row in daily.iter_rows(named=True)}


def build_g1_events(
    calendar: pl.DataFrame,
    panel: pl.DataFrame,
    nifty_daily: pl.DataFrame,
    session_dates: list[dt.date],
) -> pl.DataFrame:
    """One row per filing with a PIT-safe T and a non-zero announcement side."""
    index = session_index(session_dates)
    closes = _close_map(panel)
    opens = _open_map(panel)
    nifty_close = _date_close_map(nifty_daily)
    nifty_open = _date_open_map(nifty_daily)
    rows: list[dict] = []
    for event in calendar.iter_rows(named=True):
        event_at = _as_datetime(event["event_at"])
        t = first_close_containing(
            session_dates, event_at, NSE_EQUITY_CLOSE, index
        )
        if t is None:
            continue
        prev = offset_date(session_dates, index, t, -1)
        if prev is None:
            continue
        symbol = event["symbol"]
        start_px = closes.get((symbol, prev))
        end_px = closes.get((symbol, t))
        start_n = nifty_close.get(prev)
        end_n = nifty_close.get(t)
        if start_px is None or end_px is None or start_n is None or end_n is None:
            continue
        announcement = residual_bps(start_px, end_px, start_n, end_n)
        if announcement == 0.0:
            continue
        overnight = None
        open_px = opens.get((symbol, t))
        open_n = nifty_open.get(t)
        if open_px is not None and open_n is not None:
            overnight = residual_bps(start_px, open_px, start_n, open_n)
        rows.append(
            {
                "symbol": symbol,
                "period_end": event["period_end"],
                "event_at": event_at,
                "entry_date": t,
                "prev_date": prev,
                "announcement_residual_bps": announcement,
                "side": 1.0 if announcement > 0.0 else -1.0,
                "overnight_residual_bps": overnight,
                "year": t.year,
                "era": "early" if t.year < G1_ERA_SPLIT_YEAR else "late",
            }
        )
    if not rows:
        return pl.DataFrame(schema=_EVENT_SCHEMA)
    return pl.DataFrame(rows)


def measure_hold(
    events: pl.DataFrame,
    panel: pl.DataFrame,
    nifty_daily: pl.DataFrame,
    session_dates: list[dt.date],
    spec: HoldSpec,
) -> pl.DataFrame:
    index = session_index(session_dates)
    closes = _close_map(panel)
    nifty_close = _date_close_map(nifty_daily)
    rows: list[dict] = []
    for event in events.iter_rows(named=True):
        t = event["entry_date"]
        end = offset_date(session_dates, index, t, spec.sessions)
        if end is None:
            continue
        symbol = event["symbol"]
        start_px = closes.get((symbol, t))
        end_px = closes.get((symbol, end))
        start_n = nifty_close.get(t)
        end_n = nifty_close.get(end)
        if start_px is None or end_px is None or start_n is None or end_n is None:
            continue
        residual = residual_bps(start_px, end_px, start_n, end_n)
        rows.append(
            {
                **event,
                "window": spec.name,
                "exit_date": end,
                "residual_bps": residual,
                "trade_residual_bps": event["side"] * residual,
            }
        )
    if not rows:
        return pl.DataFrame(
            schema={
                **_EVENT_SCHEMA,
                "window": pl.String,
                "exit_date": pl.Date,
                "residual_bps": pl.Float64,
                "trade_residual_bps": pl.Float64,
            }
        )
    return pl.DataFrame(rows)


def count_complete_hold(
    events: pl.DataFrame,
    panel: pl.DataFrame,
    nifty_daily: pl.DataFrame,
    session_dates: list[dt.date],
    spec: HoldSpec,
) -> int:
    """Count events with both window closes. Does not compute residuals."""
    index = session_index(session_dates)
    closes = _close_map(panel)
    nifty_close = _date_close_map(nifty_daily)
    n = 0
    for event in events.iter_rows(named=True):
        t = event["entry_date"]
        end = offset_date(session_dates, index, t, spec.sessions)
        if end is None:
            continue
        symbol = event["symbol"]
        if closes.get((symbol, t)) is None or closes.get((symbol, end)) is None:
            continue
        if nifty_close.get(t) is None or nifty_close.get(end) is None:
            continue
        n += 1
    return n


def evaluate_trades(
    measured: pl.DataFrame,
    column: str = "trade_residual_bps",
) -> dict:
    n = measured.height
    prior_mde = mde_bps(PRIOR_EVENT_SIGMA_BPS, n) if n else float("inf")
    empty = {
        "n": 0,
        "n_clipped": 0,
        "prior_mde_bps": prior_mde,
        "sample_sigma_bps": None,
        "sample_mde_bps": None,
        "point_bps": None,
        "ci_low_bps": None,
        "ci_high_bps": None,
        "n_sessions": 0,
        "sign_ok": False,
        "n_pos_folds": 0,
        "n_folds": 0,
        "fold_means": {},
        "early_bps": None,
        "late_bps": None,
        "early_n": 0,
        "late_n": 0,
        "verdict": "INCONCLUSIVE",
        "mde_used_bps": prior_mde,
    }
    if n == 0:
        return empty
    raw = measured[column].to_numpy()
    clipped = clip_disaster(raw)
    n_clipped = int((clipped != raw).sum())
    sample_sigma = float(np.std(clipped, ddof=1)) if n > 1 else float(np.std(clipped))
    sample_mde = mde_bps(sample_sigma, n)
    session_ids = np.array(
        [d.toordinal() for d in measured["entry_date"].to_list()],
        dtype=np.int64,
    )
    rng = np.random.default_rng(BOOT_SEED)
    interval = session_block_mean_ci(clipped, session_ids, N_BOOT, rng)
    clipped_df = measured.with_columns(trade=pl.Series(clipped))
    fold_tbl = clipped_df.group_by("year").agg(mean=pl.col("trade").mean(), n=pl.len())
    fold_means = {
        str(r["year"]): float(r["mean"]) for r in fold_tbl.iter_rows(named=True)
    }
    fold_counts = {str(r["year"]): int(r["n"]) for r in fold_tbl.iter_rows(named=True)}
    sign_ok, n_pos, n_folds = fold_sign_pass(
        fold_means, fold_counts, min_events=MIN_FOLD_EVENTS
    )
    early = clipped_df.filter(pl.col("era") == "early")
    late = clipped_df.filter(pl.col("era") == "late")
    early_bps = float(early["trade"].mean()) if early.height else None
    late_bps = float(late["trade"].mean()) if late.height else None
    verdict = three_way_verdict(interval, prior_mde, sign_ok=sign_ok)
    return {
        "n": n,
        "n_clipped": n_clipped,
        "prior_mde_bps": prior_mde,
        "sample_sigma_bps": sample_sigma,
        "sample_mde_bps": sample_mde,
        "point_bps": interval.point,
        "ci_low_bps": interval.ci_low,
        "ci_high_bps": interval.ci_high,
        "n_sessions": interval.n_sessions,
        "sign_ok": sign_ok,
        "n_pos_folds": n_pos,
        "n_folds": n_folds,
        "fold_means": fold_means,
        "early_bps": early_bps,
        "late_bps": late_bps,
        "early_n": early.height,
        "late_n": late.height,
        "verdict": verdict,
        "mde_used_bps": prior_mde,
    }


def book_g_sentence(verdict: str) -> str:
    if verdict == "PASS":
        return (
            "PASS. T+3 residual exists on a passable harness. G2 is the next spend. "
            "Do not skip overnight-repriced names here — that is G3. "
            "T+1 and T+5 are companions; do not move authority after seeing them."
        )
    if verdict == "FAIL":
        return (
            "FAIL. Stop Book G. Do not scan other event types, move the window, "
            "or substitute headline sentiment."
        )
    return (
        "INCONCLUSIVE. Stops Book G. The repair (more 2025 filings) is a vendor "
        "purchase, which this plan forbids. Do not move the window."
    )


def render_charter(n: int) -> str:
    mde = mde_bps(PRIOR_EVENT_SIGMA_BPS, n) if n else float("inf")
    mde_txt = f"{mde:.1f}" if n else "n/a"
    return "\n".join(
        [
            "# G1 charter — earnings drift, gross (cost-free)",
            "",
            "Written **before** the residual peek. Windows are not revised after seeing results.",
            "Skip overnight-repriced names is **G3**, not this gate.",
            "",
            "| Lock | Choice |",
            "|---|---|",
            "| Instrument | Cash delivery, single-name vs Nifty close |",
            "| Universe | G0 quarterly first-broadcast calendar, GOLDEN panel |",
            "| Friction | **None.** 45 bps and 20.8% wait for G2 |",
            "| T | First session close that provably contains the NSE timestamp |",
            "| Close cutoff | 15:30 IST. Date-only / at-or-after-close → next session |",
            "| Side | Sign of residual T−1 close → T close. Vendor SUE is not used |",
            "| Authority window | T close → T+3 close |",
            "| Companions | T→T+1 and T→T+5. Not authority |",
            "| Statistic | Mean trade residual (side × residual), disaster-clipped −500 bps, session-block 95% CI, fold sign |",
            "| Required effect | CI lower bound > 0 on T+3 |",
            "| Hurdle | 0 bps (existence) |",
            "| Economic hurdle | **45 bps** (printed beside MDE; charged in G2, not here) |",
            "| σ prior | 600 bps |",
            f"| MDE | **{mde_txt} bps** (n={n}, σ=600, 80% power two-sided) |",
            f"| Bootstrap | session-block, n_boot={N_BOOT}, seed={BOOT_SEED} |",
            f"| Folds | calendar year of T; sign test among years with ≥{MIN_FOLD_EVENTS} events |",
            "| Disaster clip | 500 bps floor, keep the row |",
            "| Decay | 2015–19 vs 2020–25 is a column, not a gate |",
            "| Annual / half-year | Not mixed in |",
            "",
            "INCONCLUSIVE or FAIL stops Book G. Do not buy 2025 Integrated Filing.",
            "Do not add guidance or sentiment. Do not promote a companion.",
            "",
        ]
    )


def _bps(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}"


def render_block(title: str, result: dict) -> list[str]:
    if result["n"] == 0:
        return [f"### {title}", "", "n=0. INCONCLUSIVE.", ""]
    folds = result.get("fold_means", {})
    fold_txt = ", ".join(f"{k}: {v:.1f}" for k, v in sorted(folds.items()))
    return [
        f"### {title}",
        "",
        f"- n={result['n']} sessions={result['n_sessions']} clipped={result['n_clipped']}",
        f"- MDE (prior σ, printed first): **{result['prior_mde_bps']:.1f} bps**",
        "- economic hurdle (G2): **45 bps**",
        f"- point {result['point_bps']:.1f} bps, CI [{result['ci_low_bps']:.1f}, {result['ci_high_bps']:.1f}]",
        f"- sample σ {result['sample_sigma_bps']:.1f} bps, sample MDE {result['sample_mde_bps']:.1f} bps",
        (
            f"- era 2015–19 n={result['early_n']} {_bps(result['early_bps'])} bps; "
            f"2020–25 n={result['late_n']} {_bps(result['late_bps'])} bps"
        ),
        f"- fold sign {result['n_pos_folds']}/{result['n_folds']} ({fold_txt})",
        f"- **verdict: {result['verdict']}**",
        "",
    ]


def render_memo(auth: dict, companions: dict[str, dict]) -> str:
    lines = [
        "# G1 — Earnings drift, gross",
        "",
        "**Gate:** G1, cost-free. **Date:** 2026-08-19. Charter: `docs/next/g1-charter.md`.",
        "",
        "Authority is T close → T+3 close. Side = sign of T−1→T residual vs Nifty.",
        "Overnight-gap skip is G3, not this print.",
        "",
        "## Authority",
        "",
        *render_block("T+3", auth),
        "## Companions (not authority)",
        "",
    ]
    for label, result in companions.items():
        lines.extend(render_block(label, result))
    lines.extend(["## Book G", "", book_g_sentence(auth["verdict"]), ""])
    return "\n".join(lines)


def _print_mde_then_result(label: str, result: dict) -> None:
    print(f"{label} n={result['n']} MDE={result['prior_mde_bps']:.1f} bps")
    if result["n"] == 0:
        print(f"{label} verdict=INCONCLUSIVE")
        return
    print(
        f"{label} point={result['point_bps']:.1f} "
        f"CI=[{result['ci_low_bps']:.1f}, {result['ci_high_bps']:.1f}] "
        f"verdict={result['verdict']}"
    )


def write_g1_charter(n: int) -> str:
    charter = render_charter(n)
    G1_CHARTER_PATH.write_text(charter, encoding="utf-8")
    return charter


def run_g1(*, peek: bool = True) -> dict:
    panel = load_or_build_daily_panel()
    nifty_daily = load_nifty_daily(GOLDEN_DIR)
    session_dates = nifty_daily["date"].to_list()
    filings = load_or_build_results_calendar()
    events = build_g1_events(filings, panel, nifty_daily, session_dates)
    n = count_complete_hold(events, panel, nifty_daily, session_dates, AUTHORITY)
    charter = write_g1_charter(n)
    print(charter)
    if not peek:
        return {"events": events, "n": n, "charter": charter}
    print("--- peek ---")
    auth_rows = measure_hold(events, panel, nifty_daily, session_dates, AUTHORITY)
    near = measure_hold(events, panel, nifty_daily, session_dates, COMPANION_NEAR)
    far = measure_hold(events, panel, nifty_daily, session_dates, COMPANION_FAR)
    auth = evaluate_trades(auth_rows)
    companions = {
        "T+1": evaluate_trades(near),
        "T+5": evaluate_trades(far),
    }
    _print_mde_then_result("authority T+3", auth)
    for label, result in companions.items():
        _print_mde_then_result(f"companion {label}", result)
    memo = render_memo(auth, companions)
    G1_MEMO_PATH.write_text(memo, encoding="utf-8")
    G1_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    G1_LOG_PATH.write_text(charter + "\n--- peek ---\n" + memo, encoding="utf-8")
    print(memo)
    print(f"wrote {G1_MEMO_PATH}")
    return {
        "events": events,
        "measured": auth_rows,
        "near": near,
        "far": far,
        "authority": auth,
        "companions": companions,
        "charter": charter,
        "memo": memo,
    }


def main() -> None:
    run_g1()


if __name__ == "__main__":
    main()
