"""M5 forensics — why K3/K4 failed: Stage B clock confound, event dup, K4 null.

Report-only. Does not re-run a geometry grid; audits the M5 harness itself.

Three questions:
  D1  Is ``opportunity_ok`` a remaining-time filter rather than a range filter?
  D2  How much of the "event" pool is persistent state / duplicated bars?
  D3  Is the K4 driftless null mis-specified once timeout mass exists?
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

from src.horizon.fresh.events import build_long_event_panel
from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.friction import BPS, C_STAR
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    attach_opportunity_ok,
    remaining_session_range,
)
from src.horizon.fresh.stage_c import FreshHorizonModel
from src.labels.fresh_barrier import MIS_WIDE_LONG_GEOMETRY, calculate_fresh_long_labels
from src.pipelines.build_horizon_features import load_horizon_data
from src.utils.date import filter_by_period, parse_period_range
from src.utils.eval_common import session_block_mean_ci

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


def _fit_opportunity(panel: pl.DataFrame, train_start, train_end, test_start, test_end):
    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
    test = filter_by_period(panel, test_start, test_end, datetime_col="date")
    finite = pl.all_horizontal(
        [pl.col(c).is_finite() for c in (*OPPORTUNITY_FEATURES, "remaining_range")]
    )
    keep = [*OPPORTUNITY_FEATURES, "remaining_range"]
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


def _d1_clock_confound(te: pl.DataFrame) -> None:
    """K1 with and without the remaining-time channel; gate mass by clock."""
    print("\n--- D1  Stage B: range skill vs remaining-time mechanics ---")
    pred = te["range_q50"].to_numpy().astype(float)
    real = te["remaining_range"].to_numpy().astype(float)
    clock = te["bars_to_mis"].to_numpy().astype(float)

    rho_pred = float(stats.spearmanr(pred, real).statistic)
    rho_clock = float(stats.spearmanr(clock, real).statistic)
    print(f"  Spearman(range_q50, remaining_range)      = {rho_pred:.3f}   <- K1 as gated")
    print(f"  Spearman(bars_to_mis, remaining_range)    = {rho_clock:.3f}   <- clock alone")

    # Within-clock (partial) Spearman: pool rank residuals inside each bar-of-day.
    within = []
    weights = []
    for (c,), grp in te.group_by(["bars_to_mis"], maintain_order=True):
        if grp.height < 200:
            continue
        r = float(
            stats.spearmanr(
                grp["range_q50"].to_numpy().astype(float),
                grp["remaining_range"].to_numpy().astype(float),
            ).statistic
        )
        if np.isfinite(r):
            within.append(r)
            weights.append(grp.height)
    if within:
        w = np.asarray(weights, dtype=float)
        rho_within = float(np.average(np.asarray(within), weights=w))
        print(
            f"  Within-clock Spearman (n-weighted)       = {rho_within:.3f}   "
            f"<- K1 with clock removed  [buckets={len(within)}]"
        )

    gate_by_clock = (
        te.group_by("bars_to_mis")
        .agg(
            n=pl.len(),
            gate_rate=pl.col("opportunity_ok").mean(),
            med_pred=pl.col("range_q50").median(),
        )
        .sort("bars_to_mis", descending=True)
    )
    print("\n  opportunity_ok rate by bars_to_mis (gate mass concentration):")
    for row in gate_by_clock.iter_rows(named=True):
        print(
            f"    bars_to_mis={row['bars_to_mis']:>3}  n={row['n']:>7}  "
            f"gate_rate={row['gate_rate']:>6.1%}  med_pred={row['med_pred'] * BPS:>6.0f}bps"
        )
    gated = te.filter(pl.col("opportunity_ok"))
    if gated.height:
        print(
            f"\n  gated median bars_to_mis={float(gated['bars_to_mis'].median()):.1f} "
            f"vs ungated {float(te['bars_to_mis'].median()):.1f}"
        )


def _d2_event_pool(events: pl.DataFrame) -> None:
    """Duplication and staleness of the 'event' clock."""
    print("\n--- D2  Event clock: duplication and persistence ---")
    n_rows = events.height
    n_bars = events.select(["symbol", "date"]).unique().height
    print(f"  event rows={n_rows}  unique (symbol,bar)={n_bars}  "
          f"rows/bar={n_rows / max(n_bars, 1):.2f}")

    by_rule = (
        events.group_by("rule_id").agg(n=pl.len()).sort("n", descending=True)
    )
    print("  rows by rule:")
    for row in by_rule.iter_rows(named=True):
        print(f"    {row['rule_id']:<18} n={row['n']:>8}  ({row['n'] / n_rows:.1%})")

    # Fresh = first bar in the session where this (symbol, rule) fires.
    fresh = (
        events.sort(["symbol", "rule_id", "date"])
        .with_columns(date_only=pl.col("date").dt.date())
        .with_columns(
            _seq=pl.int_range(pl.len()).over(["symbol", "date_only", "rule_id"]),
        )
    )
    fresh_share = (
        fresh.group_by("rule_id")
        .agg(
            n=pl.len(),
            first_cross=(pl.col("_seq") == 0).sum(),
            fresh_rate=(pl.col("_seq") == 0).mean(),
        )
        .sort("rule_id")
    )
    print("  first-cross (fresh) share per rule — rest are restatements of the same state:")
    for row in fresh_share.iter_rows(named=True):
        print(
            f"    {row['rule_id']:<18} n={row['n']:>8}  fresh={row['first_cross']:>7}  "
            f"fresh_rate={row['fresh_rate']:>6.1%}"
        )
    print(
        f"  overall fresh_rate={float((fresh['_seq'] == 0).mean()):.1%}  "
        f"=> decision pool is mostly persistent state, not events"
    )


def _d3_k4_null(te: pl.DataFrame, p_tp: np.ndarray, n_boot: int, seed: int) -> None:
    """K4 as coded vs TO-adjusted vs martingale-residual (gross return) test."""
    print("\n--- D3  K4 null specification ---")
    label = te["tb_label"].to_numpy().astype(int)
    tp_w = te["tp_w"].to_numpy().astype(float)
    sl_w = te["sl_w"].to_numpy().astype(float)
    path = te["path_ret"].to_numpy().astype(float)
    sess = te["date_only"].cast(pl.Int32).to_numpy().astype(np.int64)
    driftless = sl_w / (tp_w + sl_w)
    admit = p_tp > driftless
    rng = np.random.default_rng(seed)

    hit_tp = (label == 1).astype(float)
    resolved = label != 0

    def _ci(vals: np.ndarray, mask: np.ndarray) -> tuple[float, float, float]:
        return session_block_mean_ci(vals[mask], sess[mask], n_boot, rng)

    for name, mask in (("all_events", np.ones_like(admit)), ("admit_set", admit)):
        if mask.sum() < 30:
            print(f"  {name}: thin n={int(mask.sum())}")
            continue
        n = int(mask.sum())
        to_mass = float((label[mask] == 0).mean())

        # (a) exactly as coded in gates.k4_edge_over_driftless
        pt, lo, hi = _ci(hit_tp - driftless, mask)
        print(
            f"  {name} n={n} TO={to_mass:.1%}\n"
            f"    (a) as-coded   P(TP) - s/(g+s)          "
            f"point={pt * 100:+.2f}pp CI[{lo * 100:+.2f},{hi * 100:+.2f}]"
        )

        # (b) conditional on resolution — removes the timeout dilution
        rmask = mask & resolved
        ptb, lob, hib = _ci(hit_tp - driftless, rmask)
        print(
            f"    (b) TO-adjusted P(TP|resolved) - s/(g+s) "
            f"point={ptb * 100:+.2f}pp CI[{lob * 100:+.2f},{hib * 100:+.2f}]  "
            f"n={int(rmask.sum())}"
        )

        # (c) martingale residual: gross path return. Exactly 0 under the null,
        #     geometry-free and timeout-safe. This is the honest cost-free test.
        ptc, loc_, hic = _ci(path, mask)
        print(
            f"    (c) gross E[path_ret]                   "
            f"point={ptc * BPS:+.2f}bps CI[{loc_ * BPS:+.2f},{hic * BPS:+.2f}]"
        )
        print(
            f"        implied EV_net @ c*=20              "
            f"point={(ptc - C_STAR) * BPS:+.2f}bps"
        )


def _d4_feature_content(tr: pl.DataFrame) -> None:
    """Does the Stage C feature set carry any directional information at all?"""
    print("\n--- D4  Stage C feature set: directional content ---")
    x = tr.select(list(STAGE_C_FEATURES)).to_numpy()
    label = tr["tb_label"].to_numpy().astype(int)
    print(f"  features={list(STAGE_C_FEATURES)}")
    print("  every column above is a volatility/range/rule-identity measure;")
    print("  none encodes where price is or which way it is moving.")

    # Univariate directional signal: Spearman(feature, TP-vs-SL outcome) on resolved.
    resolved = label != 0
    y = (label[resolved] == 1).astype(float)
    print("\n  Spearman(feature, 1{TP first}) on resolved rows:")
    for i, name in enumerate(STAGE_C_FEATURES):
        col = x[resolved, i].astype(float)
        if not np.isfinite(col).all() or np.unique(col).size < 3:
            continue
        r = float(stats.spearmanr(col, y).statistic)
        print(f"    {name:<20} rho={r:+.4f}")

    model = FreshHorizonModel().fit(x, label)
    imp = model.model.feature_importances_
    order = np.argsort(imp)[::-1]
    print("\n  LightGBM gain-split importance (as trained in M5):")
    for i in order:
        print(f"    {STAGE_C_FEATURES[i]:<20} {imp[i]:>8}")


def _run_fold(
    fold: str, data_dir: Path, config_path: Path, *, max_symbols: int, n_boot: int, seed: int
) -> None:
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(f"\n{'=' * 72}\n=== Fold {fold} train={cfg['train_period']} test={cfg['test_period']}\n{'=' * 72}")

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
    _d1_clock_confound(opp_te)

    test_stock = filter_by_period(stock_15m, test_start, test_end, datetime_col="date")
    train_stock = filter_by_period(stock_15m, train_start, train_end, datetime_col="date")
    test_nifty = filter_by_period(nifty_15m, test_start, test_end, datetime_col="date")
    train_nifty = filter_by_period(nifty_15m, train_start, train_end, datetime_col="date")

    events_te = build_long_event_panel(test_stock)
    _d2_event_pool(events_te)

    def _joined(stock, nifty, opp) -> pl.DataFrame:
        events = build_long_event_panel(stock)
        labeled = calculate_fresh_long_labels(stock, nifty, MIS_WIDE_LONG_GEOMETRY)
        return (
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
                rule_range_expand_2x=(pl.col("rule_id") == "range_expand_2x").cast(pl.Float64),
            )
            .drop_nulls(subset=list(STAGE_C_FEATURES) + ["tb_label", "tp_w", "sl_w"])
        )

    tr = _joined(train_stock, train_nifty, opp_tr)
    te = _joined(test_stock, test_nifty, opp_te)
    print(f"\n   stage-C rows train={tr.height} test={te.height}")

    # Geometry span actually labeled vs geometry the argmax "chose".
    span = (te["tp_w"] + te["sl_w"]).to_numpy()
    print(
        f"   labeled span median={float(np.median(span)) * BPS:.0f}bps  "
        f"unique (tp_w,sl_w) pairs={te.select(['tp_w', 'sl_w']).unique().height}"
    )

    _d4_feature_content(tr)

    model = FreshHorizonModel().fit(
        tr.select(list(STAGE_C_FEATURES)).to_numpy(),
        tr["tb_label"].to_numpy().astype(int),
    )
    proba = model.predict_proba(te.select(list(STAGE_C_FEATURES)).to_numpy())
    col = {int(c): i for i, c in enumerate(model.model.classes_)}
    p_tp = proba[:, col[2]] if 2 in col else np.zeros(len(proba))
    _d3_k4_null(te, p_tp, n_boot, seed)

    # Base-rate shift between train and test — the K3 calibration killer.
    print("\n--- D5  Outcome base-rate shift train -> test (uncalibrated K3) ---")
    for name, frame in (("train", tr), ("test", te)):
        lab = frame["tb_label"].to_numpy().astype(int)
        print(
            f"  {name:<6} P(SL)={np.mean(lab == -1):.3f} "
            f"P(TO)={np.mean(lab == 0):.3f} P(TP)={np.mean(lab == 1):.3f}"
        )
    print(f"  mean predicted P(TP) on test={float(p_tp.mean()):.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--config", type=Path, default=REPO_ROOT / "config" / "market_sectoral_symbols.yml"
    )
    parser.add_argument("--folds", nargs="+", default=["A"])
    parser.add_argument("--max-symbols", type=int, default=20)
    parser.add_argument("--n-boot", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    for fold in args.folds:
        _run_fold(
            fold,
            args.data_dir,
            args.config,
            max_symbols=args.max_symbols,
            n_boot=args.n_boot,
            seed=args.seed,
        )


if __name__ == "__main__":
    main()
