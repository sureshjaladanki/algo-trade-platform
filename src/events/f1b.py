"""F1b — pre-announcement ranking skill. Not a residual peek and not F2."""

from __future__ import annotations

import polars as pl

from src.events.announcements import ANNOUNCEMENTS
from src.events.constants import (
    IMPACT_COST_MAX_PCT,
    INCLUSION_FF_BUFFER,
    MCWB_MIN_MONTHS,
    N_BOOT,
)
from src.events.mcwb import load_or_build_mcwb_panel
from src.events.paths import F1B_CHARTER_PATH, F1B_LOG_PATH, F1B_MEMO_PATH
from src.events.ranking import (
    average_free_float,
    cutoff_for_announcement,
    predict_additions,
    rank_next50,
)
from src.events.stats import mde_bps

_NEXT50_SIZE = 50
_Z = 1.959963984540


def _semi_annual_additions() -> list:
    return [a for a in ANNOUNCEMENTS if a.kind == "semi_annual"]


def _cycle_size(rows: list) -> dict:
    counts: dict = {}
    for row in rows:
        key = cutoff_for_announcement(row.announcement_date)
        counts[key] = counts.get(key, 0) + 1
    return counts


def naive_hit_probability(rows: list | None = None) -> float:
    """P(actual addition ranks in the top-k Next 50 names) under random rank."""
    adds = rows if rows is not None else _semi_annual_additions()
    sizes = _cycle_size(adds)
    return sum(sizes[cutoff_for_announcement(a.announcement_date)] for a in adds) / (
        _NEXT50_SIZE * len(adds)
    )


def mde_hit_rate(p0: float, n: int) -> float:
    return mde_bps((p0 * (1.0 - p0)) ** 0.5 * 10_000.0, n) / 10_000.0


def proportion_interval(hits: int, n: int) -> tuple[float, float, float]:
    p = hits / n
    se = (p * (1.0 - p) / n) ** 0.5
    return p, max(0.0, p - _Z * se), min(1.0, p + _Z * se)


def ranking_verdict(
    point: float,
    ci_low: float,
    ci_high: float,
    mde: float,
    naive: float,
) -> str:
    if mde >= abs(point - naive):
        return "INCONCLUSIVE"
    if ci_low > naive:
        return "PASS"
    if ci_high < naive:
        return "FAIL"
    return "INCONCLUSIVE"


def render_f1b_charter(n_add: int, naive: float) -> str:
    mde = mde_hit_rate(naive, n_add) if n_add else float("inf")
    return "\n".join(
        [
            "# F1b charter — pre-announcement ranking skill",
            "",
            "Written **before** the ranking peek. This is execution-plan F3 /",
            "blueprint F1b **skill**, not a residual trade and not F2.",
            "HuggingFace Nifty-50 weight files are the wrong universe.",
            "",
            "| Lock | Choice |",
            "|---|---|",
            "| Source | NSE Indices monthly MCWB zips (Nifty 50 and Next 50) |",
            "| Universe | Next 50 members in the cut-off month |",
            "| Score | 6-month average free-float mcap ending 31 Jan / 31 Jul |",
            f"| Months required | **{MCWB_MIN_MONTHS}** of the six (skip the name otherwise) |",
            f"| Liquidity screen | mean monthly avg. impact cost ≤ **{IMPACT_COST_MAX_PCT:.2f}%** |",
            "| F&O screen | not applied this pass (no PIT F&O field in MCWB) |",
            f"| 1.5× rule | Next 50 name ≥ **{INCLUSION_FF_BUFFER}** × smallest Nifty 50 6-month FF mcap |",
            "| Labels | F0 semi-annual **additions** only. Ad-hoc swaps are out |",
            "| Cut-off map | PR in Jan–Apr → 31 Jan; PR in Jul–Sep → 31 Jul |",
            "| Authority statistic | Top-k hit rate. k = number of semi-annual additions that cycle |",
            "| Hit | Actual addition's Next 50 rank ≤ k |",
            f"| Naive | Random Next 50 rank; pooled **{naive:.4f}** (k/50 per addition) |",
            "| Required | CI lower bound of hit rate > naive |",
            f"| n | **{n_add}** semi-annual additions |",
            f"| MDE | **{mde:.4f}** hit-rate points (80% power, two-sided, vs naive) |",
            "| 1.5× companion | recall and precision of the published buffer; not the gate |",
            "| Universe miss | addition absent from Next 50 at cut-off; dropped from hit-rate n |",
            "| Hold-out print | 2015–2019 vs 2020–2025; rule is not fit on either slice |",
            "| Residual trade | not this peek |",
            f"| Bootstrap | unused (binomial CI). Residual n_boot={N_BOOT} does not apply |",
            "",
            "Do not fit a model. Do not re-window F1a. Do not open F2.",
            "",
        ]
    )


def score_additions(panel: pl.DataFrame) -> tuple[list[dict], dict]:
    adds = _semi_annual_additions()
    sizes = _cycle_size(adds)
    predicted: dict = {}
    ranked_by_cutoff: dict = {}
    for cutoff in sorted(sizes):
        averaged = average_free_float(panel, cutoff)
        ranked_by_cutoff[cutoff] = rank_next50(averaged)
        predicted[cutoff] = set(predict_additions(averaged)["symbol"].to_list())
    rows: list[dict] = []
    for add in adds:
        cutoff = cutoff_for_announcement(add.announcement_date)
        ranked = ranked_by_cutoff[cutoff]
        match = ranked.filter(pl.col("symbol") == add.included)
        k = sizes[cutoff]
        if match.height == 0:
            rows.append(
                {
                    "symbol": add.included,
                    "announcement_date": add.announcement_date,
                    "cutoff": cutoff,
                    "k": k,
                    "rank": None,
                    "hit_topk": False,
                    "in_buffer": False,
                    "universe_miss": True,
                    "naive_p": k / _NEXT50_SIZE,
                }
            )
            continue
        rank = int(match["rank"][0])
        rows.append(
            {
                "symbol": add.included,
                "announcement_date": add.announcement_date,
                "cutoff": cutoff,
                "k": k,
                "rank": rank,
                "hit_topk": rank <= k,
                "in_buffer": add.included in predicted[cutoff],
                "universe_miss": False,
                "naive_p": k / _NEXT50_SIZE,
            }
        )
    return rows, predicted


def summarise(rows: list[dict], predicted: dict | None = None) -> dict:
    scored = [r for r in rows if not r["universe_miss"]]
    n = len(scored)
    n_miss = sum(1 for r in rows if r["universe_miss"])
    miss_names = ", ".join(
        f"{r['symbol']} ({r['cutoff']})" for r in rows if r["universe_miss"]
    )
    if n == 0:
        return {
            "n": 0,
            "n_universe_miss": n_miss,
            "miss_names": miss_names,
            "hits": 0,
            "hit_rate": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "naive": 0.0,
            "mde": float("inf"),
            "verdict": "INCONCLUSIVE",
            "mean_rank": None,
            "buffer_recall": 0.0,
            "buffer_precision": None,
        }
    hits = sum(1 for r in scored if r["hit_topk"])
    naive = sum(r["naive_p"] for r in scored) / n
    point, low, high = proportion_interval(hits, n)
    mde = mde_hit_rate(naive, n)
    buffer_hits = sum(1 for r in scored if r["in_buffer"])
    precision = None
    if predicted is not None:
        actual_by_cutoff: dict[object, set[str]] = {}
        row_cutoffs = {r["cutoff"] for r in rows}
        for row in scored:
            actual_by_cutoff.setdefault(row["cutoff"], set()).add(row["symbol"])
        pred_n = 0
        pred_hit = 0
        for cutoff, names in predicted.items():
            if cutoff not in row_cutoffs:
                continue
            pred_n += len(names)
            pred_hit += len(names & actual_by_cutoff.get(cutoff, set()))
        precision = (pred_hit / pred_n) if pred_n else None
    return {
        "n": n,
        "n_universe_miss": n_miss,
        "miss_names": miss_names,
        "hits": hits,
        "hit_rate": point,
        "ci_low": low,
        "ci_high": high,
        "naive": naive,
        "mde": mde,
        "verdict": ranking_verdict(point, low, high, mde, naive),
        "mean_rank": sum(r["rank"] for r in scored) / n,
        "buffer_recall": buffer_hits / n,
        "buffer_precision": precision,
    }


def _slice(rows: list[dict], start: int, end: int) -> list[dict]:
    return [r for r in rows if start <= r["announcement_date"].year <= end]


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{100.0 * value:.1f}%"


def render_f1b_memo(full: dict, early: dict, late: dict) -> str:
    mean_rank = (
        f"{full['mean_rank']:.2f}" if full["mean_rank"] is not None else "n/a"
    )
    return "\n".join(
        [
            "# F1b — Pre-announcement ranking",
            "",
            "**Gate:** F1b / execution-plan F3 ranking skill. **Date:** 2026-08-19.",
            "Charter: `docs/next/f1b-charter.md`. Not a residual peek.",
            "",
            "## Authority (top-k hit rate)",
            "",
            f"- n={full['n']} (universe misses={full['n_universe_miss']})",
            f"- hit rate={_pct(full['hit_rate'])} CI=[{_pct(full['ci_low'])}, {_pct(full['ci_high'])}]",
            f"- naive={_pct(full['naive'])} MDE={_pct(full['mde'])}",
            f"- mean Next 50 rank={mean_rank}",
            f"- verdict=**{full['verdict']}**",
            f"- universe misses: {full.get('miss_names', 'n/a')}",
            "",
            "IOC and IBULHSGFIN sit in the Nifty 50 MCWB file at the Jan-2017",
            "cut-off, not Next 50. GRASIM, NESTLEIND, and MAXHEALTH are absent",
            "from both files at their cut-offs (not a ticker-alias miss).",
            "",
            "## 1.5× companion (not the gate)",
            "",
            f"- recall={_pct(full['buffer_recall'])}",
            f"- precision={_pct(full['buffer_precision'])}",
            "",
            "## Hold-out print (same rule, not a re-fit)",
            "",
            (
                f"- 2015–2019 n={early['n']} hit={_pct(early['hit_rate'])} "
                f"naive={_pct(early['naive'])} verdict={early['verdict']}"
            ),
            (
                f"- 2020–2025 n={late['n']} hit={_pct(late['hit_rate'])} "
                f"naive={_pct(late['naive'])} verdict={late['verdict']}"
            ),
            "",
            "## Book F",
            "",
            _f1b_sentence(full["verdict"]),
            "",
        ]
    )


def _f1b_sentence(verdict: str) -> str:
    if verdict == "FAIL":
        return (
            "Ranking does not beat a naive Next 50 draw. No pre-announcement "
            "product. Keep the public F1a calendar only. Do not fit a model."
        )
    if verdict == "PASS":
        return (
            "Out-of-sample top-k rank beats naive. That is F3 skill, not F2. "
            "Do not open a pre-announcement residual until F1a/F2 is passable."
        )
    return (
        "INCONCLUSIVE. Repair is more history or a PIT F&O field, not a fitted "
        "model and not a residual re-window."
    )


def run_f1b() -> None:
    adds = _semi_annual_additions()
    naive = naive_hit_probability(adds)
    charter = render_f1b_charter(len(adds), naive)
    F1B_CHARTER_PATH.write_text(charter, encoding="utf-8")
    print(charter)
    print("--- F1b ranking peek ---")
    F1B_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    panel = load_or_build_mcwb_panel()
    rows, predicted = score_additions(panel)
    full = summarise(rows, predicted)
    early_rows = _slice(rows, 2015, 2019)
    late_rows = _slice(rows, 2020, 2025)
    early_pred = {
        c: names
        for c, names in predicted.items()
        if any(r["cutoff"] == c for r in early_rows)
    }
    late_pred = {
        c: names
        for c, names in predicted.items()
        if any(r["cutoff"] == c for r in late_rows)
    }
    early = summarise(early_rows, early_pred)
    late = summarise(late_rows, late_pred)
    memo = render_f1b_memo(full, early, late)
    F1B_MEMO_PATH.write_text(memo, encoding="utf-8")
    F1B_LOG_PATH.write_text(charter + "\n---\n" + memo, encoding="utf-8")
    print(memo)
    print(f"wrote {F1B_CHARTER_PATH}")
    print(f"wrote {F1B_MEMO_PATH}")


def main() -> None:
    run_f1b()


if __name__ == "__main__":
    main()
