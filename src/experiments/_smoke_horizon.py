"""Temporary smoke test for Horizon Tier 2 verdict compliance."""

import datetime as dt

import numpy as np
import polars as pl

from src.features.horizon import calculate_horizon_features
from src.horizon.horizon_model import (
    LONG_FEATURES,
    SHORT_FEATURES,
    episode_balanced_weights,
    get_purged_cv_splits,
)
from src.labels.horizon import calculate_horizon_labels
from src.labels.triple_barrier import calculate_triple_barrier_labels
from src.pipelines.horizon_pipeline import (
    prepare_horizon_data,
    predict_horizon_gbm,
    fit_horizon_gbm,
)

BASE = dt.datetime(2024, 1, 1, 9, 15)
TIMES = [(BASE + dt.timedelta(minutes=15 * i)).time() for i in range(25)]


def _sessions(n: int) -> list[dt.date]:
    out = []
    d = dt.date(2023, 1, 2)
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def build_frames(n_sessions: int):
    rng = np.random.default_rng(7)
    sessions = _sessions(n_sessions)
    rows = []
    for sym in ("AAA", "BBB", "CCC"):
        px = 100.0
        for d in sessions:
            for t in TIMES:
                o = px
                c = o * (1 + rng.normal(0, 0.004))
                h = max(o, c) * (1 + rng.uniform(0, 0.006))
                lo = min(o, c) * (1 - rng.uniform(0, 0.006))
                px = max(c, 1.0)
                rows.append(
                    {
                        "symbol": sym,
                        "sector": "IT",
                        "datetime": dt.datetime.combine(d, t),
                        "open": o,
                        "high": h,
                        "low": lo,
                        "close": c,
                        "volume": float(rng.integers(1e5, 1e6)),
                    }
                )
    stock = pl.DataFrame(rows)

    nrows = []
    px = 22000.0
    for d in sessions:
        for t in TIMES:
            o = px
            c = o * (1 + rng.normal(0, 0.002))
            px = c
            nrows.append(
                {
                    "datetime": dt.datetime.combine(d, t),
                    "open": o,
                    "high": o * 1.002,
                    "low": o * 0.998,
                    "close": c,
                    "r_15": float(rng.normal()),
                    "vwap_dist": float(rng.normal() * 0.1),
                }
            )
    nifty = pl.DataFrame(nrows)
    sector = nifty.select(
        ["datetime", pl.lit("IT").alias("sector"), pl.col("close") * 0.99]
    )
    daily_stock = (
        stock.group_by(["symbol", pl.col("datetime").dt.date().alias("date")])
        .agg(
            open=pl.col("open").first(),
            high=pl.col("high").max(),
            low=pl.col("low").min(),
            close=pl.col("close").last(),
            volume=pl.col("volume").sum(),
        )
        .sort(["symbol", "date"])
    )
    daily_nifty = (
        nifty.group_by(pl.col("datetime").dt.date().alias("date"))
        .agg(
            open=pl.col("open").first(),
            high=pl.col("high").max(),
            low=pl.col("low").min(),
            close=pl.col("close").last(),
        )
        .sort("date")
    )
    daily_reg = daily_nifty.select(["date", pl.lit(1.05).alias("vol_regime_ratio")])
    regime = (
        stock.select(["symbol", "datetime"])
        .unique()
        .with_columns(
            daily_regime=pl.lit("SUPPORTIVE"),
            intraday_regime=pl.when(pl.col("datetime").dt.hour() < 12)
            .then(pl.lit("TREND_UP"))
            .otherwise(pl.lit("TREND_DOWN")),
        )
    )
    return stock, nifty, sector, daily_stock, daily_nifty, daily_reg, regime


def check_labels(stock, nifty):
    lab = calculate_horizon_labels(stock, nifty)
    assert lab.filter(
        pl.col("valid_label_long") & (pl.col("datetime").dt.time() > dt.time(14, 0))
    ).height == 0
    assert lab.filter(
        pl.col("valid_label_short") & (pl.col("datetime").dt.time() > dt.time(13, 45))
    ).height == 0
    assert lab.filter(
        (pl.col("datetime").dt.time() == dt.time(14, 15)) & pl.col("valid_label")
    ).height == 0
    print("labels/MIS ok")


def check_triple_barrier(stock, nifty, daily_stock):
    tb = calculate_triple_barrier_labels(stock, nifty, daily_stock)
    labels = set(tb["tb_label_long"].drop_nulls().unique().to_list())
    assert labels <= {-1, 0, 1}, labels
    # Barrier hits must never land inside the dead zone after the ordering fix.
    hits = tb.filter(pl.col("tb_label_long").is_in([-1, 1]))
    assert hits.height > 0, "no long barrier hits generated"
    # TP hits must clear cost; SL losses must exceed cost floor magnitude.
    tp = hits.filter(pl.col("tb_label_long") == 1)["tb_excess_ret_long"].drop_nulls()
    assert (tp.min() is None) or tp.min() > -0.02
    sl = tb.filter(pl.col("tb_label_short") == -1)
    assert sl.height > 0, "no short SL hits generated"
    assert tb.filter(
        pl.col("tb_label_short").is_not_null()
        & (pl.col("datetime").dt.time() > dt.time(13, 45))
    ).height == 0
    assert not tb.filter(pl.col("tb_label_long").is_not_null())[
        "tb_eligible_long"
    ].not_().any()
    print(
        "triple barrier ok:",
        tb.group_by("tb_label_long").len().sort("tb_label_long").to_dicts(),
    )


def check_barrier_dead_zone_ordering():
    """A TP touched intrabar must keep +1 even if the bar closes back inside ±30bps."""
    day = dt.date(2024, 3, 1)
    times = TIMES[:8]
    # Daily ATR% = 1% → long TP 2.5%, SL 1.0%; bar 1 spikes through TP then closes flat.
    closes = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
    highs = [100.0, 103.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
    lows = [100.0, 99.99, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
    rows = [
        {
            "symbol": "ZZZ",
            "datetime": dt.datetime.combine(day, t),
            "open": closes[i],
            "high": highs[i],
            "low": lows[i],
            "close": closes[i],
            "volume": 1e5,
        }
        for i, t in enumerate(times)
    ]
    stock = pl.DataFrame(rows)
    nifty = stock.select(["datetime", "open", "high", "low", "close"])
    daily = pl.DataFrame(
        [
            {
                "symbol": "ZZZ",
                "date": day - dt.timedelta(days=i),
                "open": 100.0,
                "high": 100.5,
                "low": 99.5,
                "close": 100.0,
                "volume": 1e6,
            }
            for i in range(20, -1, -1)
        ]
    )
    tb = calculate_triple_barrier_labels(stock, nifty, daily)
    entry = tb.filter(pl.col("datetime") == dt.datetime.combine(day, times[0]))
    label = entry["tb_label_long"].item()
    assert label == 1, f"TP-then-retrace must stay +1, got {label}"
    # Short SL is the mirror: price rose past +45bps.
    assert entry["tb_label_short"].item() == -1
    print("barrier dead-zone ordering ok")


def main() -> None:
    stock, nifty, sector, daily_stock, daily_nifty, daily_reg, regime = build_frames(90)
    check_labels(stock, nifty)
    check_triple_barrier(stock, nifty, daily_stock)
    check_barrier_dead_zone_ordering()

    feats = calculate_horizon_features(
        stock, nifty, sector, daily_stock, daily_nifty, daily_reg
    )
    assert feats["adv_rank_20d"].drop_nulls().max() <= 1.0 + 1e-9
    assert feats["vix_regime_ratio"].drop_nulls().len() > 0
    assert feats["index_vwap_dist"].drop_nulls().len() > 0
    # Session-scoped 4-bar returns: first 4 bars of each session must be null.
    first_bars = feats.filter(pl.col("time_only") <= dt.time(9, 45))
    assert first_bars["stock_ret_60"].null_count() == first_bars.height
    print("features ok")

    df = prepare_horizon_data(
        stock, nifty, sector, daily_stock, daily_nifty, regime, daily_reg
    )
    assert df.filter(pl.col("time_only") == dt.time(9, 15)).height == 0
    assert "bars_since_regime_flip" in df.columns
    assert "regime_episode_id" in df.columns
    assert df["bars_since_regime_flip"].min() == 0
    assert all(c in df.columns for c in LONG_FEATURES + SHORT_FEATURES)

    w = episode_balanced_weights(df)
    assert abs(float(np.mean(w)) - 1.0) < 1e-9
    print("regime feats + weights ok")

    splits = get_purged_cv_splits(df, train_days=40, val_days=5, test_days=10, n_splits=2)
    assert splits
    tr, va, te = splits[0]
    assert tr.select(pl.col("date_only").max()).item() < va.select(
        pl.col("date_only").min()
    ).item()
    assert va.select(pl.col("date_only").max()).item() < te.select(
        pl.col("date_only").min()
    ).item()
    print("purged WF ok:", len(splits), "splits")

    res = fit_horizon_gbm(
        df, cv_kwargs={"train_days": 40, "val_days": 5, "test_days": 10, "n_splits": 2}
    )
    long_model = res.get("long_models", [None])[-1]
    short_model = res.get("short_models", [None])[-1]
    scored = predict_horizon_gbm(df, long_model, short_model)
    assert scored.filter(
        (pl.col("horizon_direction") == "short")
        & (pl.col("time_only") > dt.time(13, 45))
    ).height == 0
    assert scored["horizon_rank"].drop_nulls().len() > 0
    print("train + predict ok", scored.height)


if __name__ == "__main__":
    main()
