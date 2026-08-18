"""M9 V1-index — does the range head beat India VIX on Nifty itself?

Authority-style methodology kill-switch that uses only in-repo data
(^NSEI + ^INDIAVIX). This is **not** single-name V1 (that needs M9-0).

Cash-index feeds ship volume ≡ 0, so ``volume_z`` is **dropped** for this
harness only (Regime Tier-1 lock: do not fake participation). Stock Stage B
keeps ``volume_z``.

PASS: ``range_q50`` coef > 0 and p < 0.05 dual-fold on index remaining range
after controlling for VIX-implied remaining range.

If FAIL: Track A is unlikely to work even with perfect single-name IV — the
forecast adds nothing beyond the IV market at the liquid index. Escalate or stop.
If PASS: proceed with M9-0; name-level V1 is still required for the product.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

from src.horizon.fresh.folds import FOLDS
from src.horizon.fresh.opportunity import (
    OPPORTUNITY_FEATURES,
    OpportunityModel,
    attach_opportunity_features,
    remaining_session_range,
)
from src.horizon.m9.implied_range import (
    DEFAULT_RANGE_KAPPA,
    attach_vix_implied_range,
    daily_vix_from_1m,
)
from src.horizon.m9.v1_incremental import incremental_range_ols
from src.utils.data import resample_15m
from src.utils.date import filter_by_period, parse_period_range
from src.utils.symbol_data import load_symbol_data

REPO_ROOT = Path(__file__).resolve().parents[2]

# Index-only: exclude participation. Equities keep full OPPORTUNITY_FEATURES.
INDEX_OPPORTUNITY_FEATURES: tuple[str, ...] = tuple(
    f for f in OPPORTUNITY_FEATURES if f != "volume_z"
)


def _nifty_15m(data_dir: Path, start: str, end: str) -> pl.DataFrame:
    raw = load_symbol_data(
        data_dir / "^NSEI.csv", start_period=start, end_period=end
    )
    return (
        resample_15m(raw)
        .with_columns(pl.lit("^NSEI").alias("symbol"))
        .select(["symbol", "date", "open", "high", "low", "close", "volume"])
    )


def _run_fold(
    fold: str,
    data_dir: Path,
    vix_path: Path,
    *,
    kappa: float,
) -> bool:
    cfg = FOLDS[fold]
    train_start, train_end = parse_period_range(cfg["train_period"])
    test_start, test_end = parse_period_range(cfg["test_period"])
    print(
        f"\n=== M9 V1-index fold {fold} "
        f"train={cfg['train_period']} test={cfg['test_period']} ==="
    )

    nifty = _nifty_15m(
        data_dir, min(train_start, test_start), max(train_end, test_end)
    )
    vix_1m = load_symbol_data(
        vix_path,
        start_period=min(train_start, test_start),
        end_period=max(train_end, test_end),
    )
    vix_daily = daily_vix_from_1m(vix_1m)

    panel = remaining_session_range(attach_opportunity_features(nifty))
    panel = panel.filter(pl.col("bars_to_mis") > 0)
    train = filter_by_period(panel, train_start, train_end, datetime_col="date")
    test = filter_by_period(panel, test_start, test_end, datetime_col="date")
    feats = list(INDEX_OPPORTUNITY_FEATURES)
    keep = [*feats, "remaining_range"]
    finite = pl.all_horizontal([pl.col(c).is_finite() for c in keep])
    tr = train.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    te = test.drop_nulls(subset=keep).filter(finite & (pl.col("remaining_range") > 0))
    print(f"   train={tr.height} test={te.height} feats={feats}")

    model = OpportunityModel().fit(
        tr.select(feats).to_numpy(),
        tr["remaining_range"].to_numpy(),
    )
    q = model.predict_quantiles(te.select(feats).to_numpy())
    te = te.with_columns(range_q50=pl.Series(q["range_q50"]))
    te = attach_vix_implied_range(te, vix_daily, kappa=kappa)

    res = incremental_range_ols(
        te["remaining_range"].to_numpy(),
        te["range_imp_vix"].to_numpy(),
        te["range_q50"].to_numpy(),
    )
    status = "PASS" if res.passed else "FAIL"
    print(
        f"   V1-index {status} n={res.n} R2={res.r2:.3f} "
        f"b_imp={res.coef_implied:+.3f} b_q50={res.coef_q50:+.3f} "
        f"t_q50={res.t_q50:+.2f} p={res.p_q50:.4g}"
    )
    return res.passed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data" / "GOLDEN")
    parser.add_argument(
        "--vix-path",
        type=Path,
        default=REPO_ROOT / "data" / "GOLDEN" / "^INDIAVIX.csv",
    )
    parser.add_argument("--folds", nargs="+", default=["A", "B"])
    parser.add_argument("--kappa", type=float, default=DEFAULT_RANGE_KAPPA)
    args = parser.parse_args()

    print(
        "M9 V1-index (Nifty vs India VIX) - methodology gate. "
        "Charter: docs/next/horizon-m9-range-monetization-charter.md"
    )
    flags = [
        _run_fold(fold, args.data_dir, args.vix_path, kappa=args.kappa)
        for fold in args.folds
    ]
    dual = all(flags) and len(flags) >= 2
    print(f"\nV1-index dual-fold={'PASS' if dual else 'FAIL'}")
    if dual:
        print("Proceed with M9-0 (single-name IV); name-level V1 still required.")
        sys.exit(0)
    print(
        "Track A methodology weak at the index — review before spending on "
        "single-name IV, or stop Track A."
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
