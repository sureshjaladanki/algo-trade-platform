"""F0 — reconstruct the event pool and write the counts memo."""

from __future__ import annotations

import polars as pl

from src.events.daily_panel import load_nifty_daily, load_or_build_daily_panel
from src.events.event_pool import (
    build_membership_events,
    count_events_by_year_family,
    f1_gate_support,
    families_with_membership,
    flag_tradable_universe,
    index_price_families_without_membership,
    write_event_pool,
)
from src.events.paths import F0_MEMO_PATH, GOLDEN_DIR


def render_f0_memo(
    events,
    counts,
    support: dict[str, str],
    price_only: list[str],
) -> str:
    n = events.height
    n_add = events.filter(pl.col("event_type") == "addition").height
    n_del = events.filter(pl.col("event_type") == "deletion").height
    n_tradable = int(events["in_tradable_universe"].sum())
    count_lines = [
        f"| {r['year']} | {r['family']} | {r['event_type']} | {r['n']} |"
        for r in counts.iter_rows(named=True)
    ]
    price_list = ", ".join(price_only) if price_only else "(none)"
    return "\n".join(
        [
            "# F0 — Event pool",
            "",
            "**Gate:** F0 (execution plan). **Date:** 2026-08-19.",
            "",
            "## Reconstruction",
            "",
            "Events are the first-session difference in point-in-time Nifty-50",
            "membership. The membership walk is the in-repo replacement ledger.",
            "Announcement dates are not on that ledger and were not purchased.",
            "",
            f"**Families with PIT membership:** {', '.join(families_with_membership())}",
            f"**Index price series without membership:** {price_list}",
            "",
            "## Counts",
            "",
            f"Total events **{n}** (additions {n_add}, deletions {n_del}).",
            f"In the GOLDEN tradable universe on the effective session: **{n_tradable}**.",
            "",
            "| year | family | event_type | n |",
            "|---|---|---|---|",
            *count_lines,
            "",
            "## Implied F1 sample",
            "",
            f"F1 can use at most the {n_tradable} tradable events, split by",
            "addition vs deletion, and only those whose pre-registered window",
            "has both endpoint closes (no interpolation).",
            "",
            "## Which sub-gates the dates support",
            "",
            f"- **F1a** — {support['F1a']}",
            f"- **F1b** — {support['F1b']}",
            f"- **F1c** — {support['F1c']}",
            f"- **F1-effective** — {support['F1_effective']}",
            "",
            "## Stop check",
            "",
            "The pool was built from in-repo membership. Book F does not stop",
            "at F0. Power vs the 600 bps prior is printed in the F1 charter",
            "before the peek. Announcement dates remain unrecoverable here;",
            "F1a is not run.",
            "",
        ]
    )


def run_f0(*, rebuild_panel: bool = False):
    panel = load_or_build_daily_panel(rebuild=rebuild_panel)
    nifty = load_nifty_daily(GOLDEN_DIR)
    session_dates = nifty["date"].to_list()
    events = flag_tradable_universe(
        build_membership_events(session_dates),
        panel,
    )
    counts = count_events_by_year_family(events)
    support = f1_gate_support(events)
    write_event_pool(events)
    memo = render_f0_memo(
        events,
        counts,
        support,
        index_price_families_without_membership(),
    )
    F0_MEMO_PATH.write_text(memo, encoding="utf-8")
    return events, counts, support


def main() -> None:
    events, counts, support = run_f0()
    print(counts)
    for key, line in support.items():
        print(f"{key}: {line}")
    print(f"wrote {F0_MEMO_PATH}")
    print(f"events={events.height}")


if __name__ == "__main__":
    main()
