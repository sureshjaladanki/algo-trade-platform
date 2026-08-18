"""M3 — Stage B opportunity gate: K1 / K2 + optional post-gate selection ceiling.

Full-universe dual-fold is the M3 exit. Use ``--max-symbols 0`` for all trade names.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import numpy as np
import polars as pl

from src.horizon.fresh.diagnostics import (
    format_ceiling_report,
    production_long_eligible_mask,
    selection_ceiling,
)
from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.friction import BPS, K2_MIN_MOVE
from src.horizon.fresh.gates import GateResult, k1_range_spearman, k2_post_gate_move
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    attach_opportunity_ok,
    remaining_session_range,
)
from src.labels.fresh_barrier import (
    PROD_LONG_GEOMETRY,
    calculate_fresh_long_labels,
)
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range

REPO_ROOT = Path(__file__).resolve().parents[2]
_ENTRY_LO = dt.time(9, 30)
_ENTRY_HI = dt.time(13, 45)


def _feature_matrix(df: pl.DataFrame) -> tuple[pl.DataFrame, np.ndarray, np.ndarray]:
    use = df.drop_nulls(subset=[*OPPORTUNITY_FEATURES, "remaining_range"])
    # Polars NaN ≠ null — keep only finite feature/target rows for LightGBM.
    finite = pl.all_horizontal(
        [pl.col(c).is_finite() for c in (*OPPORTUNITY_FEATURES, "remaining_range")]
    )
    use = use.filter(finite & (pl.col("remaining_range") > 0))
    x = use.select(list(OPPORTUNITY_FEATURES)).to_numpy()
    y = use["remaining_range"].to_numpy().astype(float)
    return use, x, y


def _select_symbols(stock: pl.DataFrame, max_symbols: int) -> pl.DataFrame:
    if max_symbols <= 0:
        return stock
    syms = sorted(stock["symbol"].unique().to_list())[:max_symbols]
    return stock.filter(pl.col("symbol").is_in(syms))


def _run_fold(
    fold: str,
    data_dir: Path,
    config_path: Path,
    *,
    max_symbols: int,
    n_boot: int,
    seed: int,
    with_ceiling: bool,
) -> list:
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    load_start = min(train_start, test_start)
    load_end = max(train_end, test_end)

    print(f"\n=== Fold {fold} train={cfg['train_period']} test={cfg['test_period']} ===")
    stock_15m, nifty_15m, *_rest = load_horizon_data(
        data_dir=data_dir,
        config_path=config_path,
        start_period=load_start,
        end_period=load_end,
    )
    stock_15m = _select_symbols(stock_15m, max_symbols)
    n_sym = stock_15m["symbol"].n_unique()
    print(f"   symbols={n_sym}")

    panel = remaining_session_range(attach_opportunity_features(stock_15m))
    panel = panel.filter(
        (pl.col("time_only") > _ENTRY_LO) & (pl.col("time_only") <= _ENTRY_HI)
    )

    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
    test = filter_by_period(panel, test_start, test_end, datetime_col="date")
    use_tr, x_tr, y_tr = _feature_matrix(train)
    use_te, x_te, y_te = _feature_matrix(test)
    print(f"   train={x_tr.shape[0]} test={x_te.shape[0]} feats={x_tr.shape[1]}")
    if x_tr.shape[0] < 200 or x_te.shape[0] < 100:
        print("   thin — skip")
        return []

    model = OpportunityModel().fit(x_tr, y_tr)
    q = model.predict_quantiles(x_te)
    k1 = k1_range_spearman(q["range_q50"], y_te, fold=fold)

    te_df = use_te.with_columns(
        range_q25=pl.Series(q["range_q25"]),
        range_q50=pl.Series(q["range_q50"]),
        range_q75=pl.Series(q["range_q75"]),
    )
    te_df = attach_opportunity_ok(te_df)
    gate_rate = float(te_df["opportunity_ok"].mean())
    gated = te_df.filter(pl.col("opportunity_ok"))
    print(
        f"   opportunity_ok rate={gate_rate:.1%} "
        f"n_gate={gated.height} med_rem_range="
        f"{float(gated['remaining_range'].median()) * BPS:.0f}bps"
        if gated.height
        else f"   opportunity_ok rate={gate_rate:.1%} n_gate=0"
    )

    if gated.height < 30:
        k2 = GateResult(
            "K2", fold, float("nan"), K2_MIN_MOVE, False, f"thin_gate n={gated.height}"
        )
    else:
        moves = gated["remaining_range"].to_numpy().astype(float)
        sess = gated["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
        k2 = k2_post_gate_move(moves, sess, fold=fold, n_boot=n_boot, seed=seed)

    for g in (k1, k2):
        status = "PASS" if g.passed else "FAIL"
        print(
            f"   {g.gate} {status} value={g.value:.4f} "
            f"thr={g.threshold:.4f} ({g.note})"
        )

    if with_ceiling:
        test_stock = filter_by_period(
            stock_15m, test_start, test_end, datetime_col="date"
        )
        test_nifty = filter_by_period(
            nifty_15m, test_start, test_end, datetime_col="date"
        )
        labeled = calculate_fresh_long_labels(
            test_stock, test_nifty, PROD_LONG_GEOMETRY
        )
        opp_keys = te_df.select(
            ["symbol", "date", "opportunity_ok", "remaining_range", "range_q25"]
        )
        joined = labeled.join(opp_keys, on=["symbol", "date"], how="inner")
        base = joined.filter(pl.all_horizontal(production_long_eligible_mask()))
        ungated = selection_ceiling(
            base,
            fold=fold,
            pool_name="eligible_ungated",
            n_boot=n_boot,
            seed=seed,
        )
        post = selection_ceiling(
            base.filter(pl.col("opportunity_ok")),
            fold=fold,
            pool_name="eligible_opportunity_ok",
            n_boot=n_boot,
            seed=seed,
        )
        print(format_ceiling_report(ungated))
        print(format_ceiling_report(post))
        if ungated.n_pool and post.n_pool:
            print(
                f"   ceiling lift top10%: "
                f"{(post.top_decile_mean - ungated.top_decile_mean) * BPS:+.1f}bps  "
                f"pos-mass {ungated.pos_mass:.1%} -> {post.pos_mass:.1%}  "
                f"TO {ungated.p_to:.1%} -> {post.p_to:.1%}"
            )

    return [k1, k2]


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
        "--max-symbols",
        type=int,
        default=0,
        help="Cap symbols for smoke; 0 = full trade universe",
    )
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--with-ceiling",
        action="store_true",
        help="Publish ungated vs opportunity_ok selection ceilings",
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
                with_ceiling=args.with_ceiling,
            )
        )
    if not results:
        sys.exit(1)

    by_gate: dict[str, list] = {}
    for g in results:
        by_gate.setdefault(g.gate, []).append(g)
    dual_ok = all(all(x.passed for x in gs) for gs in by_gate.values())
    fails = [g for g in results if not g.passed]
    print(
        f"\nSummary: {len(results) - len(fails)}/{len(results)} gate-fold cells passed"
    )
    for gate, gs in sorted(by_gate.items()):
        folds = ",".join(f"{g.fold}:{'P' if g.passed else 'F'}" for g in gs)
        print(f"  {gate} dual-fold={'PASS' if all(g.passed for g in gs) else 'FAIL'} [{folds}]")
    if dual_ok and len(by_gate.get("K1", [])) >= 2 and len(by_gate.get("K2", [])) >= 2:
        print("M3 K1/K2 dual-fold PASS (authority run).")
    else:
        print("M3 K1/K2 not yet dual-fold complete or FAIL.")
        if fails:
            sys.exit(2)


if __name__ == "__main__":
    main()
