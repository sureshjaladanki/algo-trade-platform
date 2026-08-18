"""M5 — Stage C on Long event pool: multiclass first-hit, K3 / K4, geometry argmax."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.horizon.fresh.events import build_long_event_panel
from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.gates import k3_tp_calibration, k4_edge_over_driftless
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    attach_opportunity_ok,
    remaining_session_range,
)
from src.horizon.fresh.stage_c import FreshHorizonModel, geometry_argmax
from src.labels.fresh_barrier import (
    MIS_WIDE_LONG_GEOMETRY,
    PROD_LONG_GEOMETRY,
    calculate_fresh_long_labels,
)
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]

STAGE_C_FEATURES: tuple[str, ...] = (
    *OPPORTUNITY_FEATURES,
    "range_q25",
    "rule_orb_break_vol",
    "rule_vwap_reclaim",
    "rule_prior_day_high",
    "rule_range_expand_2x",
)


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _opportunity_panel(stock: pl.DataFrame, train_start, train_end, test_start, test_end):
    panel = remaining_session_range(attach_opportunity_features(stock))
    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
    test = filter_by_period(panel, test_start, test_end, datetime_col="date")
    tr = train.drop_nulls(subset=[*OPPORTUNITY_FEATURES, "remaining_range"])
    te = test.drop_nulls(subset=[*OPPORTUNITY_FEATURES, "remaining_range"])
    finite = pl.all_horizontal(
        [pl.col(c).is_finite() for c in (*OPPORTUNITY_FEATURES, "remaining_range")]
    )
    tr = tr.filter(finite & (pl.col("remaining_range") > 0))
    te = te.filter(finite & (pl.col("remaining_range") > 0))
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


def _event_labeled(
    stock: pl.DataFrame,
    nifty: pl.DataFrame,
    opp: pl.DataFrame,
    geometry,
) -> pl.DataFrame:
    events = build_long_event_panel(stock)
    labeled = calculate_fresh_long_labels(stock, nifty, geometry)
    out = (
        events.select(["event_id", "symbol", "date", "rule_id"])
        .join(labeled, on=["symbol", "date"], how="inner")
        .join(
            opp.select(
                ["symbol", "date", *OPPORTUNITY_FEATURES, "range_q25", "opportunity_ok"]
            ),
            on=["symbol", "date"],
            how="inner",
        )
        .filter(
            pl.col("tb_eligible")
            & pl.col("entry_ok")
            & pl.col("tb_label").is_not_null()
            & pl.col("opportunity_ok")
        )
        .with_columns(
            rule_orb_break_vol=(pl.col("rule_id") == "orb_break_vol").cast(pl.Float64),
            rule_vwap_reclaim=(pl.col("rule_id") == "vwap_reclaim").cast(pl.Float64),
            rule_prior_day_high=(pl.col("rule_id") == "prior_day_high").cast(pl.Float64),
            rule_range_expand_2x=(pl.col("rule_id") == "range_expand_2x").cast(
                pl.Float64
            ),
        )
        .drop_nulls(subset=list(STAGE_C_FEATURES) + ["tb_label", "tp_w", "sl_w"])
    )
    return out


def _run_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    *,
    max_symbols: int,
    n_boot: int,
    seed: int,
    geometry_name: str,
) -> list:
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)
    geometry = (
        MIS_WIDE_LONG_GEOMETRY
        if geometry_name == "mis_wide"
        else PROD_LONG_GEOMETRY
    )

    print(
        f"\n=== Fold {fold} geom={geometry.name} "
        f"train={cfg['train_period']} test={cfg['test_period']} ==="
    )
    stock_15m, nifty_15m, *_ = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    stock_15m = _select_symbols(stock_15m, max_symbols)
    print(f"   symbols={stock_15m['symbol'].n_unique()}")

    opp_tr, opp_te = _opportunity_panel(
        stock_15m, train_start, train_end, test_start, test_end
    )
    train_stock = filter_by_period(stock_15m, train_start, train_end, datetime_col="date")
    test_stock = filter_by_period(stock_15m, test_start, test_end, datetime_col="date")
    train_nifty = filter_by_period(nifty_15m, train_start, train_end, datetime_col="date")
    test_nifty = filter_by_period(nifty_15m, test_start, test_end, datetime_col="date")

    tr = _event_labeled(train_stock, train_nifty, opp_tr, geometry)
    te = _event_labeled(test_stock, test_nifty, opp_te, geometry)
    print(f"   event rows train={tr.height} test={te.height}")
    if tr.height < 200 or te.height < 100:
        print("   thin — skip")
        return []

    x_tr = tr.select(list(STAGE_C_FEATURES)).to_numpy()
    y_tr = tr["tb_label"].to_numpy().astype(int)
    to_ret = tr["path_ret"].to_numpy().astype(float)
    model = FreshHorizonModel().fit(x_tr, y_tr, to_returns=to_ret)

    x_te = te.select(list(STAGE_C_FEATURES)).to_numpy()
    proba = model.predict_proba(x_te)
    # Map columns via model.classes_ (0=SL, 1=TO, 2=TP encoding)
    class_to_col = {int(c): i for i, c in enumerate(model.model.classes_)}
    p_sl = (
        proba[:, class_to_col[0]]
        if 0 in class_to_col
        else np.zeros(len(proba))
    )
    p_to = (
        proba[:, class_to_col[1]]
        if 1 in class_to_col
        else np.zeros(len(proba))
    )
    p_tp = (
        proba[:, class_to_col[2]]
        if 2 in class_to_col
        else np.zeros(len(proba))
    )
    # Renormalize if a class missing
    s = p_sl + p_to + p_tp
    s = np.where(s > 0, s, 1.0)
    p_sl, p_to, p_tp = p_sl / s, p_to / s, p_tp / s

    hit_tp = (te["tb_label"].to_numpy() == 1).astype(float)
    tp_w = te["tp_w"].to_numpy().astype(float)
    sl_w = te["sl_w"].to_numpy().astype(float)
    sess = te["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)

    k3 = k3_tp_calibration(p_tp, hit_tp, fold=fold)
    # Meta-label admit: predicted P(TP) > driftless s/(g+s)
    driftless = sl_w / (tp_w + sl_w)
    admit = p_tp > driftless
    if admit.sum() < 30:
        from src.horizon.fresh.gates import GateResult

        k4 = GateResult("K4", fold, float("nan"), 0.0, False, f"thin_admit n={admit.sum()}")
    else:
        k4 = k4_edge_over_driftless(
            hit_tp[admit],
            sl_w[admit],
            tp_w[admit],
            sess[admit],
            fold=fold,
            n_boot=n_boot,
            seed=seed,
        )

    # Geometry argmax distribution (report-only)
    range_hat = te["range_q25"].to_numpy().astype(float)
    g_stars, s_stars, ev_hats = [], [], []
    for i in range(len(te)):
        # M5 ledger: probabilities are geometry-invariant (the defect). Replay
        # that sweep via a callable so this harness still runs after the
        # geometry_argmax signature lock.
        p_tp_i, p_sl_i, p_to_i = float(p_tp[i]), float(p_sl[i]), float(p_to[i])
        g, s, ev = geometry_argmax(
            lambda _tm, _sm, pt=p_tp_i, ps=p_sl_i, po=p_to_i: (pt, ps, po),
            float(range_hat[i]),
        )
        g_stars.append(g)
        s_stars.append(s)
        ev_hats.append(ev)
    g_stars = np.asarray(g_stars)
    to_mass = float((te["tb_label"].to_numpy() == 0).mean())
    admit_df = te.with_columns(_admit=pl.Series(admit))
    admit_to = (
        float(admit_df.filter(pl.col("_admit"))["tb_label"].eq(0).mean())
        if int(admit.sum())
        else float("nan")
    )

    for g in (k3, k4):
        status = "PASS" if g.passed else "FAIL"
        print(
            f"   {g.gate} {status} value={g.value:.4f} thr={g.threshold:.4f} ({g.note})"
        )
    print(
        f"   admit_rate={admit.mean():.1%} n_admit={int(admit.sum())} "
        f"TO_mass_all={to_mass:.1%} TO_mass_admit={admit_to:.1%} "
        f"g* med={np.median(g_stars):.4f} s* med={np.median(s_stars):.4f} "
        f"unique_g*={len(np.unique(np.round(g_stars, 4)))}"
    )
    return [k3, k4]


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
        "--geometry",
        choices=["prod", "mis_wide"],
        default="mis_wide",
        help="Label geometry for Stage C events",
    )
    args = parser.parse_args()

    results = []
    for fold in args.folds:
        results.extend(
            _run_fold(
                fold,
                args.data_dir,
                args.config,
                max_symbols=args.max_symbols,
                n_boot=args.n_boot,
                seed=args.seed,
                geometry_name=args.geometry,
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
