"""M5R — Stage C rerun with the M5 harness defects repaired.

M5 declared K4 FAIL, but the head it tested had no directional input, no
calibrator, no Stage A mask, a scrambled clock feature, and an event pool that
was 73% restatements of persisting state. This harness fixes those five things
and re-reads K3 / K4. Report-only until the dual-fold full-universe authority
run is pre-registered (see implementation plan M5R).

Repairs vs ``eval_horizon_fresh_m5_stage_c.py``:
  1. ``bars_to_mis`` Int8 overflow fixed upstream in ``opportunity.py``
  2. directional + cross-sectional feature block (``fresh/direction.py``)
  3. events reduced to first-cross, one row per (symbol, bar), multi-hot rules
  4. Stage A tradability mask applied (M4 said A∩B is required before Stage C)
  5. isotonic calibration on a purged validation slice carved out of train
  6. K4 read as a martingale residual on gross return, plus TO-adjusted P(TP)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.horizon.fresh.direction import (
    DIRECTION_FEATURES,
    XS_VOL_FEATURES,
    attach_cross_sectional_vol_ranks,
    attach_direction_features,
)
from src.horizon.fresh.events import (
    build_long_event_panel,
    collapse_to_bar,
    transition_events,
)
from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.friction import BPS, C_STAR
from src.horizon.fresh.gates import (
    GateResult,
    k3_calibration_ece,
    k4_edge_over_driftless,
    k4_martingale_residual,
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
from src.labels.fresh_barrier import MIS_WIDE_LONG_GEOMETRY, calculate_fresh_long_labels
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range
from src.utils.eval_common import session_block_mean_ci

REPO_ROOT = Path(__file__).resolve().parents[2]

RULE_FLAGS: tuple[str, ...] = (
    "rule_orb_break_vol",
    "rule_vwap_reclaim",
    "rule_prior_day_high",
    "rule_range_expand_2x",
)

# Vol state enters as within-bar ranks; raw levels shift between folds.
STAGE_C_FEATURES: tuple[str, ...] = (
    *DIRECTION_FEATURES,
    *XS_VOL_FEATURES,
    "volume_z",
    "gap_bps",
    "bars_to_mis",
    *RULE_FLAGS,
    "n_rules",
)

# Fraction of train sessions held back (with a one-session embargo) for isotonic.
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


def _stage_c_panel(
    stock: pl.DataFrame,
    nifty: pl.DataFrame,
    opp: pl.DataFrame,
    *,
    use_stage_a: bool,
) -> pl.DataFrame:
    """Events ∩ Stage A ∩ Stage B, one row per (symbol, bar), fully featured."""
    events = collapse_to_bar(transition_events(build_long_event_panel(stock)))
    labeled = calculate_fresh_long_labels(stock, nifty, MIS_WIDE_LONG_GEOMETRY)

    panel = labeled.join(
        opp.select(
            ["symbol", "date", "volume_z", "gap_bps", "rv_5d", "open_30m_range",
             "bars_to_mis", "range_q25", "opportunity_ok"]
        ),
        on=["symbol", "date"],
        how="inner",
    ).join(
        stock.select(["symbol", "date", "open", "high", "low", "close", "volume"]),
        on=["symbol", "date"],
        how="inner",
    )

    if use_stage_a:
        panel = attach_tradability_mask(corwin_schultz_spread_bps(panel))
    else:
        panel = panel.with_columns(tradable_ok=pl.lit(True))

    panel = attach_direction_features(panel, nifty)
    panel = attach_cross_sectional_vol_ranks(panel)

    return (
        events.select(["symbol", "date", *RULE_FLAGS, "n_rules"])
        .join(panel, on=["symbol", "date"], how="inner")
        .filter(
            pl.col("tb_eligible")
            & pl.col("entry_ok")
            & pl.col("tb_label").is_not_null()
            & pl.col("opportunity_ok")
            & pl.col("tradable_ok")
        )
        .with_columns(n_rules=pl.col("n_rules").cast(pl.Float64))
        .drop_nulls(subset=[*STAGE_C_FEATURES, "tb_label", "tp_w", "sl_w", "path_ret"])
        .filter(pl.all_horizontal([pl.col(c).is_finite() for c in STAGE_C_FEATURES]))
    )


def _attach_forward_drift(panel: pl.DataFrame, stock: pl.DataFrame) -> pl.DataFrame:
    """
    Barrier-free return from the decision bar to the MIS flatten close.

    The barrier race mixes drift with geometry. This is the compass: a negative
    reading says the event's conditional drift points the other way, which is a
    primary-rule sign problem, not a span or cost problem.
    """
    mis_close = (
        stock.with_columns(
            date_only=pl.col("date").dt.date(), time_only=pl.col("date").dt.time()
        )
        .filter(pl.col("time_only") <= MIS_EXIT_BAR_END)
        .sort(["symbol", "date"])
        .group_by(["symbol", "date_only"])
        .agg(mis_close=pl.col("close").last())
    )
    return panel.join(mis_close, on=["symbol", "date_only"], how="left").with_columns(
        fwd_ret_mis=pl.col("mis_close") / pl.col("close") - 1.0,
    )


def _purged_calibration_split(tr: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Last ``CALIB_SESSION_FRACTION`` of train sessions for isotonic, with embargo."""
    sessions = tr["date_only"].unique().sort()
    n_cal = max(round(sessions.len() * CALIB_SESSION_FRACTION), 1)
    cal_sessions = sessions.tail(n_cal)
    fit_sessions = sessions.head(max(sessions.len() - n_cal - EMBARGO_SESSIONS, 1))
    return (
        tr.filter(pl.col("date_only").is_in(fit_sessions.implode())),
        tr.filter(pl.col("date_only").is_in(cal_sessions.implode())),
    )


def _run_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    *,
    max_symbols: int,
    n_boot: int,
    seed: int,
    use_stage_a: bool,
) -> list[GateResult]:
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(
        f"\n=== M5R Fold {fold} train={cfg['train_period']} test={cfg['test_period']} "
        f"stage_a={'on' if use_stage_a else 'off'} ==="
    )

    stock_15m, nifty_15m, *_ = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=min(train_start, test_start),
        end_period=max(train_end, test_end),
    )
    stock_15m = _select_symbols(stock_15m, max_symbols)
    print(f"   symbols={stock_15m['symbol'].n_unique()}")

    panel = remaining_session_range(attach_opportunity_features(stock_15m))
    opp_tr, opp_te = _fit_opportunity(
        panel, train_start, train_end, test_start, test_end
    )

    def _slice(df: pl.DataFrame, lo, hi) -> pl.DataFrame:
        return filter_by_period(df, lo, hi, datetime_col="date")

    tr = _stage_c_panel(
        _slice(stock_15m, train_start, train_end),
        _slice(nifty_15m, train_start, train_end),
        opp_tr,
        use_stage_a=use_stage_a,
    )
    te = _stage_c_panel(
        _slice(stock_15m, test_start, test_end),
        _slice(nifty_15m, test_start, test_end),
        opp_te,
        use_stage_a=use_stage_a,
    )
    print(f"   stage-C rows train={tr.height} test={te.height}")
    if tr.height < 500 or te.height < 200:
        print("   thin — skip")
        return []

    fit_df, cal_df = _purged_calibration_split(tr)
    print(
        f"   fit rows={fit_df.height} calib rows={cal_df.height} "
        f"(purged {CALIB_SESSION_FRACTION:.0%} of train sessions)"
    )

    feats = list(STAGE_C_FEATURES)
    model = FreshHorizonModel().fit(
        fit_df.select(feats).to_numpy(),
        fit_df["tb_label"].to_numpy().astype(int),
        to_returns=fit_df["path_ret"].to_numpy().astype(float),
    )
    if cal_df.height >= 200:
        model.calibrate(
            cal_df.select(feats).to_numpy(), cal_df["tb_label"].to_numpy().astype(int)
        )

    proba = model.predict_proba(te.select(feats).to_numpy())
    p_tp = proba[:, 2]

    label = te["tb_label"].to_numpy().astype(int)
    hit_tp = (label == 1).astype(float)
    resolved = label != 0
    tp_w = te["tp_w"].to_numpy().astype(float)
    sl_w = te["sl_w"].to_numpy().astype(float)
    path = te["path_ret"].to_numpy().astype(float)
    sess = te["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    driftless = sl_w / (tp_w + sl_w)

    k3 = k3_calibration_ece(p_tp, hit_tp, fold=fold, seed=seed)
    results = [k3]

    print(
        f"   base rates  test P(SL)={np.mean(label == -1):.3f} "
        f"P(TO)={np.mean(label == 0):.3f} P(TP)={np.mean(label == 1):.3f} | "
        f"mean p_tp_hat={p_tp.mean():.3f}"
    )

    # Admit on calibrated P(TP) vs the driftless race, then read the cost-free gates.
    admit = p_tp > driftless
    for scope, mask in (("all_events", np.ones_like(admit)), ("admit", admit)):
        if mask.sum() < 30:
            print(f"   {scope}: thin n={int(mask.sum())}")
            continue
        k4 = k4_martingale_residual(
            path[mask], sess[mask], fold=fold, n_boot=n_boot, seed=seed
        )
        k4_prob = k4_edge_over_driftless(
            hit_tp[mask],
            sl_w[mask],
            tp_w[mask],
            sess[mask],
            fold=fold,
            n_boot=n_boot,
            seed=seed,
            resolved=resolved[mask],
        )
        tag = "PASS" if k4.passed else "FAIL"
        print(
            f"   [{scope:<10}] n={int(mask.sum())} "
            f"K4 gross {tag} {k4.value * BPS:+.2f}bps ({k4.note}) "
            f"| EV_net@20={(k4.value - C_STAR) * BPS:+.2f}bps"
        )
        print(
            f"   {'':<13}K4 P(TP|resolved)-driftless {k4_prob.value * 100:+.2f}pp "
            f"({k4_prob.note})"
        )
        if scope == "admit":
            results.append(k4)

    print(f"   K3 {'PASS' if k3.passed else 'FAIL'} {k3.note}")

    # Direction compass — barrier-free drift from the event bar to MIS flatten.
    te_drift = _attach_forward_drift(te, _slice(stock_15m, test_start, test_end))
    drift = te_drift["fwd_ret_mis"].to_numpy().astype(float)
    d_mask = np.isfinite(drift)
    rng = np.random.default_rng(seed)
    point, lo, hi = session_block_mean_ci(drift[d_mask], sess[d_mask], n_boot, rng)
    print(
        f"   drift to MIS  mean={point * BPS:+.2f}bps CI=[{lo * BPS:+.2f},{hi * BPS:+.2f}] "
        f"n={int(d_mask.sum())}"
    )
    for flag in RULE_FLAGS:
        sub = te_drift.filter(pl.col(flag) > 0)
        if sub.height < 100:
            continue
        d = sub["fwd_ret_mis"].to_numpy().astype(float)
        s = sub["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
        m = np.isfinite(d)
        p, lo, hi = session_block_mean_ci(d[m], s[m], n_boot, rng)
        print(
            f"     {flag:<24} n={sub.height:<6} drift={p * BPS:+7.2f}bps "
            f"CI=[{lo * BPS:+.1f},{hi * BPS:+.1f}]"
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config", type=Path, default=REPO_ROOT / "config" / "market_sectoral_symbols.yml"
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--no-stage-a", action="store_true", help="Ablate Stage A mask")
    args = parser.parse_args()

    results: list[GateResult] = []
    for fold in args.folds:
        results.extend(
            _run_fold(
                fold,
                args.data_dir,
                args.config,
                max_symbols=args.max_symbols,
                n_boot=args.n_boot,
                seed=args.seed,
                use_stage_a=not args.no_stage_a,
            )
        )
    if not results:
        sys.exit(1)
    fails = [g for g in results if not g.passed]
    print(f"\nSummary: {len(results) - len(fails)}/{len(results)} gate-fold cells passed")
    if fails:
        sys.exit(2)


if __name__ == "__main__":
    main()
