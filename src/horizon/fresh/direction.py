"""Stage C directional features — where price is and which way it is moving.

M5 trained the first-hit head on volatility/range features only, which are
symmetric in the barrier race: they raise P(TP) and P(SL) together and cannot
express a Long edge. Everything here is signed and vol-normalized so the same
column means the same thing on a 200-rupee name and a 5,000-rupee name.

Causality: every column uses the decision bar and earlier bars only.
"""

from __future__ import annotations

import polars as pl

from src.features.core import vwap as vwap_expr

DIRECTION_FEATURES: tuple[str, ...] = (
    "close_vs_vwap_atr",
    "vwap_slope_atr",
    "pos_in_day_range",
    "ret_1b_atr",
    "ret_3b_atr",
    "ret_6b_atr",
    "above_orb_high_atr",
    "above_prior_day_high_atr",
    "consec_up_bars",
    "upper_wick_share",
    "close_loc_in_bar",
    "nifty_ret_6b_bps",
    "rel_strength_6b_atr",
    "xs_rank_ret_6b",
)

# Cross-sectional ranks of vol state. Levels shift between folds (2018 vs 2019
# vol regimes); within-day ranks do not, so the head stops extrapolating.
XS_VOL_FEATURES: tuple[str, ...] = (
    "xs_rank_rv_5d",
    "xs_rank_open_30m_range",
    "xs_rank_range_q25",
)

_MOM_LOOKBACK = 6


def attach_direction_features(
    bars: pl.DataFrame,
    nifty: pl.DataFrame,
    *,
    atr_col: str = "atr_pct",
) -> pl.DataFrame:
    """
    Signed, ATR-normalized directional block on a 15m panel.

    ``bars`` must already carry ``atr_col`` (TOD-normalized 15m range) from the
    fresh labeler, plus ``symbol``/``date`` keys. ``nifty`` supplies index closes
    for market direction and relative strength.
    """
    df = bars.sort(["symbol", "date"]).with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
    )
    atr = pl.max_horizontal(pl.col(atr_col), pl.lit(1e-4))

    df = df.with_columns(
        _vwap=vwap_expr().over(["symbol", "date_only"]),
        _day_hi=pl.col("high").cum_max().over(["symbol", "date_only"]),
        _day_lo=pl.col("low").cum_min().over(["symbol", "date_only"]),
        _up=(pl.col("close") > pl.col("close").shift(1).over("symbol")).cast(pl.Int32),
    )

    # ORB high (first two 15m bars) and prior-session high — both causal.
    orb = (
        df.filter(pl.col("time_only") <= pl.lit("09:45:00").str.to_time())
        .group_by(["symbol", "date_only"])
        .agg(_orb_high=pl.col("high").max())
    )
    prior_high = (
        df.group_by(["symbol", "date_only"])
        .agg(_day_high_full=pl.col("high").max())
        .sort(["symbol", "date_only"])
        .with_columns(_prior_day_high=pl.col("_day_high_full").shift(1).over("symbol"))
        .drop("_day_high_full")
    )
    nifty_mom = (
        nifty.sort("date")
        .select(["date", pl.col("close").alias("_nifty_close")])
        .with_columns(
            _nifty_ret_6b=pl.col("_nifty_close") / pl.col("_nifty_close").shift(_MOM_LOOKBACK)
            - 1.0,
        )
    )

    df = (
        df.join(orb, on=["symbol", "date_only"], how="left")
        .join(prior_high, on=["symbol", "date_only"], how="left")
        .join(nifty_mom, on="date", how="left")
    )

    ret_6b = pl.col("close") / pl.col("close").shift(_MOM_LOOKBACK).over("symbol") - 1.0
    day_span = pl.max_horizontal(pl.col("_day_hi") - pl.col("_day_lo"), pl.lit(1e-9))
    bar_span = pl.max_horizontal(pl.col("high") - pl.col("low"), pl.lit(1e-9))

    df = df.with_columns(
        close_vs_vwap_atr=(pl.col("close") / pl.col("_vwap") - 1.0) / atr,
        vwap_slope_atr=(
            pl.col("_vwap") / pl.col("_vwap").shift(3).over(["symbol", "date_only"]) - 1.0
        )
        / atr,
        pos_in_day_range=(pl.col("close") - pl.col("_day_lo")) / day_span,
        ret_1b_atr=(pl.col("close") / pl.col("close").shift(1).over("symbol") - 1.0) / atr,
        ret_3b_atr=(pl.col("close") / pl.col("close").shift(3).over("symbol") - 1.0) / atr,
        ret_6b_atr=ret_6b / atr,
        above_orb_high_atr=(pl.col("close") / pl.col("_orb_high") - 1.0) / atr,
        above_prior_day_high_atr=(pl.col("close") / pl.col("_prior_day_high") - 1.0) / atr,
        consec_up_bars=pl.col("_up")
        .rolling_sum(3, min_samples=3)
        .over(["symbol", "date_only"])
        .cast(pl.Float64),
        upper_wick_share=(pl.col("high") - pl.col("close")) / bar_span,
        close_loc_in_bar=(pl.col("close") - pl.col("low")) / bar_span,
        nifty_ret_6b_bps=pl.col("_nifty_ret_6b") * 1e4,
        rel_strength_6b_atr=(ret_6b - pl.col("_nifty_ret_6b")) / atr,
    )

    # Cross-sectional rank of momentum within the bar: relative strength needs a
    # peer group, not an absolute level.
    df = df.with_columns(
        xs_rank_ret_6b=pl.col("ret_6b_atr").rank(method="average").over("date")
        / pl.len().over("date"),
    )
    return df.drop(
        [c for c in ("_vwap", "_day_hi", "_day_lo", "_up", "_orb_high", "_prior_day_high",
                     "_nifty_close", "_nifty_ret_6b") if c in df.columns]
    )


def attach_cross_sectional_vol_ranks(panel: pl.DataFrame) -> pl.DataFrame:
    """Within-bar ranks of vol-state columns (level-shift immune)."""
    n = pl.len().over("date")
    return panel.with_columns(
        xs_rank_rv_5d=pl.col("rv_5d").rank(method="average").over("date") / n,
        xs_rank_open_30m_range=pl.col("open_30m_range").rank(method="average").over("date")
        / n,
        xs_rank_range_q25=pl.col("range_q25").rank(method="average").over("date") / n,
    )
