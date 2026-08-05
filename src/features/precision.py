"""Tier 3 Precision 1-minute timing features (Long / Short)."""

import datetime as dt

import polars as pl

# Keep local to avoid features → precision.rules → LightGBM import chain.
AFTERNOON_COVER_START = dt.time(13, 0)


def calculate_precision_features(
    stock_1m: pl.DataFrame,
    nifty_1m: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """
    Causal 1m timing features for Precision entry rules.

    Inputs:
    - stock_1m: 1m OHLCV (date, open, high, low, close, volume, symbol)
    - nifty_1m: optional 1m index OHLCV for afternoon cover (declining index rv)

    TB widths / horizon rank / dist_to_* are attached at the decision-bar join
    in the pipeline — this builder stays pure 1m path quality.
    """
    df = stock_1m.sort(["symbol", "date"]).with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
    )

    session = ["symbol", "date_only"]

    # Session VWAP (typical price × volume).
    df = df.with_columns(
        typ_price=(pl.col("high") + pl.col("low") + pl.col("close")) / 3.0,
    ).with_columns(
        cum_vol=pl.col("volume").cum_sum().over(session),
        cum_pv=(pl.col("typ_price") * pl.col("volume")).cum_sum().over(session),
    ).with_columns(
        vwap=pl.col("cum_pv") / pl.col("cum_vol"),
    ).with_columns(
        vwap_dist_1m=(pl.col("close") - pl.col("vwap")) / pl.col("vwap"),
        vwap_dist_bps=((pl.col("close") - pl.col("vwap")) / pl.col("vwap")) * 1e4,
        spread_proxy_bps=((pl.col("high") - pl.col("low")) / pl.col("close")) * 1e4,
    )

    # 1m true range → short ATR for compression vs frozen TB atr_pct.
    df = df.with_columns(
        tr_1m=pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - pl.col("close").shift(1).over(session)).abs(),
            (pl.col("low") - pl.col("close").shift(1).over(session)).abs(),
        ),
        up_close=pl.col("close") > pl.col("close").shift(1).over(session),
        down_close=pl.col("close") < pl.col("close").shift(1).over(session),
    ).with_columns(
        atr_1m_5=pl.col("tr_1m").rolling_mean(window_size=5).over(session),
        # Micro EMA for short bounce detection.
        ema_1m_5=pl.col("close").ewm_mean(span=5, adjust=False).over(session),
        prior_high=pl.col("high").shift(1).over(session),
        prior_low=pl.col("low").shift(1).over(session),
    )

    # Consecutive green / red closes (cap 5), reset on opposite print.
    df = df.with_columns(
        _green_grp=(~pl.col("up_close").fill_null(False))
        .cast(pl.Int32)
        .cum_sum()
        .over(session),
        _red_grp=(~pl.col("down_close").fill_null(False))
        .cast(pl.Int32)
        .cum_sum()
        .over(session),
    ).with_columns(
        consec_green_1m=pl.when(pl.col("up_close").fill_null(False))
        .then(
            pl.col("up_close")
            .cast(pl.Int32)
            .cum_sum()
            .over(session + ["_green_grp"])
            .clip(upper_bound=5)
        )
        .otherwise(0)
        .cast(pl.Int32),
        consec_red_1m=pl.when(pl.col("down_close").fill_null(False))
        .then(
            pl.col("down_close")
            .cast(pl.Int32)
            .cum_sum()
            .over(session + ["_red_grp"])
            .clip(upper_bound=5)
        )
        .otherwise(0)
        .cast(pl.Int32),
    )

    # Micro swing: last 5-bar high/low for pullback / bounce depth.
    df = df.with_columns(
        swing_high_5=pl.col("high").rolling_max(window_size=5).over(session),
        swing_low_5=pl.col("low").rolling_min(window_size=5).over(session),
    ).with_columns(
        _swing_range=(pl.col("swing_high_5") - pl.col("swing_low_5")).clip(
            lower_bound=1e-9
        ),
    ).with_columns(
        # % retrace of last up-leg (0 = at high, 1 = full giveback to swing low).
        m1_pullback_depth=(pl.col("swing_high_5") - pl.col("close"))
        / pl.col("_swing_range"),
        # % retrace of last down-leg (bounce off lows).
        m1_bounce_depth=(pl.col("close") - pl.col("swing_low_5"))
        / pl.col("_swing_range"),
        # Bps above micro EMA (short bounce confirmation).
        m1_bounce_bps=((pl.col("close") - pl.col("ema_1m_5")) / pl.col("ema_1m_5"))
        * 1e4,
        reclaim_prior_high=pl.col("close") > pl.col("prior_high"),
        break_prior_low=pl.col("close") < pl.col("prior_low"),
    )

    # Local realized range (rv proxy) for afternoon cover.
    df = df.with_columns(
        rv_1m=pl.col("tr_1m") / pl.col("close"),
    ).with_columns(
        rv_1m_mean_5=pl.col("rv_1m").rolling_mean(window_size=5).over(session),
    )

    if nifty_1m is not None and nifty_1m.height > 0:
        # Session-scoped roll so the 5-bar mean does not bleed across overnight gaps.
        nifty = (
            nifty_1m.sort("date")
            .with_columns(
                date_only=pl.col("date").dt.date(),
                nifty_rv=(pl.col("high") - pl.col("low")) / pl.col("close"),
            )
            .with_columns(
                nifty_rv_mean_5=pl.col("nifty_rv")
                .rolling_mean(window_size=5)
                .over("date_only"),
            )
            .select(["date", "nifty_rv", "nifty_rv_mean_5"])
        )
        df = df.join(nifty, on="date", how="left")
        declining_index = pl.col("nifty_rv") < pl.col("nifty_rv_mean_5")
    else:
        declining_index = pl.lit(True)

    declining_stock = pl.col("rv_1m") < pl.col("rv_1m_mean_5")
    df = df.with_columns(
        afternoon_cover_risk=(
            (pl.col("time_only") >= AFTERNOON_COVER_START)
            & declining_stock
            & declining_index
        ),
    )

    return df.drop(
        [
            "typ_price",
            "cum_vol",
            "cum_pv",
            "tr_1m",
            "up_close",
            "down_close",
            "_green_grp",
            "_red_grp",
            "_swing_range",
        ]
    )
