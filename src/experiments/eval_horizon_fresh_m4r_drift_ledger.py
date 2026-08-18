"""M4R — pre-registered drift-sign ledger (before any Stage C fit).

Barrier-free return from the event bar to MIS flatten, signed for the rule's
side. Dual-fold A/B is the decision ledger; no Stage C head is fit here.

Sleeve selection: fold-consistent sign + CI UB on the favorable side clears
c* (a credible route past friction). STOP if no family qualifies.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.horizon.fresh.candidate_events import (
    build_candidate_event_panel,
    transition_candidate_events,
)
from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.friction import BPS, C_STAR, C_STAR_BPS
from src.horizon.fresh.rule_registry import (
    RULE_REGISTRY,
    get_rule,
    sleeve_id,
)
from src.horizon.session import MIS_EXIT_BAR_END
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range
from src.utils.eval_common import session_block_mean_ci

REPO_ROOT = Path(__file__).resolve().parents[2]


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _attach_side_drift(events: pl.DataFrame, stock: pl.DataFrame) -> pl.DataFrame:
    mis_close = (
        stock.with_columns(
            date_only=pl.col("date").dt.date(), time_only=pl.col("date").dt.time()
        )
        .filter(pl.col("time_only") <= MIS_EXIT_BAR_END)
        .sort(["symbol", "date"])
        .group_by(["symbol", "date_only"])
        .agg(mis_close=pl.col("close").last())
    )
    out = events.join(mis_close, on=["symbol", "date_only"], how="left").with_columns(
        fwd_long=pl.col("mis_close") / pl.col("close") - 1.0,
    )
    return out.with_columns(
        side_drift=pl.when(pl.col("side") == "long")
        .then(pl.col("fwd_long"))
        .otherwise(-pl.col("fwd_long"))
    )


def _rule_drift(
    panel: pl.DataFrame, rule_id: str, *, n_boot: int, seed: int
) -> dict | None:
    sub = panel.filter(pl.col("rule_id") == rule_id)
    if sub.height < 80:
        return None
    d = sub["side_drift"].to_numpy().astype(float)
    s = sub["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    m = np.isfinite(d)
    if m.sum() < 80:
        return None
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(d[m], s[m], n_boot, rng)
    return {
        "rule_id": rule_id,
        "n": int(m.sum()),
        "n_sess": int(np.unique(s[m]).size),
        "point": point,
        "lo": lo,
        "hi": hi,
        "point_bps": point * BPS,
        "lo_bps": lo * BPS,
        "hi_bps": hi * BPS,
    }


def _fold_ledger(
    fold: str,
    stock: pl.DataFrame,
    *,
    n_boot: int,
    seed: int,
) -> dict[str, dict]:
    cfg = FOLDS[fold]
    _tr0, _tr1 = parse_period_range(cfg["train_period"])
    te0, te1 = parse_period_range(cfg["test_period"])
    # Drift ledger is report-only on the test window (no fit).
    te = filter_by_period(stock, te0, te1, datetime_col="date")
    events = transition_candidate_events(build_candidate_event_panel(te))
    panel = _attach_side_drift(events, te)
    print(f"\n=== M4R drift ledger fold {fold} test={cfg['test_period']} ===")
    print(f"   events after transition={panel.height}")
    out: dict[str, dict] = {}
    for rule in RULE_REGISTRY:
        row = _rule_drift(panel, rule.rule_id, n_boot=n_boot, seed=seed)
        if row is None:
            print(f"   {rule.rule_id:<28} thin")
            continue
        out[rule.rule_id] = row
        print(
            f"   {rule.rule_id:<28} n={row['n']:<5} sess={row['n_sess']:<4} "
            f"drift={row['point_bps']:+7.2f}bps "
            f"CI=[{row['lo_bps']:+.1f},{row['hi_bps']:+.1f}] "
            f"[{rule.family}/{rule.side}]"
        )
    return out


def _select_sleeve(ledgers: dict[str, dict[str, dict]]) -> tuple[str | None, str]:
    """
    Pick one sleeve: fold-consistent sign on A+B and CI UB > c* on ≥1 fold
    (credible route past friction). Prefer larger |mean point|.
    """
    folds = list(ledgers)
    if len(folds) < 2:
        return None, "need dual-fold ledger"
    fa, fb = folds[0], folds[1]
    candidates: list[tuple[float, str, str]] = []
    for rule in RULE_REGISTRY:
        rid = rule.rule_id
        if rid not in ledgers[fa] or rid not in ledgers[fb]:
            continue
        a, b = ledgers[fa][rid], ledgers[fb][rid]
        if a["point"] == 0 or b["point"] == 0:
            continue
        if (a["point"] > 0) != (b["point"] > 0):
            continue  # inconsistent sign
        # Credible route: at least one fold's CI UB exceeds c* in the drift direction.
        route = (a["hi"] >= C_STAR) or (b["hi"] >= C_STAR)
        if not route:
            continue
        score = abs(0.5 * (a["point"] + b["point"]))
        candidates.append((score, sleeve_id(rule.family, rule.side), rid))

    if not candidates:
        return None, "no fold-consistent rule with CI UB >= c* on either fold"

    candidates.sort(reverse=True)
    score, sleeve, rid = candidates[0]
    rule = get_rule(rid)
    rationale = (
        f"selected sleeve={sleeve} via rule={rid} "
        f"(family={rule.family}, side={rule.side}); "
        f"mean |drift|={score * BPS:.1f}bps; "
        f"fold-consistent sign; CI UB clears c* on at least one fold"
    )
    # If multiple rules share the sleeve, keep the sleeve (one head per family×side).
    return sleeve, rationale


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    print("M4R PRE-REGISTRATION: drift-sign ledger before any Stage C fit.")
    print(f"Registered rules ({len(RULE_REGISTRY)}):")
    for r in RULE_REGISTRY:
        desc = r.description.replace("≥", ">=").replace("×", "x")
        print(f"  {r.rule_id:<28} {r.family}/{r.side} - {desc}")

    periods = []
    for fold in args.folds:
        periods.append(parse_period_range(FOLDS[fold]["train_period"]))
        periods.append(parse_period_range(FOLDS[fold]["test_period"]))
    start = min(p[0] for p in periods)
    end = max(p[1] for p in periods)

    stock, *_ = load_horizon_data(
        data_dir=args.data_dir,
        config_path=args.config,
        start_period=start,
        end_period=end,
    )
    stock = _select_symbols(stock, args.max_symbols)
    print(f"symbols={stock['symbol'].n_unique()}")

    ledgers = {
        fold: _fold_ledger(fold, stock, n_boot=args.n_boot, seed=args.seed)
        for fold in args.folds
    }
    sleeve, rationale = _select_sleeve(ledgers)
    print("\n=== M4R sleeve decision ===")
    print(rationale)
    if sleeve is None:
        print(
            f"\nSTOP: no rule family has fold-consistent drift with a credible "
            f"route to c* ({C_STAR_BPS:.0f} bps). Product definition must change "
            f"(hedge / universe / session) - architecture FAIL under blueprint sec 14."
        )
        sys.exit(3)
    print(f"M4R EXIT: carry sleeve={sleeve} to Stage C (M5 re-read).")
    sys.exit(0)


if __name__ == "__main__":
    main()
