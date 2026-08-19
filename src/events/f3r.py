"""F3-RESIDUAL / C2 — predicted Next 50 top-3, cut-off → session after PR.

Charter is already written (`docs/next/f3-residual-charter.md`). This module
does not rewrite it. One peek, terminal for Book F capital.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl

from src.events.announcements import ANNOUNCEMENTS
from src.events.constants import (
    BOOT_SEED,
    F3R_CONTROL_RANK_HI,
    F3R_CONTROL_RANK_LO,
    F3R_END_YEAR,
    F3R_ERA_SPLIT_YEAR,
    F3R_GO_BPS,
    F3R_K,
    F3R_MIN_COVERAGE,
    F3R_PRIOR_SIGMA_BPS,
    F3R_START_YEAR,
    F3R_STOP_BPS,
    MIN_FOLD_EVENTS,
    N_BOOT,
)
from src.events.daily_panel import load_nifty_daily, load_or_build_daily_panel
from src.events.mcwb import load_or_build_mcwb_panel
from src.events.paths import F3R_LOG_PATH, F3R_MEMO_PATH, GOLDEN_DIR
from src.events.ranking import average_free_float, cutoff_for_announcement, rank_next50
from src.events.residual import (
    first_session_on_or_after,
    first_session_strictly_after,
    residual_bps,
)
from src.events.stats import (
    clip_disaster,
    fold_sign_pass,
    mde_bps,
    session_block_mean_ci,
)

# Periodic-review PRs for cut-offs with no semi-annual row in ANNOUNCEMENTS.
# Jan-2020 announced a Nifty 50 swap that F1b later labelled ad-hoc.
_EXTRA_CYCLE_PRS: dict[dt.date, tuple[dt.date, str]] = {
    dt.date(2016, 7, 31): (
        dt.date(2016, 8, 12),
        "IISL dashboard Sep-2016 citing ind_prs12082016.pdf",
    ),
    dt.date(2020, 1, 31): (
        dt.date(2020, 2, 18),
        "TOI/ET 2020-02-18 periodic review (YESBANK/SHREECEM later deferred)",
    ),
    dt.date(2021, 7, 31): (
        dt.date(2021, 8, 23),
        "ZeeBiz/ET: NSE Indices PR 2021-08-23 (Next 50 changes, Nifty 50 unchanged)",
    ),
    dt.date(2023, 1, 31): (
        dt.date(2023, 2, 17),
        "ET originally 2023-02-17; Equitypandit 2023-02-17 (Nifty 50 unchanged)",
    ),
    dt.date(2023, 7, 31): (
        dt.date(2023, 8, 17),
        "NSE/FAOP/58020 cites NSE Indices PR dated 2023-08-17",
    ),
}


def semi_annual_cutoffs(
    start_year: int = F3R_START_YEAR,
    end_year: int = F3R_END_YEAR,
) -> list[dt.date]:
    return [
        dt.date(year, month, 31)
        for year in range(start_year, end_year + 1)
        for month in (1, 7)
    ]


def entry_month_for_cutoff(cutoff: dt.date) -> int:
    if cutoff.month == 1 and cutoff.day == 31:
        return 2
    if cutoff.month == 7 and cutoff.day == 31:
        return 8
    raise ValueError(f"cut-off must be 31 Jan or 31 Jul, got {cutoff}")


def _semi_annual_pr_by_cutoff() -> dict[dt.date, dt.date]:
    found: dict[dt.date, dt.date] = {}
    for row in ANNOUNCEMENTS:
        if row.kind != "semi_annual":
            continue
        cutoff = cutoff_for_announcement(row.announcement_date)
        prev = found.get(cutoff)
        if prev is not None and prev != row.announcement_date:
            raise ValueError(
                f"conflicting PRs for {cutoff}: {prev} vs {row.announcement_date}"
            )
        found[cutoff] = row.announcement_date
    return found


def announcement_for_cutoff(cutoff: dt.date) -> tuple[dt.date, str]:
    mapped = _semi_annual_pr_by_cutoff().get(cutoff)
    if mapped is not None:
        return mapped, "ANNOUNCEMENTS semi_annual"
    extra = _EXTRA_CYCLE_PRS.get(cutoff)
    if extra is None:
        raise ValueError(f"no periodic-review PR for cut-off {cutoff}")
    return extra


def n_semi_annual_additions(cutoff: dt.date) -> int:
    return sum(
        1
        for row in ANNOUNCEMENTS
        if row.kind == "semi_annual"
        and cutoff_for_announcement(row.announcement_date) == cutoff
    )


def capital_verdict(
    point_bps: float,
    ci_low_bps: float,
    early_mean_bps: float,
    late_mean_bps: float,
) -> str:
    """GO / STOP / INCONCLUSIVE. INCONCLUSIVE resolves to STOP for capital."""
    eras_ok = early_mean_bps > 0 and late_mean_bps > 0
    if point_bps >= F3R_GO_BPS and ci_low_bps > 0 and eras_ok:
        return "GO"
    if point_bps < F3R_STOP_BPS:
        return "STOP"
    return "INCONCLUSIVE"


def _close_map(panel: pl.DataFrame) -> dict[tuple[str, dt.date], float]:
    return {
        (row["symbol"], row["date"]): float(row["close"])
        for row in panel.iter_rows(named=True)
    }


def _nifty_map(nifty_daily: pl.DataFrame) -> dict[dt.date, float]:
    return {
        row["date"]: float(row["close"]) for row in nifty_daily.iter_rows(named=True)
    }


def equal_weight_residual(
    closes: dict[tuple[str, dt.date], float],
    nifty: dict[dt.date, float],
    symbols: list[str],
    start: dt.date,
    end: dt.date,
) -> tuple[float, int, int]:
    """Mean residual; a slot with no bars contributes 0 bps (cash)."""
    if not symbols:
        raise ValueError("empty basket")
    start_n = nifty[start]
    end_n = nifty[end]
    total = 0.0
    covered = 0
    for symbol in symbols:
        start_px = closes.get((symbol, start))
        end_px = closes.get((symbol, end))
        if start_px is None or end_px is None:
            continue
        total += residual_bps(start_px, end_px, start_n, end_n)
        covered += 1
    return total / len(symbols), covered, len(symbols)


def _names_in_rank_band(ranked: pl.DataFrame, lo: int, hi: int) -> list[str]:
    band = ranked.filter((pl.col("rank") >= lo) & (pl.col("rank") <= hi))
    return band["symbol"].to_list()


def measure_cycles(
    panel: pl.DataFrame,
    mcwb: pl.DataFrame,
    nifty_daily: pl.DataFrame,
) -> pl.DataFrame:
    calendar = nifty_daily["date"].to_list()
    closes = _close_map(panel)
    nifty = _nifty_map(nifty_daily)
    rows: list[dict] = []
    for cutoff in semi_annual_cutoffs():
        announcement, source = announcement_for_cutoff(cutoff)
        entry = first_session_on_or_after(
            calendar, dt.date(cutoff.year, entry_month_for_cutoff(cutoff), 1)
        )
        exit_day = first_session_strictly_after(calendar, announcement)
        if entry is None or exit_day is None:
            raise RuntimeError(f"{cutoff}: calendar missing entry or exit")
        if exit_day <= entry:
            raise RuntimeError(f"{cutoff}: exit {exit_day} is not after entry {entry}")
        if entry not in nifty or exit_day not in nifty:
            raise RuntimeError(f"{cutoff}: Nifty close missing on {entry} or {exit_day}")
        ranked = rank_next50(average_free_float(mcwb, cutoff))
        if ranked.height < F3R_CONTROL_RANK_LO:
            raise RuntimeError(f"{cutoff}: Next 50 rank depth {ranked.height}")
        treat_names = _names_in_rank_band(ranked, 1, F3R_K)
        control_names = _names_in_rank_band(
            ranked, F3R_CONTROL_RANK_LO, F3R_CONTROL_RANK_HI
        )
        if len(treat_names) != F3R_K:
            raise RuntimeError(f"{cutoff}: expected {F3R_K} predicted names")
        treat_bps, treat_n, treat_slots = equal_weight_residual(
            closes, nifty, treat_names, entry, exit_day
        )
        control_bps, control_n, control_slots = equal_weight_residual(
            closes, nifty, control_names, entry, exit_day
        )
        rows.append(
            {
                "cutoff": cutoff,
                "announcement_date": announcement,
                "announcement_source": source,
                "entry_date": entry,
                "exit_date": exit_day,
                "year": cutoff.year,
                "era": "early" if cutoff.year < F3R_ERA_SPLIT_YEAR else "late",
                "n_additions": n_semi_annual_additions(cutoff),
                "treat_bps": treat_bps,
                "control_bps": control_bps,
                "authority_bps": treat_bps - control_bps,
                "treat_covered": treat_n,
                "treat_slots": treat_slots,
                "control_covered": control_n,
                "control_slots": control_slots,
                "treat_coverage": treat_n / treat_slots,
                "control_coverage": control_n / control_slots,
                "top3": ",".join(treat_names),
            }
        )
    return pl.DataFrame(rows)


def evaluate_series(measured: pl.DataFrame, column: str) -> dict:
    n = measured.height
    prior_mde = mde_bps(F3R_PRIOR_SIGMA_BPS, n) if n else float("inf")
    if n == 0:
        return {
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
            "mean_treat_coverage": None,
            "mean_control_coverage": None,
            "verdict": "INCONCLUSIVE",
            "capital": "STOP",
        }
    raw = measured[column].to_numpy()
    clipped = clip_disaster(raw)
    n_clipped = int((clipped != raw).sum())
    sample_sigma = float(np.std(clipped, ddof=1)) if n > 1 else float(np.std(clipped))
    sample_mde = mde_bps(sample_sigma, n)
    session_ids = np.array(
        [d.toordinal() for d in measured["exit_date"].to_list()],
        dtype=np.int64,
    )
    rng = np.random.default_rng(BOOT_SEED)
    interval = session_block_mean_ci(clipped, session_ids, N_BOOT, rng)
    clipped_df = measured.with_columns(trade=pl.Series(clipped))
    fold_tbl = clipped_df.group_by("year").agg(mean=pl.col("trade").mean(), n=pl.len())
    fold_means = {str(r["year"]): float(r["mean"]) for r in fold_tbl.iter_rows(named=True)}
    fold_counts = {str(r["year"]): int(r["n"]) for r in fold_tbl.iter_rows(named=True)}
    sign_ok, n_pos, n_folds = fold_sign_pass(
        fold_means, fold_counts, min_events=MIN_FOLD_EVENTS
    )
    early = clipped_df.filter(pl.col("era") == "early")
    late = clipped_df.filter(pl.col("era") == "late")
    early_bps = float(early["trade"].mean()) if early.height else float("nan")
    late_bps = float(late["trade"].mean()) if late.height else float("nan")
    verdict = capital_verdict(interval.point, interval.ci_low, early_bps, late_bps)
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
        "mean_treat_coverage": float(measured["treat_coverage"].mean()),
        "mean_control_coverage": float(measured["control_coverage"].mean()),
        "verdict": verdict,
        "capital": "GO" if verdict == "GO" else "STOP",
    }


def _pct(value: float) -> str:
    return f"{100.0 * value:.1f}%"


def _bps(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f}"


def render_block(title: str, result: dict) -> list[str]:
    if result["n"] == 0:
        return [f"### {title}", "", "n=0. INCONCLUSIVE → STOP for capital.", ""]
    folds = result.get("fold_means", {})
    fold_txt = ", ".join(f"{k}: {v:.1f}" for k, v in sorted(folds.items()))
    return [
        f"### {title}",
        "",
        f"- n={result['n']} sessions={result['n_sessions']} clipped={result['n_clipped']}",
        f"- MDE (prior σ {F3R_PRIOR_SIGMA_BPS:.0f}, printed first): **{result['prior_mde_bps']:.1f} bps**",
        f"- economic hurdle: **{F3R_STOP_BPS:.0f} bps**; GO bar: **{F3R_GO_BPS:.0f} bps**",
        f"- point {result['point_bps']:.1f} bps, CI [{result['ci_low_bps']:.1f}, {result['ci_high_bps']:.1f}]",
        f"- sample σ {result['sample_sigma_bps']:.1f} bps, sample MDE {result['sample_mde_bps']:.1f} bps",
        (
            f"- era 2015–19 n={result['early_n']} {_bps(result['early_bps'])} bps; "
            f"2020–25 n={result['late_n']} {_bps(result['late_bps'])} bps"
        ),
        f"- fold sign {result['n_pos_folds']}/{result['n_folds']} ({fold_txt})",
        (
            f"- mean coverage treat {_pct(result['mean_treat_coverage'])} "
            f"control {_pct(result['mean_control_coverage'])}"
        ),
        f"- **verdict: {result['verdict']}** (capital {result['capital']})",
        "",
    ]


def _capital_sentence(verdict: str) -> str:
    if verdict == "GO":
        return (
            "GO. Predicted top-3 clears 450 bps, CI lower bound > 0, both eras "
            "positive. Opens F5 tradability and a domestic replication. Does not "
            "release live capital. F2-NET re-opens on this window only."
        )
    if verdict == "STOP":
        return (
            "STOP. Point is below the 300 bps economic hurdle. Book F capital "
            "stops. Ranking (F3-SKILL) is retained as a research asset. Do not "
            "fit a model, re-window, or open F2-NET. G remains the research primary."
        )
    return (
        "INCONCLUSIVE. Resolves to STOP for Book F capital. No further Nifty 50 "
        "events exist to repair power. Do not treat this as a pass. G remains "
        "the research primary."
    )


def render_memo(
    auth: dict,
    nifty: dict,
    sensitivity: dict,
    measured: pl.DataFrame,
) -> str:
    n_zero = measured.filter(pl.col("n_additions") == 0).height
    cycle_lines = [
        (
            f"- {r['cutoff']}: entry {r['entry_date']} → exit {r['exit_date']} "
            f"adds={r['n_additions']} treat={r['treat_bps']:.1f} "
            f"ctrl={r['control_bps']:.1f} auth={r['authority_bps']:.1f} "
            f"cover={r['treat_covered']}/{r['treat_slots']} top3={r['top3']}"
        )
        for r in measured.iter_rows(named=True)
    ]
    return "\n".join(
        [
            "# F3-RESIDUAL — predicted Next 50 basket",
            "",
            "**Gate:** F3-RESIDUAL / C2, cost-free. **Date:** 2026-08-19.",
            "Charter: `docs/next/f3-residual-charter.md`. Written before this peek.",
            "Not a re-window of F1 / F1a / T−40 on actual additions.",
            "",
            (
                "Rank uses the cut-off month MCWB file (roll-forward shares/float "
                "fields are not in MCWB). Lag recorded."
            ),
            "",
            (
                f"Cycles n={measured.height} of which zero-addition={n_zero}. "
                f"k={F3R_K} equal weight vs ranks "
                f"{F3R_CONTROL_RANK_LO}–{F3R_CONTROL_RANK_HI}."
            ),
            "",
            "## Authority (top-3 minus ranks 21–50)",
            "",
            *render_block("Ex-ante basket vs Next 50 ranks 21–50", auth),
            "## Companion (not authority)",
            "",
            *render_block("Top-3 vs Nifty", nifty),
            *render_block(
                f"Sensitivity: drop treat coverage < {_pct(F3R_MIN_COVERAGE)}",
                sensitivity,
            ),
            "## Cycles",
            "",
            *cycle_lines,
            "",
            "## Book F capital",
            "",
            _capital_sentence(auth["verdict"]),
            "",
        ]
    )


def _print_mde(label: str, result: dict) -> None:
    print(f"{label} n={result['n']} MDE={result['prior_mde_bps']:.1f} bps")
    if result["n"] == 0:
        print(f"{label} verdict=INCONCLUSIVE capital=STOP")
        return
    print(
        f"{label} point={result['point_bps']:.1f} "
        f"CI=[{result['ci_low_bps']:.1f}, {result['ci_high_bps']:.1f}] "
        f"verdict={result['verdict']} capital={result['capital']}"
    )


def run_f3r() -> None:
    panel = load_or_build_daily_panel()
    nifty_daily = load_nifty_daily(GOLDEN_DIR)
    mcwb = load_or_build_mcwb_panel()
    n = len(semi_annual_cutoffs())
    prior_mde = mde_bps(F3R_PRIOR_SIGMA_BPS, n)
    print(
        f"F3-RESIDUAL n={n} prior sigma={F3R_PRIOR_SIGMA_BPS:.0f} "
        f"MDE={prior_mde:.1f} bps hurdle={F3R_STOP_BPS:.0f} GO={F3R_GO_BPS:.0f}"
    )
    print("--- peek ---")
    measured = measure_cycles(panel, mcwb, nifty_daily)
    auth = evaluate_series(measured, "authority_bps")
    nifty = evaluate_series(measured, "treat_bps")
    covered = measured.filter(pl.col("treat_coverage") >= F3R_MIN_COVERAGE)
    sensitivity = evaluate_series(covered, "authority_bps")
    _print_mde("authority vs ranks 21-50", auth)
    _print_mde("companion vs Nifty", nifty)
    _print_mde("sensitivity coverage>=2/3", sensitivity)
    memo = render_memo(auth, nifty, sensitivity, measured)
    F3R_MEMO_PATH.write_text(memo, encoding="utf-8")
    F3R_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    F3R_LOG_PATH.write_text(memo, encoding="utf-8")
    print(memo)
    print(f"wrote {F3R_MEMO_PATH}")


def main() -> None:
    run_f3r()


if __name__ == "__main__":
    main()
