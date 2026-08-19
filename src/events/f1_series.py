"""F1a / F1b / F1c. Does not move the F1-effective T−20 window."""

from __future__ import annotations

import polars as pl

from src.events.announcements import attach_announcement_dates
from src.events.constants import N_BOOT, PRIOR_EVENT_SIGMA_BPS
from src.events.daily_panel import load_nifty_daily, load_or_build_daily_panel
from src.events.event_pool import build_membership_events, flag_tradable_universe
from src.events.f1 import (
    COMPANION_REVERSAL,
    evaluate_sleeve,
    measure_window,
    render_sleeve_block,
)
from src.events.paths import (
    F1_SERIES_LOG_PATH,
    F1A_CHARTER_PATH,
    F1A_MEMO_PATH,
    F1C_MEMO_PATH,
    GOLDEN_DIR,
)
from src.events.residual import first_session_on_or_after, window_residual_bps
from src.events.stats import mde_bps

_SIDE = {"addition": 1.0, "deletion": -1.0}


def measure_f1a(
    panel: pl.DataFrame,
    events: pl.DataFrame,
    calendar: list,
) -> pl.DataFrame:
    rows: list[dict] = []
    for event in events.iter_rows(named=True):
        if event["announcement_date"] is None:
            continue
        start = first_session_on_or_after(calendar, event["announcement_date"])
        end = event["effective_date"]
        if start is None or start >= end:
            continue
        residual = window_residual_bps(panel, event["symbol"], start, end)
        if residual is None:
            continue
        side = _SIDE[event["event_type"]]
        rows.append(
            {
                "family": event["family"],
                "symbol": event["symbol"],
                "event_type": event["event_type"],
                "effective_date": end,
                "announcement_date": event["announcement_date"],
                "window": "f1a_announcement_to_effective",
                "residual_bps": residual,
                "trade_residual_bps": residual * side,
                "year": end.year,
            }
        )
    if not rows:
        return pl.DataFrame(
            schema={
                "family": pl.String,
                "symbol": pl.String,
                "event_type": pl.String,
                "effective_date": pl.Date,
                "announcement_date": pl.Date,
                "window": pl.String,
                "residual_bps": pl.Float64,
                "trade_residual_bps": pl.Float64,
                "year": pl.Int32,
            }
        )
    return pl.DataFrame(rows)


def count_f1a_complete(
    panel: pl.DataFrame,
    events: pl.DataFrame,
    calendar: list,
) -> dict[str, int]:
    symbols = set(panel["symbol"].unique().to_list())
    have = {
        s: set(panel.filter(pl.col("symbol") == s)["date"].to_list())
        for s in symbols
    }
    counts = {"addition": 0, "deletion": 0}
    for event in events.iter_rows(named=True):
        if event["announcement_date"] is None:
            continue
        start = first_session_on_or_after(calendar, event["announcement_date"])
        end = event["effective_date"]
        if start is None or start >= end:
            continue
        dates = have.get(event["symbol"], set())
        if start in dates and end in dates:
            counts[event["event_type"]] += 1
    return counts


def render_f1a_charter(n_add: int, n_del: int) -> str:
    mde_add = mde_bps(PRIOR_EVENT_SIGMA_BPS, n_add) if n_add else float("inf")
    mde_del = mde_bps(PRIOR_EVENT_SIGMA_BPS, n_del) if n_del else float("inf")
    return "\n".join(
        [
            "# F1a charter — announcement to effective (cost-free)",
            "",
            "Written **before** the F1a residual peek. This is not a move of the",
            "F1-effective T−20 window.",
            "",
            "| Lock | Choice |",
            "|---|---|",
            "| Instrument | Cash delivery, name vs Nifty close |",
            "| Friction | None |",
            "| Entry | Close of the first NSE session on or after the recovered announcement date |",
            "| Exit | Close of the PIT effective session |",
            "| Statistic | Mean trade residual, disaster-clipped −500 bps, session-block 95% CI, fold sign |",
            "| Additions | +(r_name − r_Nifty) |",
            "| Deletions | −(r_name − r_Nifty), separate sleeve |",
            "| Required effect | CI lower bound > 0 |",
            "| Hurdle | 0 bps |",
            "| σ prior | 600 bps |",
            f"| MDE additions | **{mde_add:.1f} bps** (n={n_add}) |",
            f"| MDE deletions | **{mde_del:.1f} bps** (n={n_del}) |",
            f"| Bootstrap | session-block, n_boot={N_BOOT}, seed=7 |",
            "",
            "Evening press releases may make the entry close pre-announcement;",
            "that is accepted as the recoverable free calendar, not interpolated.",
            "Ad-hoc events keep their actual notice, including short notice.",
            "",
        ]
    )


def _print_mde(label: str, result: dict) -> None:
    print(f"{label} n={result['n']} MDE={result['prior_mde_bps']:.1f} bps")
    if result["n"] == 0:
        print(f"{label} verdict=INCONCLUSIVE")
        return
    print(
        f"{label} point={result['point_bps']:.1f} "
        f"CI=[{result['ci_low_bps']:.1f}, {result['ci_high_bps']:.1f}] "
        f"verdict={result['verdict']}"
    )


def run_f1_series() -> None:
    panel = load_or_build_daily_panel()
    calendar = load_nifty_daily(GOLDEN_DIR)["date"].to_list()
    events = attach_announcement_dates(
        flag_tradable_universe(build_membership_events(calendar), panel)
    )
    n_complete = count_f1a_complete(panel, events, calendar)
    charter = render_f1a_charter(n_complete["addition"], n_complete["deletion"])
    F1A_CHARTER_PATH.write_text(charter, encoding="utf-8")
    print(charter)
    print("--- F1a peek ---")

    measured = measure_f1a(panel, events, calendar)
    add_a = evaluate_sleeve(measured, event_type="addition")
    del_a = evaluate_sleeve(measured, event_type="deletion")
    _print_mde("F1a additions", add_a)
    _print_mde("F1a deletions", del_a)

    f1a_memo = "\n".join(
        [
            "# F1a — Post-announcement existence",
            "",
            "**Gate:** F1a, cost-free. **Date:** 2026-08-19.",
            "Charter: `docs/next/f1a-charter.md`. Not a re-window of T−20.",
            "",
            *render_sleeve_block("Additions", add_a),
            *render_sleeve_block("Deletions", del_a),
            "## Book F",
            "",
            _f1a_sentence(add_a["verdict"], del_a["verdict"]),
            "",
        ]
    )
    F1A_MEMO_PATH.write_text(f1a_memo, encoding="utf-8")

    print("F1b ranking is python -m src.events.f1b (MCWB Next 50, not this runner)")

    print("--- F1c (pre-registered T→T+20 fade) ---")
    rev = measure_window(panel, events, COMPANION_REVERSAL, calendar)
    add_c = evaluate_sleeve(rev, event_type="addition")
    del_c = evaluate_sleeve(rev, event_type="deletion")
    _print_mde("F1c additions (authority)", add_c)
    _print_mde("F1c deletions (companion)", del_c)
    f1c_memo = "\n".join(
        [
            "# F1c — Post-effective reversal",
            "",
            "**Gate:** F1c, cost-free. **Date:** 2026-08-19.",
            "Window locked in the F1 charter before the first peek: T close → T+20 close, fade.",
            "Blueprint authority is **additions**. Deletions are a companion.",
            "",
            *render_sleeve_block("Additions (authority)", add_c),
            *render_sleeve_block("Deletions (companion)", del_c),
            "## Book F",
            "",
            (
                "F1c additions are the reversal gate. Do not promote the deletion "
                "companion or change T+20 after seeing the print."
            ),
            "",
        ]
    )
    F1C_MEMO_PATH.write_text(f1c_memo, encoding="utf-8")
    F1_SERIES_LOG_PATH.write_text(
        charter
        + "\n---\n"
        + f1a_memo
        + "\n---\nF1b: python -m src.events.f1b\n---\n"
        + f1c_memo,
        encoding="utf-8",
    )
    print(f"wrote {F1A_MEMO_PATH}")
    print(f"wrote {F1C_MEMO_PATH}")


def _f1a_sentence(add_v: str, del_v: str) -> str:
    if add_v == "FAIL" and del_v == "FAIL":
        return "FAIL. Stop Book F. Do not buy an event calendar or widen families."
    if add_v == "PASS" or del_v == "PASS":
        return (
            "F1a has a passing sleeve. F2 is the next spend on that sleeve only."
        )
    return (
        "INCONCLUSIVE. Repair is more history from this panel, not a different "
        "window after seeing the result. Do not open F2."
    )


def main() -> None:
    run_f1_series()


if __name__ == "__main__":
    main()
