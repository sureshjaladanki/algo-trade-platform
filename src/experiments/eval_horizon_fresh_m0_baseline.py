"""M0 baseline reprint — EV-net Step 0 summary without editing production labels.

Thin wrapper around the archived Step 0 harness (audit-only). Prefer running
``analyze_horizon_ev_net_step0.py`` directly for the full ledger; this entry
documents the M0 exit criterion path.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
STEP0 = REPO_ROOT / "src" / "experiments" / "analyze_horizon_ev_net_step0.py"


def main() -> None:
    print(
        "M0 baseline: reprinting EV-net Step 0 via audit-only harness "
        f"({STEP0.name}). Production labels untouched."
    )
    sys.argv = [str(STEP0), *sys.argv[1:]]
    runpy.run_path(str(STEP0), run_name="__main__")


if __name__ == "__main__":
    main()
