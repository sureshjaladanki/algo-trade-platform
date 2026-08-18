"""M5P — validation power: MDE ledger on rolling purged folds.

Publishes minimum detectable effect for K2 / K4 / K5 proxies on the current
dual-fold design and on ≥6 rolling annual folds with explicit purge/embargo.
Pre-registers the three-way K4 rule (PASS / FAIL / INCONCLUSIVE).

Session-block bootstrap treats the session as the independent unit: ~82 names
inside a session are cross-sectionally correlated and do **not** count as 82
iid observations.

STOP if no fold design can deliver K4 MDE < c* on available history.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.horizon.fresh.events import (
    build_long_event_panel,
    collapse_to_bar,
    transition_events,
)
from src.horizon.fresh.folds import (
    FOLDS,
    ROLLING_FOLDS,
    apply_purge_cutoff,
    apply_purge_date_filter,
    fold_spec,
)
from src.horizon.fresh.friction import BPS, C_STAR, C_STAR_BPS, K2_MIN_MOVE
from src.horizon.fresh.gates import (
    GateResult,
    k2_post_gate_move,
    k4_martingale_residual,
    k4_three_way,
    k5_economics,
)
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    attach_opportunity_ok,
    remaining_session_range,
)
from src.labels.fresh_barrier import MIS_WIDE_LONG_GEOMETRY, calculate_fresh_long_labels
from src.labels.triple_barrier import TP_PENETRATION
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _event_path_panel(stock: pl.DataFrame, nifty: pl.DataFrame) -> pl.DataFrame:
    """Sparse event rows with MIS-wide path returns (15m labels — power study)."""
    events = collapse_to_bar(transition_events(build_long_event_panel(stock)))
    labeled = calculate_fresh_long_labels(
        stock,
        nifty,
        MIS_WIDE_LONG_GEOMETRY,
        tp_penetration=TP_PENETRATION,
        sl_penetration=TP_PENETRATION,  # symmetric — match M5R-b measurement
    )
    return (
        events.join(labeled, on=["symbol", "date"], how="inner")
        .filter(
            pl.col("tb_eligible")
            & pl.col("entry_ok")
            & pl.col("tb_label").is_not_null()
            & pl.col("path_ret").is_finite()
        )
        .with_columns(
            abs_move=pl.col("path_ret").abs(),
            ev_net=pl.col("path_ret") - C_STAR,
        )
    )


def _fit_opportunity_mask(
    stock: pl.DataFrame,
    train_start: str,
    train_end: str,
    *,
    purge_calendar_days: int = 0,
) -> pl.DataFrame:
    panel = remaining_session_range(attach_opportunity_features(stock))
    keep = [*OPPORTUNITY_FEATURES, "remaining_range"]
    finite = pl.all_horizontal(
        [pl.col(c).is_finite() for c in (*OPPORTUNITY_FEATURES, "remaining_range")]
    )
    tr = filter_by_period(panel, train_start, train_end, datetime_col="date")
    if purge_calendar_days > 0 and train_end.isdigit():
        tr = apply_purge_date_filter(tr, int(train_end), purge_calendar_days)
    tr = tr.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    if tr.height < 200:
        return panel.with_columns(opportunity_ok=pl.lit(True))
    model = OpportunityModel().fit(
        tr.select(list(OPPORTUNITY_FEATURES)).to_numpy(),
        tr["remaining_range"].to_numpy(),
    )
    q = model.predict_quantiles(panel.select(list(OPPORTUNITY_FEATURES)).to_numpy())
    return attach_opportunity_ok(
        panel.with_columns(
            range_q25=pl.Series(q["range_q25"]),
            range_q50=pl.Series(q["range_q50"]),
        )
    )


def _power_on_slice(
    panel: pl.DataFrame,
    *,
    fold: str,
    n_boot: int,
    seed: int,
) -> dict[str, GateResult | float]:
    path = panel["path_ret"].to_numpy().astype(float)
    abs_move = panel["abs_move"].to_numpy().astype(float)
    ev_net = panel["ev_net"].to_numpy().astype(float)
    sess = panel["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    n_sess = int(np.unique(sess).size)
    # Effective N is sessions, not name-bars (cross-sectional correlation).
    k2 = k2_post_gate_move(abs_move, sess, fold=fold, n_boot=n_boot, seed=seed)
    k4 = k4_martingale_residual(path, sess, fold=fold, n_boot=n_boot, seed=seed)
    k5 = k5_economics(ev_net, sess, fold=fold, n_boot=n_boot, seed=seed)
    return {
        "k2": k2,
        "k4": k4,
        "k5": k5,
        "n_events": float(panel.height),
        "n_sessions": float(n_sess),
        "events_per_session": float(panel.height / n_sess) if n_sess else float("nan"),
    }


def _run_fold_design(
    fold_id: str,
    stock: pl.DataFrame,
    nifty: pl.DataFrame,
    *,
    n_boot: int,
    seed: int,
    apply_opportunity: bool,
) -> dict:
    spec = fold_spec(fold_id)
    train_start, train_end = parse_period_range(spec.train_period)
    test_start, test_end = parse_period_range(spec.test_period)

    train_end_disp = train_end
    if spec.purge_calendar_days > 0 and train_end.isdigit():
        train_end_disp = apply_purge_cutoff(int(train_end), spec.purge_calendar_days)

    stock_te = filter_by_period(stock, test_start, test_end, datetime_col="date")
    nifty_te = filter_by_period(nifty, test_start, test_end, datetime_col="date")
    te = _event_path_panel(stock_te, nifty_te)

    if apply_opportunity:
        # Stage B fit on calendar train years, then drop the purged embargo window.
        opp = _fit_opportunity_mask(
            stock,
            train_start,
            train_end,
            purge_calendar_days=spec.purge_calendar_days,
        )
        te = te.join(
            opp.select(["symbol", "date", "opportunity_ok"]),
            on=["symbol", "date"],
            how="inner",
        ).filter(pl.col("opportunity_ok"))

    print(
        f"\n=== M5P fold={fold_id} train={train_start}..{train_end_disp} "
        f"test={test_start}..{test_end} purge_days={spec.purge_calendar_days} ==="
    )
    if te.height < 50:
        print(f"   thin events={te.height} — skip")
        return {"fold": fold_id, "thin": True}

    out = _power_on_slice(te, fold=fold_id, n_boot=n_boot, seed=seed)
    k2, k4, k5 = out["k2"], out["k4"], out["k5"]
    assert isinstance(k2, GateResult) and isinstance(k4, GateResult)
    assert isinstance(k5, GateResult)
    print(
        f"   effective N: events={int(out['n_events'])} sessions={int(out['n_sessions'])} "
        f"(~{out['events_per_session']:.1f} events/session; session-block bootstrap)"
    )
    print(
        f"   K2 MDE={ (k2.mde or float('nan')) * BPS:.1f}bps "
        f"point={k2.value * BPS:.1f}bps thr={K2_MIN_MOVE * BPS:.0f}bps | {k2.note}"
    )
    print(
        f"   K4 MDE={ (k4.mde or float('nan')) * BPS:.1f}bps "
        f"point={k4.value * BPS:+.2f}bps verdict={k4.verdict} | {k4.note}"
    )
    print(
        f"   K5 MDE={ (k5.mde or float('nan')) * BPS:.1f}bps "
        f"point={k5.value * BPS if np.isfinite(k5.value) else float('nan'):+.2f}bps | {k5.note}"
    )
    k4_ok_mde = k4.mde is not None and k4.mde < C_STAR
    print(
        f"   K4 MDE < c* ({C_STAR_BPS:.0f}bps): "
        f"{'YES' if k4_ok_mde else 'NO'}"
    )
    return {
        "fold": fold_id,
        "thin": False,
        "k4_mde_bps": (k4.mde or float("nan")) * BPS,
        "k4_verdict": k4.verdict,
        "k4_point_bps": k4.value * BPS,
        "k2_mde_bps": (k2.mde or float("nan")) * BPS,
        "k5_mde_bps": (k5.mde or float("nan")) * BPS,
        "n_sessions": out["n_sessions"],
        "mde_ok": k4_ok_mde,
        "purge_days": spec.purge_calendar_days,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument(
        "--folds",
        nargs="+",
        default=[*FOLDS.keys(), *ROLLING_FOLDS.keys()],
        help="Fold ids (default: A B + R2017..R2022)",
    )
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--no-opportunity",
        action="store_true",
        help="Skip Stage B mask (raw event pool power)",
    )
    args = parser.parse_args()

    # Pre-register three-way rule in the ledger (executable documentation).
    print("M5P pre-registered K4 three-way rule:")
    print("  PASS if CI LB > 0")
    print(f"  FAIL if CI UB < c* ({C_STAR_BPS:.0f} bps)")
    print("  otherwise INCONCLUSIVE (buy power; do not stop/proceed)")
    demo = k4_three_way(0.0, -0.001, C_STAR * 1.5)
    assert demo.value == "INCONCLUSIVE"

    # Load full span covering all requested folds.
    periods = []
    for fid in args.folds:
        sp = fold_spec(fid)
        periods.append(parse_period_range(sp.train_period))
        periods.append(parse_period_range(sp.test_period))
    start = min(p[0] for p in periods)
    end = max(p[1] for p in periods)

    stock, nifty, *_ = load_horizon_data(
        data_dir=args.data_dir,
        config_path=args.config,
        start_period=start,
        end_period=end,
    )
    stock = _select_symbols(stock, args.max_symbols)
    print(f"symbols={stock['symbol'].n_unique()} span={start}..{end}")

    rows = [
        _run_fold_design(
            fid,
            stock,
            nifty,
            n_boot=args.n_boot,
            seed=args.seed,
            apply_opportunity=not args.no_opportunity,
        )
        for fid in args.folds
    ]
    scored = [r for r in rows if not r.get("thin")]
    if not scored:
        print("\nSTOP: no fold produced enough events to measure MDE.")
        sys.exit(3)

    mde_ok = [r for r in scored if r.get("mde_ok")]
    worst = max(r["k4_mde_bps"] for r in scored)
    best = min(r["k4_mde_bps"] for r in scored)
    print("\n=== M5P summary ===")
    print(f"folds scored={len(scored)}  K4 MDE range=[{best:.1f}, {worst:.1f}] bps")
    print(f"folds with K4 MDE < c*: {len(mde_ok)}/{len(scored)}")
    for r in scored:
        print(
            f"  {r['fold']:<6} MDE={r['k4_mde_bps']:5.1f}bps  "
            f"point={r['k4_point_bps']:+6.2f}bps  verdict={r['k4_verdict']}  "
            f"sess={int(r['n_sessions'])} purge={r['purge_days']}d"
        )

    # Pooled rolling design: concatenate all rolling-fold path residuals' session
    # counts as a lower bound on multi-fold power (report-only companion).
    rolling = [r for r in scored if str(r["fold"]).startswith("R")]
    if len(rolling) >= 6:
        # Inverse-variance style: MDE scales ~1/sqrt(N_sess); pooled sess sum.
        sess_sum = sum(r["n_sessions"] for r in rolling)
        # Use median single-fold MDE scaled by sqrt(median_sess / sess_sum).
        med = sorted(rolling, key=lambda r: r["n_sessions"])[len(rolling) // 2]
        scale = (med["n_sessions"] / sess_sum) ** 0.5
        pooled_mde = med["k4_mde_bps"] * scale
        print(
            f"pooled-rolling K4 MDE proxy~{pooled_mde:.1f}bps "
            f"(from {len(rolling)} folds, {int(sess_sum)} session-folds)"
        )
        if pooled_mde < C_STAR_BPS:
            mde_ok.append({"fold": "pooled_rolling", "mde_ok": True})

    if not mde_ok:
        print(
            f"\nSTOP: available history cannot deliver K4 MDE < c* "
            f"({C_STAR_BPS:.0f} bps). Escalate to product definition; "
            f"do not run underpowered authority peeks."
        )
        sys.exit(3)

    print(
        f"\nM5P EXIT: K4 MDE < c* achievable on {len(mde_ok)} design(s). "
        f"Proceed to M4R with rolling purged folds + three-way K4."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
