"""F1 — cost-free existence peek on the dates F0 can actually support."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from src.events.constants import (
    BOOT_SEED,
    DISASTER_CLIP_BPS,
    F1_AUTHORITY_SESSIONS,
    F1_COMPANION_PRE_SESSIONS,
    F1_REVERSAL_SESSIONS,
    MIN_FOLD_EVENTS,
    N_BOOT,
    PRIOR_EVENT_SIGMA_BPS,
)
from src.events.daily_panel import load_nifty_daily, load_or_build_daily_panel
from src.events.event_pool import (
    build_membership_events,
    flag_tradable_universe,
)
from src.events.paths import F1_CHARTER_PATH, F1_LOG_PATH, F1_MEMO_PATH, GOLDEN_DIR
from src.events.residual import (
    offset_date,
    session_index,
    window_residual_bps,
)
from src.events.stats import (
    fold_sign_pass,
    mde_bps,
    session_block_mean_ci,
    three_way_verdict,
)

_SIDE = {"addition": 1.0, "deletion": -1.0}


@dataclass(frozen=True)
class WindowSpec:
    name: str
    start_offset: int
    end_offset: int
    fade: bool
    role: str


AUTHORITY = WindowSpec(
    name="effective_Tm20_to_T",
    start_offset=-F1_AUTHORITY_SESSIONS,
    end_offset=0,
    fade=False,
    role="authority — F1-effective, not F1a",
)
COMPANION_PRE = WindowSpec(
    name="companion_Tm40_to_Tm20",
    start_offset=-(F1_AUTHORITY_SESSIONS + F1_COMPANION_PRE_SESSIONS),
    end_offset=-F1_AUTHORITY_SESSIONS,
    fade=False,
    role="companion — pre-window, not pre-announcement",
)
COMPANION_REVERSAL = WindowSpec(
    name="f1c_T_to_Tp20",
    start_offset=0,
    end_offset=F1_REVERSAL_SESSIONS,
    fade=True,
    role="companion — F1c post-effective fade",
)


def measure_window(
    panel: pl.DataFrame,
    events: pl.DataFrame,
    spec: WindowSpec,
    calendar: list,
) -> pl.DataFrame:
    index = session_index(calendar)
    rows: list[dict] = []
    for event in events.iter_rows(named=True):
        t = event["effective_date"]
        start = offset_date(calendar, index, t, spec.start_offset)
        end = offset_date(calendar, index, t, spec.end_offset)
        if start is None or end is None:
            continue
        residual = window_residual_bps(panel, event["symbol"], start, end)
        if residual is None:
            continue
        side = _SIDE[event["event_type"]]
        trade = -residual if spec.fade else residual
        trade *= side
        rows.append(
            {
                "family": event["family"],
                "symbol": event["symbol"],
                "event_type": event["event_type"],
                "effective_date": t,
                "window": spec.name,
                "residual_bps": residual,
                "trade_residual_bps": trade,
                "year": t.year,
            }
        )
    if not rows:
        return pl.DataFrame(
            schema={
                "family": pl.String,
                "symbol": pl.String,
                "event_type": pl.String,
                "effective_date": pl.Date,
                "window": pl.String,
                "residual_bps": pl.Float64,
                "trade_residual_bps": pl.Float64,
                "year": pl.Int32,
            }
        )
    return pl.DataFrame(rows)


def evaluate_sleeve(measured: pl.DataFrame, *, event_type: str) -> dict:
    sleeve = measured.filter(pl.col("event_type") == event_type)
    n = sleeve.height
    prior_mde = mde_bps(PRIOR_EVENT_SIGMA_BPS, n) if n else float("inf")
    if n == 0:
        return {
            "event_type": event_type,
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
            "verdict": "INCONCLUSIVE",
            "mde_used_bps": prior_mde,
        }
    clipped_df = sleeve.with_columns(
        trade=pl.max_horizontal(
            pl.col("trade_residual_bps"), pl.lit(-DISASTER_CLIP_BPS)
        )
    )
    clipped = clipped_df["trade"].to_numpy()
    n_clipped = int(
        (clipped != sleeve["trade_residual_bps"].to_numpy()).sum()
    )
    sample_sigma = float(np.std(clipped, ddof=1)) if n > 1 else float(np.std(clipped))
    sample_mde = mde_bps(sample_sigma, n)
    session_ids = np.array(
        [d.toordinal() for d in sleeve["effective_date"].to_list()],
        dtype=np.int64,
    )
    rng = np.random.default_rng(BOOT_SEED)
    interval = session_block_mean_ci(clipped, session_ids, N_BOOT, rng)
    fold_tbl = clipped_df.group_by("year").agg(
        mean=pl.col("trade").mean(), n=pl.len()
    )
    fold_means = {
        str(r["year"]): float(r["mean"]) for r in fold_tbl.iter_rows(named=True)
    }
    fold_counts = {str(r["year"]): int(r["n"]) for r in fold_tbl.iter_rows(named=True)}
    sign_ok, n_pos, n_folds = fold_sign_pass(
        fold_means, fold_counts, min_events=MIN_FOLD_EVENTS
    )
    # Charter MDE (prior σ) sits beside the point estimate; sample MDE is a check.
    mde_used = prior_mde
    verdict = three_way_verdict(interval, mde_used, sign_ok=sign_ok)
    return {
        "event_type": event_type,
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
        "verdict": verdict,
        "mde_used_bps": mde_used,
    }


def count_complete(
    panel: pl.DataFrame,
    events: pl.DataFrame,
    spec: WindowSpec,
    calendar: list,
) -> dict[str, int]:
    """Count events with both window closes. Does not compute residuals."""
    index = session_index(calendar)
    counts = {"addition": 0, "deletion": 0}
    symbols = set(panel["symbol"].unique().to_list())
    dates_by_symbol: dict[str, set] = {
        s: set(
            panel.filter(pl.col("symbol") == s)["date"].to_list()
        )
        for s in symbols
    }
    for event in events.iter_rows(named=True):
        t = event["effective_date"]
        start = offset_date(calendar, index, t, spec.start_offset)
        end = offset_date(calendar, index, t, spec.end_offset)
        if start is None or end is None:
            continue
        have = dates_by_symbol.get(event["symbol"], set())
        if start in have and end in have:
            counts[event["event_type"]] += 1
    return counts


def render_charter(n_add: int, n_del: int) -> str:
    mde_add = mde_bps(PRIOR_EVENT_SIGMA_BPS, n_add) if n_add else float("inf")
    mde_del = mde_bps(PRIOR_EVENT_SIGMA_BPS, n_del) if n_del else float("inf")
    return "\n".join(
        [
            "# F1 charter — effect exists (cost-free)",
            "",
            "Written **before** the residual peek. Windows are not revised after seeing results.",
            "",
            "| Lock | Choice |",
            "|---|---|",
            "| Instrument | Cash delivery, single-name vs Nifty-50 close |",
            "| Friction | **None.** F1 is cost-free. 45 bps and 20.8% wait for F2 |",
            "| Dates | Effective session from PIT difference. Announcement dates unrecoverable |",
            "| Authority window | T−20 close → T close (F1-effective, **not** F1a) |",
            "| Statistic | Mean trade residual (bps), disaster-clipped at −500 bps, session-block 95% CI, fold sign test |",
            "| Additions | Long residual = r_name − r_Nifty |",
            "| Deletions | Short residual = −(r_name − r_Nifty). Evaluated separately |",
            "| Companions | T−40→T−20 (labelled pre-window, not pre-announcement); T→T+20 fade (F1c) |",
            "| Required effect | CI lower bound > 0 on the authority window |",
            "| Hurdle | 0 bps |",
            "| σ prior | 600 bps (blueprint sketch) |",
            f"| MDE additions | **{mde_add:.1f} bps** (n={n_add}, σ=600, 80% power two-sided) |",
            f"| MDE deletions | **{mde_del:.1f} bps** (n={n_del}, σ=600, 80% power two-sided) |",
            f"| Bootstrap | session-block, n_boot={N_BOOT}, seed={BOOT_SEED} |",
            f"| Folds | calendar year of T; sign test among years with ≥{MIN_FOLD_EVENTS} events |",
            "| Disaster clip | 500 bps floor, keep the row |",
            "| Purge | 5 calendar days on rolling year folds (no model is fit here) |",
            "",
            "F1a (announcement→effective) is **not** this peek. If MDE ≥ |point|, the verdict is INCONCLUSIVE;",
            "the repair is more event history from this panel, not a different window.",
            "",
        ]
    )


def render_sleeve_block(title: str, result: dict) -> list[str]:
    if result["n"] == 0:
        return [f"### {title}", "", "n=0. INCONCLUSIVE.", ""]
    folds = result.get("fold_means", {})
    fold_txt = ", ".join(
        f"{k}: {v:.1f}" for k, v in sorted(folds.items())
    )
    return [
        f"### {title}",
        "",
        f"- n={result['n']} sessions={result['n_sessions']} clipped={result['n_clipped']}",
        f"- MDE (prior σ, printed first): **{result['prior_mde_bps']:.1f} bps**",
        f"- point {result['point_bps']:.1f} bps, CI [{result['ci_low_bps']:.1f}, {result['ci_high_bps']:.1f}]",
        f"- sample σ {result['sample_sigma_bps']:.1f} bps, sample MDE {result['sample_mde_bps']:.1f} bps",
        f"- fold sign {result['n_pos_folds']}/{result['n_folds']} ({fold_txt})",
        f"- **verdict: {result['verdict']}**",
        "",
    ]


def book_f_sentence(add_v: str, del_v: str) -> str:
    if add_v == "FAIL" and del_v == "FAIL":
        return (
            "FAIL. Both sleeves fail. Stop Book F. Do not widen the window "
            "or buy an event calendar."
        )
    if add_v == "PASS" or del_v == "PASS":
        return (
            "The existence gate has a passing sleeve. F2 is the next spend "
            "on that sleeve only. The other sleeve is not pooled back in."
        )
    return (
        "INCONCLUSIVE on the authority window. Companion prints are not a "
        "repair. Do not move the window after seeing results. Do not open F2. "
        "Repair is more history from the existing panel."
    )


def render_verdict_memo(
    add_auth: dict,
    del_auth: dict,
    companions: dict[str, dict],
) -> str:
    lines = [
        "# F1 — Does the effect exist",
        "",
        "**Gate:** F1, cost-free. **Date:** 2026-08-19. Charter: `docs/next/f1-charter.md`.",
        "",
        "Authority window is F1-effective (T−20→T), not F1a.",
        "",
        "## Authority",
        "",
        *render_sleeve_block("Additions", add_auth),
        *render_sleeve_block("Deletions", del_auth),
        "## Companions (not authority)",
        "",
    ]
    for key, result in companions.items():
        lines.extend(render_sleeve_block(key, result))
    lines.extend(
        [
            "## Book F",
            "",
            book_f_sentence(add_auth["verdict"], del_auth["verdict"]),
            "",
        ]
    )
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


def run_f1() -> None:
    panel = load_or_build_daily_panel()
    calendar = load_nifty_daily(GOLDEN_DIR)["date"].to_list()
    events = flag_tradable_universe(
        build_membership_events(calendar),
        panel,
    )
    n_complete = count_complete(panel, events, AUTHORITY, calendar)
    charter = render_charter(n_complete["addition"], n_complete["deletion"])
    F1_CHARTER_PATH.write_text(charter, encoding="utf-8")
    print(charter)
    print("--- peek ---")

    auth = measure_window(panel, events, AUTHORITY, calendar)
    pre = measure_window(panel, events, COMPANION_PRE, calendar)
    rev = measure_window(panel, events, COMPANION_REVERSAL, calendar)

    add_auth = evaluate_sleeve(auth, event_type="addition")
    del_auth = evaluate_sleeve(auth, event_type="deletion")
    _print_mde_then_result("additions authority", add_auth)
    _print_mde_then_result("deletions authority", del_auth)

    companions = {
        "Additions companion T−40→T−20": evaluate_sleeve(pre, event_type="addition"),
        "Deletions companion T−40→T−20": evaluate_sleeve(pre, event_type="deletion"),
        "Additions F1c T→T+20 fade": evaluate_sleeve(rev, event_type="addition"),
        "Deletions F1c T→T+20 fade": evaluate_sleeve(rev, event_type="deletion"),
    }
    for label, result in companions.items():
        _print_mde_then_result(label, result)

    memo = render_verdict_memo(add_auth, del_auth, companions)
    F1_MEMO_PATH.write_text(memo, encoding="utf-8")
    F1_LOG_PATH.write_text(charter + "\n--- peek ---\n" + memo, encoding="utf-8")
    print(f"wrote {F1_MEMO_PATH}")


def main() -> None:
    run_f1()


if __name__ == "__main__":
    main()
