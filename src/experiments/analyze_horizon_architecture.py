"""Short architecture Phase 1 — train/val diagnosis (0 peeks)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.horizon.eval import N_BOOT, evaluate_horizon, format_report
from src.horizon.eval.architecture import (
    A1_H5_PROXY_MAX,
    A1_JACCARD_MAX,
    A1_TB_ONLY_LIFT,
    A2_MEAN_ELIGIBLE_MIN,
    A2_NDCG_LIFT_MIN,
    A3_H5_DELTA_MIN,
    adv_tercile_stress,
    apply_adv_p50_mask,
    authorize_levers,
    complementarity,
    fit_short_a2_listwise,
    fit_short_last_fold_path_ev,
    fit_tb_probe_lambdarank,
    holdout_min_n,
    listwise_geometry,
    masked_proxies,
    metric_map,
    peek_h5_clear,
    reprint_holdout_h5_fail,
    score_val_panel,
    train_adv_p50_cutoff,
)
from src.horizon.eval.diagnostics import adv_tercile_topk_diagnostics
from src.horizon.eval.nifty50_pit import apply_nifty50_mask
from src.horizon.eval.panel import annotate_hygiene_flags, prepare_eval_panel
from src.horizon.horizon_model import SHORT_FEATURES
from src.pipelines.build_horizon_features import (
    build_horizon_features,
    load_horizon_data,
)
from src.pipelines.build_regime_features import (
    build_regime_features,
    load_regime_data,
)
from src.pipelines.horizon_pipeline import predict_horizon_gbm
from src.pipelines.regime_pipeline import predict_intraday_hmm
from src.regime.intraday import override_intraday_regime
from src.utils.date import filter_by_period, parse_period_range
from src.utils.mlflow_loader import load_hmm_model

REPO_ROOT = Path(__file__).resolve().parents[2]

FOLDS = {
    "A": {
        "train_period": "2015-2017",
        "test_period": "2018-2018",
        "regime_run_id": "e9dbc99428d748f0a78e12281531f27f",
    },
    "B": {
        "train_period": "2016-2018",
        "test_period": "2019-2019",
        "regime_run_id": "7fff95a9410144efb4ac69c10608ee53",
    },
}


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None or not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _run_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    n_boot: int,
    seed: int,
) -> dict:
    cfg = FOLDS[fold]
    train_period = cfg["train_period"]
    test_period = cfg["test_period"]
    train_start, train_end = parse_period_range(train_period)
    test_start, test_end = parse_period_range(test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    print(f"\n=== Fold {fold}  train={train_period}  test={test_period} ===")
    print(f"Loading regime data {load_start} -> {load_end}...")
    vix_daily, market_daily, market_15m, nifty100_daily = load_regime_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    daily_regime, intraday_regime = build_regime_features(
        vix_daily, market_daily, market_15m, nifty100_daily
    )
    hmm_model, resolved_run_id = load_hmm_model(
        train_period=train_period,
        run_id=cfg["regime_run_id"],
    )
    print(f"   Regime run id: {resolved_run_id}")
    regime_preds = override_intraday_regime(
        predict_intraday_hmm(
            daily_regime, intraday_regime, hmm_model, apply_hysteresis=True
        )
    )
    regime_df = regime_preds.select(["date", "daily_regime", "intraday_regime"])

    print("Loading Horizon universe + building features/labels/TB...")
    stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    horizon_df = build_horizon_features(
        stock_15m,
        nifty_15m,
        sector_15m,
        daily_stock,
        daily_nifty,
        daily_regime_df=daily_regime,
        intraday_regime_df=intraday_regime,
        regime_df=regime_df,
    )
    train_df = filter_by_period(
        horizon_df, train_start, train_end, datetime_col="date"
    )
    test_df = filter_by_period(
        horizon_df, test_start, test_end, datetime_col="date"
    )
    test_df = annotate_hygiene_flags(test_df)
    print(f"   Train rows={train_df.height}  Test rows={test_df.height}")
    if train_df.height == 0 or test_df.height == 0:
        print("Error: empty train or test after period filter.")
        sys.exit(1)

    print("Fitting last-fold path-EV (Phase 1 -- not a peek)...")
    model, fold_train, fold_val, fit_stats = fit_short_last_fold_path_ev(train_df)
    if model is None or fold_train is None or fold_val is None:
        print("Error: last-fold path-EV fit failed.")
        sys.exit(1)
    print(
        f"   val IC_ev={_fmt(fit_stats.get('val_ic_ev'), 4)} "
        f"train_bars={fit_stats.get('train_bars')} val_bars={fit_stats.get('val_bars')}"
    )
    print(
        f"   sleeve bars={fit_stats['diagnostics']['bars']} "
        f"sess={fit_stats['diagnostics']['sessions']}"
    )

    val_panel = score_val_panel(fold_val, model)
    print(f"   Val eval panel rows={val_panel.height}")

    print("Fitting diagnostic TB-probe lambdarank (complementarity only)...")
    probe, ic_tb = fit_tb_probe_lambdarank(fold_train, fold_val, list(SHORT_FEATURES))
    if probe is None:
        print("Error: TB-probe fit failed.")
        sys.exit(1)
    probe_pred = probe.predict(val_panel.select(SHORT_FEATURES).to_numpy())
    # Align probe scores to val_panel row order (predict uses val_panel features).
    comp = complementarity(val_panel, probe_pred)
    comp["probe_ic_tb"] = ic_tb
    print(
        f"   Jaccard={_fmt(comp['jaccard'])}  probe IC_tb={_fmt(ic_tb, 4)}  "
        f"hit EV-only/TB-only/both/neither="
        f"{_fmt(comp['hit_ev_only'])}/{_fmt(comp['hit_tb_only'])}/"
        f"{_fmt(comp['hit_both'])}/{_fmt(comp['hit_neither'])}"
    )
    print(
        f"   val H5-proxy EV={_fmt(comp['ev_h5_proxy'], 4)} "
        f"probe={_fmt(comp['probe_h5_proxy'], 4)}  "
        f"H2-proxy EV={_fmt(comp['ev_h2_proxy'], 4)}"
    )

    geom = listwise_geometry(val_panel)
    print(
        f"   mean eligible/bar={_fmt(geom['mean_eligible'], 1)}  "
        f"grade TP/TO/SL={int(geom['n_tp'])}/{int(geom['n_to'])}/{int(geom['n_sl'])}  "
        f"NDCG@3 EV={_fmt(geom['ndcg_ev'], 4)} null={_fmt(geom['ndcg_null'], 4)} "
        f"lift={_fmt(geom['ndcg_lift'], 4)}"
    )

    advt = adv_tercile_topk_diagnostics(val_panel, "short")
    if advt:
        print(f"   val ADVt lo={_fmt(advt[0].value)}  {advt[0].note}")
    tercile = adv_tercile_stress(val_panel)
    for bucket, row in tercile.items():
        print(
            f"   ADV {bucket}: H5-proxy={_fmt(row['h5_proxy'], 4)} "
            f"H2-proxy={_fmt(row['h2_proxy'], 4)} bars={int(row['n_bars'])}"
        )

    print("Scoring holdout path-EV (frozen reprint + mask min-N; not a peek gate)...")
    holdout_scored = predict_horizon_gbm(test_df, model)
    holdout_metrics = evaluate_horizon(
        holdout_scored, directions=["short"], n_boot=n_boot, seed=seed
    )
    title = (
        f"Architecture Phase 1 holdout reprint  fold={fold}  "
        f"train={train_period}  test={test_period}  (FROZEN -- not authorize)"
    )
    report = format_report(holdout_metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    holdout_panel = prepare_eval_panel(holdout_scored, "short")
    h_bars, h_sess, h_clear = holdout_min_n(holdout_panel)
    print(f"   Holdout min-N (full): {h_bars} bars / {h_sess} sess  clear={h_clear}")

    baseline_h5 = comp["ev_h5_proxy"]
    adv_cut = train_adv_p50_cutoff(fold_train)
    print(f"   Train ADV P50 cutoff={_fmt(adv_cut, 4)}")

    masks: dict[str, dict] = {}
    for name, apply_mask in (
        ("nifty50", apply_nifty50_mask),
        ("adv_p50", lambda p: apply_adv_p50_mask(p, adv_cut)),
    ):
        val_masked = apply_mask(val_panel)
        proxies = masked_proxies(val_panel, val_masked, baseline_h5)
        ho_masked = apply_mask(holdout_panel)
        ho_rerank = ho_masked.with_columns(
            eval_rank=pl.col("eval_score")
            .rank(method="ordinal", descending=True)
            .over("date")
        )
        ho_bars, ho_sess, ho_ok = holdout_min_n(ho_rerank)
        proxies["holdout_bars"] = float(ho_bars)
        proxies["holdout_sess"] = float(ho_sess)
        proxies["holdout_min_n_clear"] = ho_ok
        masks[name] = proxies
        print(
            f"   Mask {name}: val H5 d={_fmt(proxies['h5_delta'], 4)} "
            f"H2-proxy={_fmt(proxies['h2_proxy'], 4)}  "
            f"holdout min-N {ho_bars}/{ho_sess} clear={ho_ok}"
        )

    h5_fail = reprint_holdout_h5_fail(holdout_metrics)
    row = {
        **comp,
        **geom,
        "probe_ic_tb": ic_tb,
        "masks": masks,
        "adv_cut": adv_cut,
        "holdout_h5_fail": h5_fail,
        "holdout_bars": h_bars,
        "holdout_sess": h_sess,
        "holdout_metrics": holdout_metrics,
        "train_tb_pos": fold_train.filter(pl.col("tb_label_short") == 1).height,
        "val_tb_pos": fold_val.filter(pl.col("tb_label_short") == 1).height,
    }
    return row


def _print_decision(fold_rows: dict[str, dict], decision: dict) -> None:
    print("\n=== Phase 1 numeric gate (Short; holdout H5 = frozen reprint) ===")
    print(
        f"  cuts: A1 Jaccard<{A1_JACCARD_MAX} & TB-only lift>={A1_TB_ONLY_LIFT:.3f} "
        f"& both H5-proxy<={A1_H5_PROXY_MAX} | "
        f"A2 mean-N>={A2_MEAN_ELIGIBLE_MIN:.0f} & NDCG lift>={A2_NDCG_LIFT_MIN:.3f} | "
        f"A3 dH5>={A3_H5_DELTA_MIN:.3f} & H2-proxy>0 & min-N"
    )
    for fold, row in fold_rows.items():
        print(f"  Fold {fold}:")
        print(
            f"    complementarity Jaccard={_fmt(row['jaccard'])}  "
            f"probe IC_tb={_fmt(row['probe_ic_tb'], 4)}  "
            f"hit EV-only={_fmt(row['hit_ev_only'])} TB-only={_fmt(row['hit_tb_only'])} "
            f"(d={_fmt(row['hit_tb_only'] - row['hit_ev_only'])})"
        )
        print(
            f"    val H5-proxy EV={_fmt(row['ev_h5_proxy'], 4)} "
            f"probe={_fmt(row['probe_h5_proxy'], 4)}  "
            f"holdout H5 FAIL reprint={row['holdout_h5_fail']}  "
            f"min-N {row['holdout_bars']}/{row['holdout_sess']}"
        )
        print(
            f"    listwise mean-N={_fmt(row['mean_eligible'], 1)}  "
            f"grades ok={bool(row['grade_mass_ok'])}  "
            f"NDCG lift={_fmt(row['ndcg_lift'], 4)}"
        )
        for mask, m in row["masks"].items():
            print(
                f"    {mask}: dH5={_fmt(m['h5_delta'], 4)} "
                f"H2={_fmt(m['h2_proxy'], 4)} "
                f"holdout {int(m['holdout_bars'])}/{int(m['holdout_sess'])} "
                f"min-N={m['holdout_min_n_clear']}"
            )

    print(f"  A1={decision['a1']}  A2={decision['a2']}  A3={decision['a3']} "
          f"mask={decision['a3_mask']}  mask_clear={decision['mask_clear']}")
    if decision["hard_stop"]:
        print("  HARD-STOP FIRED -> STOP @ 0/2")
        print("  authorized=[]")
        print("  next = Long-only cascade economics; Short sleeve disabled")
        return
    print(f"  AUTHORIZED ladder={decision['authorized']} (tie-break A1->A2->A3; spend <=2)")
    print(f"  Peek 1 = {decision['peek1']}"
          + (f"  Peek 2 contingent = {decision['peek2']}" if decision["peek2"] else ""))


def _load_fold_frames(
    fold: str, data_dir: Path, config_path: Path
) -> tuple[pl.DataFrame, pl.DataFrame, str, str]:
    cfg = FOLDS[fold]
    train_period = cfg["train_period"]
    test_period = cfg["test_period"]
    train_start, train_end = parse_period_range(train_period)
    test_start, test_end = parse_period_range(test_period)
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)
    print(f"\n=== Fold {fold}  train={train_period}  test={test_period} ===")
    print(f"Loading regime data {load_start} -> {load_end}...")
    vix_daily, market_daily, market_15m, nifty100_daily = load_regime_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    daily_regime, intraday_regime = build_regime_features(
        vix_daily, market_daily, market_15m, nifty100_daily
    )
    hmm_model, resolved_run_id = load_hmm_model(
        train_period=train_period,
        run_id=cfg["regime_run_id"],
    )
    print(f"   Regime run id: {resolved_run_id}")
    regime_preds = override_intraday_regime(
        predict_intraday_hmm(
            daily_regime, intraday_regime, hmm_model, apply_hysteresis=True
        )
    )
    regime_df = regime_preds.select(["date", "daily_regime", "intraday_regime"])
    print("Loading Horizon universe + building features/labels/TB...")
    stock_15m, nifty_15m, sector_15m, daily_stock, daily_nifty = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    horizon_df = build_horizon_features(
        stock_15m,
        nifty_15m,
        sector_15m,
        daily_stock,
        daily_nifty,
        daily_regime_df=daily_regime,
        intraday_regime_df=intraday_regime,
        regime_df=regime_df,
    )
    train_df = filter_by_period(
        horizon_df, train_start, train_end, datetime_col="date"
    )
    test_df = filter_by_period(
        horizon_df, test_start, test_end, datetime_col="date"
    )
    test_df = annotate_hygiene_flags(test_df)
    print(f"   Train rows={train_df.height}  Test rows={test_df.height}")
    if train_df.height == 0 or test_df.height == 0:
        print("Error: empty train or test after period filter.")
        sys.exit(1)
    return train_df, test_df, train_period, test_period


def _run_a2_peek_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    n_boot: int,
    seed: int,
) -> list:
    train_df, test_df, train_period, test_period = _load_fold_frames(
        fold, data_dir, config_path
    )
    print("Fitting A2 true listwise (rank_xendcg, grades TP=2/TO=1/SL=0, NDCG@3)...")
    model, fit_stats = fit_short_a2_listwise(train_df)
    if model is None:
        print("Error: A2 listwise fit failed.")
        sys.exit(1)
    print(
        f"   n_splits={fit_stats.get('n_splits')} mean val IC_tb="
        f"{_fmt(fit_stats.get('mean_ic_tb'), 4)}"
    )
    scored = predict_horizon_gbm(test_df, model)
    print(f"   Scored short rows: {scored.height}")
    metrics = evaluate_horizon(
        scored, directions=["short"], n_boot=n_boot, seed=seed
    )
    title = (
        f"Architecture Peek 1 A2  fold={fold}  train={train_period}  "
        f"test={test_period}  short-only"
    )
    report = format_report(metrics, title)
    sys.stdout.buffer.write((report + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()
    return metrics


def _print_peek_verdict(peek_metrics: dict[str, list]) -> None:
    print("\n=== Peek 1 A2 vs cost peek-1 Short (H5 primary; no H1/H2/H3 regression) ===")
    h5_both = True
    h123_both = True
    for fold, metrics in peek_metrics.items():
        mm = metric_map(metrics)
        h5 = mm.get("H5")
        h5_ok = peek_h5_clear(metrics)
        h1, h2, h3 = mm.get("H1"), mm.get("H2"), mm.get("H3")
        h123_ok = all(m is not None and m.gate_pass is True for m in (h1, h2, h3))
        h5_both = h5_both and h5_ok
        h123_both = h123_both and h123_ok
        h5_val = _fmt(h5.value, 4) if h5 else "nan"
        h5_lo = _fmt(h5.ci_low, 4) if h5 else "nan"
        h5_hi = _fmt(h5.ci_high, 4) if h5 else "nan"
        print(
            f"  Fold {fold}: H5={h5_val} ci=[{h5_lo}, {h5_hi}] "
            f"{'PASS' if h5_ok else 'FAIL'}  "
            f"H1/H2/H3={'PASS' if h123_ok else 'FAIL'}"
        )
    if h5_both and h123_both:
        print("  VERDICT: Short H5 dual-fold CLEAR -- STOP (PASS path)")
    else:
        print("  VERDICT: Peek 1 A2 FAIL -- no remaining authorized lever -- STOP @ FAIL")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Short architecture Phase 1 diagnosis, or Phase-1-authorized peek "
            "(A2 listwise). One lever; Short-only."
        )
    )
    parser.add_argument("--config", type=str, default="config/market_sectoral_symbols.yml")
    parser.add_argument("--data-dir", type=str, default="data/GOLDEN")
    parser.add_argument("--folds", type=str, default="A,B")
    parser.add_argument(
        "--peek",
        type=str,
        default=None,
        choices=["a2"],
        help="Authorized peek only (Phase 1 must have authorized A2).",
    )
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = REPO_ROOT / data_dir
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist.")
        sys.exit(1)
    if not config_path.exists():
        print(f"Error: Config file {config_path} does not exist.")
        sys.exit(1)

    folds = [f.strip().upper() for f in args.folds.split(",") if f.strip()]
    for fold in folds:
        if fold not in FOLDS:
            print(f"Error: unknown fold {fold}; expected one of {list(FOLDS)}")
            sys.exit(1)

    if args.peek == "a2":
        print("Architecture Peek 1 A2 -- true listwise rank_xendcg (Short only)")
        print(f"Folds={folds}  n_boot={args.n_boot}")
        peek_metrics = {}
        for fold in folds:
            peek_metrics[fold] = _run_a2_peek_fold(
                fold, data_dir, config_path, args.n_boot, args.seed
            )
        _print_peek_verdict(peek_metrics)
        return

    print("Architecture Phase 1 -- REPORT ONLY (0 peeks)")
    print(f"Folds={folds}  n_boot={args.n_boot}")

    fold_rows: dict[str, dict] = {}
    for fold in folds:
        fold_rows[fold] = _run_fold(
            fold, data_dir, config_path, args.n_boot, args.seed
        )

    holdout_fail = {f: fold_rows[f]["holdout_h5_fail"] for f in fold_rows}
    decision = authorize_levers(fold_rows, holdout_fail)
    _print_decision(fold_rows, decision)


if __name__ == "__main__":
    main()
