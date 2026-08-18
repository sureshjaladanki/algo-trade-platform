"""M4R-b — two pre-registered falsifications (F1 selector, F2 c_eff).

Authority: docs/archive/horizon-fresh-m4rb-preregistration.md
Expected outcome: FAIL on both. Do not retune after seeing the log.

F1: Stage C meta-label on ``prior_day_high_reject`` Short, vertical-only
     (barrier-free side_drift to MIS; disaster filter at 500 bps).
F2: same paths with row-level ``c_eff``; flat-c* / archive-30 companions.
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
from src.horizon.fresh.direction import (
    DIRECTION_FEATURES,
    XS_VOL_FEATURES,
    attach_cross_sectional_vol_ranks,
    attach_direction_features,
)
from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.friction import ARCHIVE_C_STAR, BPS, C_STAR, C_STAR_BPS
from src.horizon.fresh.gates import (
    declare_admit_power,
    k4_martingale_residual,
    path_ev_net,
)
from src.horizon.fresh.microstructure import corwin_schultz_spread_bps
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    attach_opportunity_ok,
    remaining_session_range,
)
from src.horizon.fresh.stage_c import FreshHorizonModel
from src.horizon.fresh.tradability import attach_tradability_mask
from src.horizon.session import MIS_EXIT_BAR_END
from src.labels.fresh_barrier import MIS_VERTICAL_ONLY_SHORT_GEOMETRY
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]

RULE_ID = "prior_day_high_reject"
DISASTER_SL = MIS_VERTICAL_ONLY_SHORT_GEOMETRY.sl_floor  # 500 bps
REQUIRED_IC_BREAKEVEN = 0.054
REQUIRED_IC_MARGIN = 0.10

STAGE_C_FEATURES: tuple[str, ...] = (
    *DIRECTION_FEATURES,
    *XS_VOL_FEATURES,
    "volume_z",
    "gap_bps",
    "bars_to_mis",
    "range_q25",
)

CALIB_SESSION_FRACTION = 0.20
EMBARGO_SESSIONS = 1


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _fit_opportunity(panel: pl.DataFrame, train_start, train_end, test_start, test_end):
    finite = pl.all_horizontal(
        [pl.col(c).is_finite() for c in (*OPPORTUNITY_FEATURES, "remaining_range")]
    )
    keep = [*OPPORTUNITY_FEATURES, "remaining_range"]
    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
    test = filter_by_period(panel, test_start, test_end, datetime_col="date")
    tr = train.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    te = test.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    model = OpportunityModel().fit(
        tr.select(list(OPPORTUNITY_FEATURES)).to_numpy(),
        tr["remaining_range"].to_numpy(),
    )

    def _apply(df: pl.DataFrame) -> pl.DataFrame:
        q = model.predict_quantiles(df.select(list(OPPORTUNITY_FEATURES)).to_numpy())
        return attach_opportunity_ok(
            df.with_columns(
                range_q25=pl.Series(q["range_q25"]),
                range_q50=pl.Series(q["range_q50"]),
            )
        )

    return _apply(tr), _apply(te)


def _side_drift_panel(events: pl.DataFrame, stock: pl.DataFrame) -> pl.DataFrame:
    mis_close = (
        stock.with_columns(
            date_only=pl.col("date").dt.date(), time_only=pl.col("date").dt.time()
        )
        .filter(pl.col("time_only") <= MIS_EXIT_BAR_END)
        .sort(["symbol", "date"])
        .group_by(["symbol", "date_only"])
        .agg(mis_close=pl.col("close").last())
    )
    return (
        events.join(mis_close, on=["symbol", "date_only"], how="left")
        .with_columns(fwd_long=pl.col("mis_close") / pl.col("close") - 1.0)
        .with_columns(
            side_drift=pl.when(pl.col("side") == "long")
            .then(pl.col("fwd_long"))
            .otherwise(-pl.col("fwd_long")),
        )
        # Vertical-only disaster stop: realize −sl_floor, do not drop the path
        # (dropping the left tail biases K4 upward).
        .with_columns(
            side_drift=pl.max_horizontal(pl.col("side_drift"), pl.lit(-DISASTER_SL))
        )
    )


def _sleeve_panel(
    stock: pl.DataFrame,
    nifty: pl.DataFrame,
    opp: pl.DataFrame,
) -> pl.DataFrame:
    events = transition_candidate_events(build_candidate_event_panel(stock)).filter(
        pl.col("rule_id") == RULE_ID
    )
    if events.height == 0:
        return events
    drifted = _side_drift_panel(events, stock)
    panel = drifted.join(
        opp.select(
            [
                "symbol",
                "date",
                "volume_z",
                "gap_bps",
                "rv_5d",
                "open_30m_range",
                "bars_to_mis",
                "range_q25",
                "opportunity_ok",
            ]
        ),
        on=["symbol", "date"],
        how="inner",
    ).join(
        stock.select(["symbol", "date", "open", "high", "low", "close", "volume"]),
        on=["symbol", "date"],
        how="inner",
    )
    panel = attach_tradability_mask(corwin_schultz_spread_bps(panel))
    # atr_pct proxy for direction features
    panel = panel.with_columns(
        atr_pct=pl.max_horizontal(pl.col("rv_5d"), pl.lit(1e-4)),
    )
    panel = attach_direction_features(panel, nifty)
    panel = attach_cross_sectional_vol_ranks(panel)
    # Lookback features are undefined on the first few bars of a session / before
    # ORB exists — fill 0 rather than dropping the event (M4R-b thin-sleeve bug).
    fill0 = [c for c in (*DIRECTION_FEATURES, *XS_VOL_FEATURES) if c in panel.columns]
    panel = panel.with_columns([pl.col(c).fill_null(0.0) for c in fill0])
    # Meta-label: +1 favorable drift, −1 adverse (no TO mass under barrier-free).
    panel = panel.with_columns(
        tb_label=pl.when(pl.col("side_drift") > 0.0)
        .then(pl.lit(1, dtype=pl.Int8))
        .otherwise(pl.lit(-1, dtype=pl.Int8)),
        path_ret=pl.col("side_drift"),
        c_eff=pl.col("c_eff_bps") / BPS,
    )
    return (
        panel.filter(pl.col("opportunity_ok") & pl.col("tradable_ok"))
        .drop_nulls(subset=[*STAGE_C_FEATURES, "tb_label", "path_ret", "c_eff"])
        .filter(pl.all_horizontal([pl.col(c).is_finite() for c in STAGE_C_FEATURES]))
    )


def _purged_split(tr: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    sessions = tr["date_only"].unique().sort()
    n_cal = max(int(round(sessions.len() * CALIB_SESSION_FRACTION)), 1)
    cal = sessions.tail(n_cal)
    fit = sessions.head(max(sessions.len() - n_cal - EMBARGO_SESSIONS, 1))
    return (
        tr.filter(pl.col("date_only").is_in(fit.implode())),
        tr.filter(pl.col("date_only").is_in(cal.implode())),
    )


def _print_prereg(expected_n: int, expected_sess: int) -> None:
    plan = declare_admit_power(expected_n, expected_sess)
    print("\n=== M4R-b PRE-REGISTRATION (before fit) ===")
    print(f"  rule={RULE_ID} side=short geometry={MIS_VERTICAL_ONLY_SHORT_GEOMETRY.name}")
    print(f"  disaster_sl={DISASTER_SL * BPS:.0f}bps")
    print(
        f"  AdmitPowerPlan n={plan.expected_admit_n} sess={plan.expected_sessions} "
        f"expected_mde={plan.expected_mde_bps:.1f}bps ({plan.note})"
    )
    print(
        f"  required_IC breakeven={REQUIRED_IC_BREAKEVEN:.3f} "
        f"margin={REQUIRED_IC_MARGIN:.3f}"
    )
    print("  expected_verdict=FAIL (both F1 and F2)")


def _selector_ic(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Spearman IC of score vs realized side_drift (signed)."""
    from scipy import stats

    m = np.isfinite(y_true) & np.isfinite(scores)
    if m.sum() < 30:
        return float("nan")
    return float(stats.spearmanr(scores[m], y_true[m]).statistic)


def _run_f1(
    fold: str,
    data_dir: Path,
    config_path: Path,
    *,
    max_symbols: int,
    n_boot: int,
    seed: int,
) -> dict:
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(
        f"\n=== M4R-b F1 fold {fold} train={cfg['train_period']} "
        f"test={cfg['test_period']} ==="
    )
    stock, nifty, *_ = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=min(train_start, test_start),
        end_period=max(train_end, test_end),
    )
    stock = _select_symbols(stock, max_symbols)
    panel = remaining_session_range(attach_opportunity_features(stock))
    opp_tr, opp_te = _fit_opportunity(
        panel, train_start, train_end, test_start, test_end
    )

    def _slice(df, lo, hi):
        return filter_by_period(df, lo, hi, datetime_col="date")

    tr = _sleeve_panel(
        _slice(stock, train_start, train_end),
        _slice(nifty, train_start, train_end),
        opp_tr,
    )
    te = _sleeve_panel(
        _slice(stock, test_start, test_end),
        _slice(nifty, test_start, test_end),
        opp_te,
    )
    # Ex-ante admit plan from train base rate of "worth it" (~half if balanced).
    _print_prereg(max(int(0.25 * te.height), 1), max(te["date_only"].n_unique(), 1))
    print(f"   sleeve rows train={tr.height} test={te.height}")
    if tr.height < 200 or te.height < 80:
        print("   thin — skip")
        return {}

    fit_df, cal_df = _purged_split(tr)
    feats = list(STAGE_C_FEATURES)
    model = FreshHorizonModel().fit(
        fit_df.select(feats).to_numpy(),
        fit_df["tb_label"].to_numpy().astype(int),
    )
    if cal_df.height >= 100:
        model.calibrate(
            cal_df.select(feats).to_numpy(),
            cal_df["tb_label"].to_numpy().astype(int),
        )
    proba = model.predict_proba(te.select(feats).to_numpy())
    # classes: 0=SL(adverse), 1=TO, 2=TP(favorable) — with binary labels TO absent
    p_fav = proba[:, 2] if proba.shape[1] > 2 else proba[:, -1]
    path = te["path_ret"].to_numpy().astype(float)
    sess = te["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    ceff = te["c_eff"].to_numpy().astype(float)

    admit = p_fav > 0.5
    print(f"   admit_rate={admit.mean():.1%} n_admit={int(admit.sum())}")
    ic = _selector_ic(path, p_fav)
    print(
        f"   selector_IC={ic:+.4f} (need ≥{REQUIRED_IC_BREAKEVEN:.3f} breakeven / "
        f"{REQUIRED_IC_MARGIN:.3f} margin)"
    )

    out = {"fold": fold, "ic": ic, "n_admit": int(admit.sum()), "ceff": None}
    for scope, mask in (("all", np.ones_like(admit)), ("admit", admit)):
        if mask.sum() < 30:
            print(f"   [{scope}] thin")
            continue
        k4 = k4_martingale_residual(
            path[mask], sess[mask], fold=fold, n_boot=n_boot, seed=seed
        )
        print(
            f"   [{scope:<5}] K4 gross {k4.note} | "
            f"EV_net@20={(k4.value - C_STAR) * BPS:+.2f}bps"
        )
        if scope == "admit":
            out["k4"] = k4
            out["path"] = path[mask]
            out["sess"] = sess[mask]
            out["ceff"] = ceff[mask]
    return out


def _run_f2(f1: dict, *, n_boot: int, seed: int) -> None:
    print("\n=== M4R-b F2 row-level c_eff reprint ===")
    if not f1 or f1.get("ceff") is None or f1.get("path") is None:
        print("   no F1 admit set — skip")
        return
    path, sess, ceff = f1["path"], f1["sess"], f1["ceff"]
    print(
        f"   c_eff p10/p50/p90 = "
        f"{np.percentile(ceff, 10) * BPS:.1f} / "
        f"{np.percentile(ceff, 50) * BPS:.1f} / "
        f"{np.percentile(ceff, 90) * BPS:.1f} bps  "
        f"(flat c*={C_STAR_BPS:.0f})"
    )
    # Capacity sketch: liquid-tail share below median c_eff of 12 bps.
    liquid = ceff <= 0.0012
    print(
        f"   liquid_tail (c_eff≤12bps) share={liquid.mean():.1%} "
        f"n={int(liquid.sum())} — capacity statement: sparse book only; "
        f"do not scale past ADV participation without a separate charter"
    )
    for name, cost in (
        ("c_eff", ceff),
        ("flat_c*", C_STAR),
        ("archive_30", ARCHIVE_C_STAR),
    ):
        ev = path_ev_net(path, cost)
        # EV_net is already net of cost — three-way null is 0, not c*.
        k4 = k4_martingale_residual(
            ev, sess, fold=f1["fold"], n_boot=n_boot, seed=seed, c_star=0.0
        )
        print(f"   [{name:<10}] EV_net {k4.note}")


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
    parser.add_argument(
        "--mode", choices=["f1", "f2", "both"], default="both"
    )
    args = parser.parse_args()

    print(
        "M4R-b falsifications — pre-registration: "
        "docs/archive/horizon-fresh-m4rb-preregistration.md"
    )
    results = []
    for fold in args.folds:
        if args.mode in ("f1", "both"):
            f1 = _run_f1(
                fold,
                args.data_dir,
                args.config,
                max_symbols=args.max_symbols,
                n_boot=args.n_boot,
                seed=args.seed,
            )
            results.append(f1)
            if args.mode in ("f2", "both") and f1:
                _run_f2(f1, n_boot=args.n_boot, seed=args.seed)

    # Combined verdict (decision folds only) — matches preregistration.
    f1_pass_folds = []
    f1_fail_folds = []
    for f1 in results:
        if not f1 or "k4" not in f1:
            f1_fail_folds.append("thin")
            continue
        k4 = f1["k4"]
        ic = f1.get("ic", float("nan"))
        ic_ok = np.isfinite(ic) and ic >= REQUIRED_IC_BREAKEVEN
        if k4.verdict == "PASS" and ic_ok:
            f1_pass_folds.append(f1["fold"])
            print(f"\nFold {f1['fold']}: F1 PASS (K4 PASS + IC={ic:.4f} ≥ {REQUIRED_IC_BREAKEVEN})")
        else:
            f1_fail_folds.append(f1["fold"])
            print(
                f"\nFold {f1['fold']}: F1 FAIL (verdict={k4.verdict}, "
                f"IC={ic:.4f}, need IC≥{REQUIRED_IC_BREAKEVEN})"
            )
    if f1_pass_folds and not f1_fail_folds:
        print("\nM4R-b F1 dual-fold PASS — open M5 re-read / M6 on this sleeve.")
        return
    print(
        "\nM4R-b F1 FAIL on decision folds (selector IC below breakeven and/or "
        "K4 not dual-fold PASS). F2 c_eff companions are in the log above. "
        "Combined F1 FAIL + F2 without dual-fold EV_net LB>0 → earn §14 "
        "capability FAIL → M9."
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
