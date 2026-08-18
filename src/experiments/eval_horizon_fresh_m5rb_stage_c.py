"""M5R-b — Stage C with 1m first-hit + symmetric penetration (blueprint §9.1).

Report-only reprint of K3/K4 after fixing the two measurement biases that
push the barrier race against Long: (1) 15m dual-touch ties broken to SL,
(2) TP-only 2 bps penetration. Authority re-declaration is a separate step
after this harness is reviewed (implementation plan M5R exit).

Builds on ``eval_horizon_fresh_m5r_stage_c.py``; keeps that file as the
15m/asymmetric M5R ledger.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.experiments.eval_horizon_fresh_m5r_stage_c import (
    CALIB_SESSION_FRACTION,
    RULE_FLAGS,
    STAGE_C_FEATURES,
    _attach_forward_drift,
    _fit_opportunity,
    _purged_calibration_split,
    _select_symbols,
)
from src.horizon.fresh.direction import (
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
    attach_opportunity_features,
    remaining_session_range,
)
from src.horizon.fresh.stage_c import FreshHorizonModel
from src.horizon.fresh.tradability import attach_tradability_mask
from src.horizon.session import MIS_EXIT_BAR_END
from src.labels.fresh_barrier import (
    MIS_WIDE_LONG_GEOMETRY,
    calculate_fresh_long_labels,
    dual_touch_share,
    resolve_fresh_long_first_hit_1m,
)
from src.labels.triple_barrier import TP_PENETRATION
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range
from src.utils.eval_common import session_block_mean_ci
from src.utils.load_config import load_config
from src.utils.symbol_data import load_symbol_data

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_stock_1m(
    data_dir: Path,
    config_path: Path,
    symbols: list[str],
    start_period: str,
    end_period: str,
) -> pl.DataFrame:
    """1m OHLCV for the Stage C symbol set (CSV; parquet optional later)."""
    frames: list[pl.DataFrame] = []
    for sym in symbols:
        path = data_dir / f"{sym}.csv"
        if not path.exists():
            continue
        raw = load_symbol_data(path, start_period=start_period, end_period=end_period)
        if raw.height == 0:
            continue
        frames.append(
            raw.select(["date", "open", "high", "low", "close", "volume"]).with_columns(
                pl.lit(sym).alias("symbol")
            )
        )
    if not frames:
        raise FileNotFoundError(f"no 1m CSV loaded under {data_dir} for {symbols[:5]}…")
    return pl.concat(frames).sort(["symbol", "date"])


def _stage_c_panel_1m(
    stock_15m: pl.DataFrame,
    nifty_15m: pl.DataFrame,
    stock_1m: pl.DataFrame,
    opp: pl.DataFrame,
    *,
    use_stage_a: bool,
    penetration: float,
) -> tuple[pl.DataFrame, dict[str, float | int]]:
    """Events ∩ A ∩ B with path outcomes resolved on 1m (symmetric penetration)."""
    events = collapse_to_bar(transition_events(build_long_event_panel(stock_15m)))
    # 15m pass: widths + dual-touch diagnostic (asymmetric SL, matching M5R ledger).
    labeled_15m = calculate_fresh_long_labels(
        stock_15m, nifty_15m, MIS_WIDE_LONG_GEOMETRY
    )

    panel = labeled_15m.join(
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
        stock_15m.select(["symbol", "date", "open", "high", "low", "close", "volume"]),
        on=["symbol", "date"],
        how="inner",
    )

    if use_stage_a:
        panel = attach_tradability_mask(corwin_schultz_spread_bps(panel))
    else:
        panel = panel.with_columns(tradable_ok=pl.lit(True))

    panel = attach_direction_features(panel, nifty_15m)
    panel = attach_cross_sectional_vol_ranks(panel)

    panel = (
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
    )

    touch_stats = dual_touch_share(panel)
    panel = resolve_fresh_long_first_hit_1m(
        panel,
        stock_1m,
        penetration=penetration,
        mis_exit_bar_end=MIS_EXIT_BAR_END,
    )
    panel = panel.filter(pl.col("tb_label").is_not_null()).drop_nulls(
        subset=[*STAGE_C_FEATURES, "tb_label", "tp_w", "sl_w", "path_ret"]
    ).filter(pl.all_horizontal([pl.col(c).is_finite() for c in STAGE_C_FEATURES]))

    n_dual_1m = int(panel["dual_touch_1m"].sum()) if panel.height else 0
    touch_stats = {
        **touch_stats,
        "n_after_1m": panel.height,
        "n_dual_1m": n_dual_1m,
        "dual_touch_1m_share": (n_dual_1m / panel.height) if panel.height else float("nan"),
    }
    return panel, touch_stats


def _run_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    *,
    max_symbols: int,
    n_boot: int,
    seed: int,
    use_stage_a: bool,
    penetration: float,
) -> list[GateResult]:
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(
        f"\n=== M5R-b Fold {fold} train={cfg['train_period']} "
        f"test={cfg['test_period']} stage_a={'on' if use_stage_a else 'off'} "
        f"pen={penetration * BPS:.1f}bps symmetric ==="
    )

    stock_15m, nifty_15m, *_ = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=min(train_start, test_start),
        end_period=max(train_end, test_end),
    )
    stock_15m = _select_symbols(stock_15m, max_symbols)
    symbols = sorted(stock_15m["symbol"].unique().to_list())
    print(f"   symbols={len(symbols)}")

    print("   loading 1m bars for first-hit resolution...")
    stock_1m = _load_stock_1m(
        data_dir,
        config_path,
        symbols,
        start_period=min(train_start, test_start),
        end_period=max(train_end, test_end),
    )
    print(f"   1m rows={stock_1m.height}")

    panel = remaining_session_range(attach_opportunity_features(stock_15m))
    opp_tr, opp_te = _fit_opportunity(
        panel, train_start, train_end, test_start, test_end
    )

    def _slice(df: pl.DataFrame, lo, hi) -> pl.DataFrame:
        return filter_by_period(df, lo, hi, datetime_col="date")

    tr, touch_tr = _stage_c_panel_1m(
        _slice(stock_15m, train_start, train_end),
        _slice(nifty_15m, train_start, train_end),
        _slice(stock_1m, train_start, train_end),
        opp_tr,
        use_stage_a=use_stage_a,
        penetration=penetration,
    )
    te, touch_te = _stage_c_panel_1m(
        _slice(stock_15m, test_start, test_end),
        _slice(nifty_15m, test_start, test_end),
        _slice(stock_1m, test_start, test_end),
        opp_te,
        use_stage_a=use_stage_a,
        penetration=penetration,
    )
    print(f"   stage-C rows train={tr.height} test={te.height}")
    print(
        f"   9.1 dual-touch 15m train={touch_tr['dual_touch_share'] * 100:.2f}% "
        f"(n_dual={touch_tr['n_dual']}/{touch_tr['n']}) | "
        f"test={touch_te['dual_touch_share'] * 100:.2f}% "
        f"(n_dual={touch_te['n_dual']}/{touch_te['n']})"
    )
    print(
        f"   9.1 dual-touch 1m  train={touch_tr['dual_touch_1m_share'] * 100:.3f}% "
        f"| test={touch_te['dual_touch_1m_share'] * 100:.3f}%"
    )
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
        "--config",
        type=Path,
        default=REPO_ROOT / "config" / "market_sectoral_symbols.yml",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--max-symbols", type=int, default=0)
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--no-stage-a", action="store_true")
    parser.add_argument(
        "--penetration",
        type=float,
        default=TP_PENETRATION,
        help="Symmetric penetration applied to TP and SL (default 2 bps).",
    )
    args = parser.parse_args()
    _ = load_config(args.config)  # fail fast if config missing

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
                penetration=args.penetration,
            )
        )
    if not results:
        sys.exit(1)
    fails = [g for g in results if not g.passed]
    print(f"\nSummary: {len(results) - len(fails)}/{len(results)} gate-fold cells passed")
    print(
        "M5R-b note: report-only until dual-fold full-universe authority is "
        "pre-registered after this harness review."
    )
    if fails:
        sys.exit(2)


if __name__ == "__main__":
    main()
