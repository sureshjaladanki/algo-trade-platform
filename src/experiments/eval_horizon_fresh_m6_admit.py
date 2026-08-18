"""M6 — Stage D absolute admit + book caps.

**Blocked.** Directional Nifty-100 MIS cash earned blueprint §14 capability FAIL
(M4R-b). This harness previously remounted the defective M5 Stage C (rule
one-hots, geometry-invariant sweep, per-fold ``k5_economics``). That is not a
K5 authority run.

Revisit M6 only against an M9 (or later) absolute-EV registry — not production
Top-K and not the M5 Long-continuation head.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

M6_BLOCKED_REASON = (
    "M6 BLOCKED: directional cash MIS is a blueprint §14 capability FAIL "
    "(M4R-b F1+F2). Do not remount M5 Stage C as a K5 authority run. "
    "Revisit Stage D against an M9 absolute-EV registry. "
    "See docs/next/horizon-fresh-architecture-implementation-plan.md §M6."
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument(
        "--force-scaffold",
        action="store_true",
        help="Ignored: M6 scaffold is withdrawn, not force-runnable.",
    )
    args = parser.parse_args()
    del args  # no authority path
    print(M6_BLOCKED_REASON)
    sys.exit(3)


if __name__ == "__main__":
    main()
