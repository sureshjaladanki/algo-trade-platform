"""M9 V2 stub — gross held ATM-straddle PnL on a forward sample (2021–2022).

Does **not** remount M4–M8. Reprints Stage B K1 and V1 on rolling folds, then
a cost-free EOD settle stub (T → next session, same strike/expiry).

Pre-registered (locked in this harness before the run):

* Folds: R2021, R2022 (skip 2020 as an authority test year).
* Long vol when first-bar ``range_q50 > range_imp_atm``.
* Entry: session-T ATM CE+PE settle; exit: same contract next marks session.
* PASS if session-block CI LB of mean PnL (bps of spot) > 0; FAIL if UB < 0;
  else INCONCLUSIVE. MDE published. Clock-mismatched vs remaining-session.

    poetry run python -m src.experiments.eval_horizon_m9_v2_stub --folds R2021 R2022
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.experiments.eval_horizon_m9_v1 import _run_fold
from src.horizon.fresh.gates import k1_range_spearman
from src.horizon.m9.implied_range import DEFAULT_RANGE_KAPPA
from src.horizon.m9.iv_store import DEFAULT_IV_PATH, IvStoreMissingError, load_atm_iv_daily
from src.horizon.m9.v2_straddle import (
    held_straddle_pnl,
    morning_long_vol_sessions,
    v2_session_block_gate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MARKS = REPO_ROOT / "data" / "GOLDEN_IV" / "option_marks_daily.parquet"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--iv-path", type=Path, default=REPO_ROOT / DEFAULT_IV_PATH)
    parser.add_argument("--marks-path", type=Path, default=DEFAULT_MARKS)
    parser.add_argument("--folds", nargs="+", default=["R2021", "R2022"])
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--kappa", type=float, default=DEFAULT_RANGE_KAPPA)
    args = parser.parse_args()

    print(
        "M9 forward-sample V2 stub (EOD settle, held contract). "
        "Not M0-M8 remount. Charter Track A V2."
    )
    print(
        "Locked: folds R2021/R2022; long vol if morning q50>implied; "
        "PnL = (T+1 settle - T settle)/spot; CI LB>0 PASS."
    )
    try:
        iv = load_atm_iv_daily(args.iv_path)
    except IvStoreMissingError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    if "straddle" not in iv.columns:
        print("ERROR: IV store has no straddle marks; rebuild with extract_atm_iv_rows premiums")
        sys.exit(1)
    if not args.marks_path.exists():
        print(f"ERROR: marks store missing at {args.marks_path}")
        sys.exit(1)
    marks = pl.read_parquet(args.marks_path)
    print(
        f"   iv_rows={iv.height} iv_max={iv['date_only'].max()} "
        f"marks_rows={marks.height} marks_max={marks['date_only'].max()}"
    )

    v1_flags: list[bool] = []
    v2_flags: list[bool] = []
    for fold in args.folds:
        passed, te = _run_fold(
            fold,
            args.data_dir,
            args.config,
            iv,
            max_symbols=args.max_symbols,
            kappa=args.kappa,
        )
        v1_flags.append(passed)
        k1 = k1_range_spearman(
            te["range_q50"].to_numpy(),
            te["remaining_range"].to_numpy(),
            fold=fold,
        )
        print(
            f"   K1 reprint {k1.passed} rho={k1.value:.3f} "
            f"threshold={k1.threshold:.2f} ({k1.note})"
        )
        selected = morning_long_vol_sessions(te)
        print(f"   V2 selected sessions={selected.height}")
        pnl = held_straddle_pnl(selected, iv, marks)
        gate = v2_session_block_gate(pnl, fold=fold)
        print(
            f"   V2 {gate.verdict} n={gate.n} sessions={gate.n_sessions} "
            f"mean={gate.mean_bps:+.2f} bps CI[{gate.ci_lo:+.2f},{gate.ci_hi:+.2f}] "
            f"MDE={gate.mde:.2f} ({gate.note})"
        )
        v2_flags.append(gate.verdict == "PASS")

    dual_v1 = all(v1_flags) and len(v1_flags) >= 2
    dual_v2 = all(v2_flags) and len(v2_flags) >= 2
    print(f"\nV1 dual-fold={'PASS' if dual_v1 else 'FAIL'}")
    print(f"V2 dual-fold={'PASS' if dual_v2 else 'FAIL'} (stub; INCONCLUSIVE is not PASS)")
    if dual_v1 and dual_v2:
        sys.exit(0)
    sys.exit(2)


if __name__ == "__main__":
    main()
