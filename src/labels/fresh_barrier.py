"""Fresh barrier labels — absolute path first; excess as report-only companion.

Production ``triple_barrier.py`` floors / H=6 stay frozen until M8.
This module is the fresh M1/M5 label surface: ``ev_net_abs`` / ``ev_net_excess``.

M5R-b (blueprint §9.1): first-hit on 1m bars + symmetric penetration so K4 is
not biased by 15m dual-touch→SL ties or TP-only penetration.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import numpy as np
import polars as pl

from src.horizon.session import MIS_EXIT_BAR_END, last_entry_for_horizon
from src.labels.triple_barrier import (
    DEAD_ZONE,
    ROUND_TRIP_COST,
    SL_FLOOR,
    TOD_LOOKBACK_DAYS,
    TP_FLOOR_LONG,
    TP_PENETRATION,
)
from src.regime.intraday import NSE_OPEN_BLEED_BAR
from src.utils.eval_common import H_BARS


@dataclass(frozen=True)
class FreshLongGeometry:
    """Parameterized Long barriers for fresh labels (not production ship floors)."""

    name: str
    horizon_bars: int
    tp_floor: float
    sl_floor: float
    tp_vol_mult: float
    sl_vol_mult: float
    mis_vertical: bool = False  # True → race until MIS flatten (M5)


# Production-shaped geometry for M1 absolute-vs-excess / selection-ceiling baselines.
PROD_LONG_GEOMETRY = FreshLongGeometry(
    name="prod_long_60_30_h6",
    horizon_bars=H_BARS,
    tp_floor=TP_FLOOR_LONG,
    sl_floor=SL_FLOOR,
    tp_vol_mult=2.5,
    sl_vol_mult=1.0,
    mis_vertical=False,
)

# M5 Stage C: MIS-vertical race with ~15× cost span (200/100) when atr allows.
MIS_WIDE_LONG_GEOMETRY = FreshLongGeometry(
    name="mis_wide_200_100",
    horizon_bars=8,  # last entry ~13:15 so MIS race can resolve
    tp_floor=10 * ROUND_TRIP_COST,  # 200 bps
    sl_floor=5 * ROUND_TRIP_COST,  # 100 bps
    tp_vol_mult=3.0,
    sl_vol_mult=1.5,
    mis_vertical=True,
)

# M5P-b / blueprint §1.6: vertical-only for thin-drift sleeves.
# Horizontal TP is set unreachable; SL is a wide disaster stop. Exit is MIS
# flatten unless the disaster stop fires. Risk control lives in Stage D sizing.
MIS_VERTICAL_ONLY_LONG_GEOMETRY = FreshLongGeometry(
    name="mis_vertical_only_disaster_sl",
    horizon_bars=8,
    tp_floor=50 * ROUND_TRIP_COST,  # 1000 bps — not a real target
    sl_floor=25 * ROUND_TRIP_COST,  # 500 bps disaster stop
    tp_vol_mult=100.0,  # keep TP above any realistic atr path
    sl_vol_mult=5.0,
    mis_vertical=True,
)

# Short sleeve uses the same barrier widths; path sign is applied by the caller
# (side_drift / short labeler). Named so harnesses do not silently reuse Long 200/100.
MIS_VERTICAL_ONLY_SHORT_GEOMETRY = FreshLongGeometry(
    name="mis_vertical_only_disaster_sl_short",
    horizon_bars=8,
    tp_floor=50 * ROUND_TRIP_COST,
    sl_floor=25 * ROUND_TRIP_COST,
    tp_vol_mult=100.0,
    sl_vol_mult=5.0,
    mis_vertical=True,
)


def calculate_fresh_long_labels(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame | None,
    geometry: FreshLongGeometry = PROD_LONG_GEOMETRY,
    *,
    cost: float = ROUND_TRIP_COST,
    tp_penetration: float = TP_PENETRATION,
    sl_penetration: float = 0.0,
    mis_exit_bar_end: dt.time = MIS_EXIT_BAR_END,
    tod_lookback_days: int = TOD_LOOKBACK_DAYS,
) -> pl.DataFrame:
    """
    Long-only first-hit labels with explicit ``ev_net_abs`` (and optional excess).

    When ``nifty_df`` is provided, also emits ``ev_net_excess`` on the same path.
    When ``geometry.mis_vertical``, vertical is MIS flatten (variable H), not fixed bars.

    Default penetration is asymmetric (TP only) to match the M5/M5R ledger.
    Pass ``sl_penetration=tp_penetration`` for the M5R-b symmetric reading.
    Emits ``dual_touch_15m`` when the first-hit 15m bar touches both barriers.
    """
    h_bars = geometry.horizon_bars
    long_last_entry = last_entry_for_horizon(h_bars, short=False)

    stock_df = stock_df.sort(["symbol", "date"])
    df = stock_df.with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
        entry_time=pl.col("date").dt.time(),
        range_pct=(
            (pl.col("high") - pl.col("low"))
            / pl.col("close").shift(1).over("symbol")
        ),
    )

    min_periods = max(10, tod_lookback_days // 4)
    df = (
        df.sort(["symbol", "time_only", "date_only"])
        .with_columns(
            rv_15_mean=pl.col("range_pct")
            .shift(1)
            .rolling_mean(window_size=tod_lookback_days, min_samples=min_periods)
            .over(["symbol", "time_only"]),
        )
        .sort(["symbol", "date"])
    )

    df = df.with_columns(
        atr_pct=pl.col("rv_15_mean"),
        entry_px=pl.col("close"),
    ).with_columns(
        tp_vol=geometry.tp_vol_mult * pl.col("atr_pct"),
        tp_w=pl.max_horizontal(
            geometry.tp_vol_mult * pl.col("atr_pct"),
            pl.lit(geometry.tp_floor),
        ),
        sl_w=pl.max_horizontal(
            geometry.sl_vol_mult * pl.col("atr_pct"),
            pl.lit(geometry.sl_floor),
        ),
    ).with_columns(
        tb_eligible=(
            pl.col("atr_pct").is_finite()
            if geometry.mis_vertical
            else (pl.col("tp_vol") >= geometry.tp_floor)
        ),
        entry_ok=(
            (pl.col("entry_time") > NSE_OPEN_BLEED_BAR)
            & (pl.col("entry_time") <= long_last_entry)
        ),
    )

    if nifty_df is not None:
        nifty = nifty_df.select(
            [
                pl.col("date"),
                pl.col("close").alias("nifty_close"),
            ]
        )
        df = df.join(nifty, on="date", how="left").with_columns(
            entry_nifty=pl.col("nifty_close"),
        )

    # Max look-ahead: fixed H or remaining bars to MIS on the same session.
    max_h = h_bars
    if geometry.mis_vertical:
        # 15m bars from ~09:45 to 15:15 → up to ~22 bars; cap for column fan-out.
        max_h = 22

    for h in range(1, max_h + 1):
        df = df.with_columns(
            **{
                f"_hi_{h}": pl.col("high").shift(-h).over("symbol"),
                f"_lo_{h}": pl.col("low").shift(-h).over("symbol"),
                f"_c_{h}": pl.col("close").shift(-h).over("symbol"),
                f"_t_{h}": pl.col("date").shift(-h).dt.time().over("symbol"),
                f"_d_{h}": pl.col("date").shift(-h).dt.date().over("symbol"),
            }
        )
        if nifty_df is not None:
            df = df.with_columns(
                **{
                    f"_nc_{h}": pl.col("nifty_close").shift(-h).over("symbol"),
                }
            )

    default_exit = max_h if geometry.mis_vertical else h_bars
    df = df.with_columns(
        _exit_h=pl.lit(default_exit, dtype=pl.Int32),
        _event=pl.lit(0, dtype=pl.Int8),
        dual_touch_15m=pl.lit(False),
    )

    for h in range(1, max_h + 1):
        in_session = (
            (pl.col(f"_d_{h}") == pl.col("date_only"))
            & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
            & pl.col(f"_c_{h}").is_not_null()
        )
        if not geometry.mis_vertical:
            in_session = in_session & (pl.lit(h) <= h_bars)
        long_tp = in_session & (
            pl.col(f"_hi_{h}")
            >= pl.col("entry_px") * (1.0 + pl.col("tp_w") + tp_penetration)
        )
        long_sl = in_session & (
            pl.col(f"_lo_{h}")
            <= pl.col("entry_px") * (1.0 - pl.col("sl_w") - sl_penetration)
        )
        still = pl.col("_event") == 0
        # Same-bar TP+SL → SL first (15m conservatism); flag the ambiguity.
        df = df.with_columns(
            dual_touch_15m=pl.when(still & long_sl & long_tp)
            .then(True)
            .otherwise(pl.col("dual_touch_15m")),
            _event=pl.when(still & long_sl)
            .then(pl.lit(-1, dtype=pl.Int8))
            .when(still & long_tp)
            .then(pl.lit(1, dtype=pl.Int8))
            .otherwise(pl.col("_event")),
            _exit_h=pl.when(still & (long_sl | long_tp))
            .then(pl.lit(h, dtype=pl.Int32))
            .otherwise(pl.col("_exit_h")),
        )

    exit_close = pl.lit(None, dtype=pl.Float64)
    path_ok = pl.lit(False)
    exit_nifty = pl.lit(None, dtype=pl.Float64)
    for h in range(1, max_h + 1):
        in_session = (
            (pl.col(f"_d_{h}") == pl.col("date_only"))
            & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
            & pl.col(f"_c_{h}").is_not_null()
        )
        if not geometry.mis_vertical:
            in_session = in_session & (pl.lit(h) <= h_bars)
        exit_close = (
            pl.when((pl.col("_exit_h") == h) & in_session)
            .then(pl.col(f"_c_{h}"))
            .otherwise(exit_close)
        )
        path_ok = pl.when((pl.col("_exit_h") == h) & in_session).then(True).otherwise(
            path_ok
        )
        if nifty_df is not None:
            exit_nifty = (
                pl.when((pl.col("_exit_h") == h) & in_session)
                .then(pl.col(f"_nc_{h}"))
                .otherwise(exit_nifty)
            )

    df = df.with_columns(
        _exit_close=exit_close,
        _ok=path_ok,
        _exit_nifty=exit_nifty if nifty_df is not None else pl.lit(None),
    ).with_columns(
        path_ret=pl.when(pl.col("_event") == 1)
        .then(pl.col("tp_w"))
        .when(pl.col("_event") == -1)
        .then(-pl.col("sl_w"))
        .otherwise(pl.col("_exit_close") / pl.col("entry_px") - 1.0),
    )

    # Dead zone on timeouts only (match production spirit).
    label = (
        pl.when(~pl.col("_ok"))
        .then(None)
        .when(pl.col("_event") != 0)
        .then(pl.col("_event"))
        .when(pl.col("path_ret").abs() <= DEAD_ZONE)
        .then(pl.lit(0, dtype=pl.Int8))
        .otherwise(pl.lit(0, dtype=pl.Int8))
    )

    df = df.with_columns(
        tb_label=pl.when(pl.col("_ok")).then(label).otherwise(None),
        ev_net_abs=pl.when(pl.col("_ok"))
        .then(pl.col("path_ret") - cost)
        .otherwise(None),
    )

    if nifty_df is not None:
        nifty_ret = pl.col("_exit_nifty") / pl.col("entry_nifty") - 1.0
        df = df.with_columns(
            nifty_ret=nifty_ret,
            ev_net_excess=pl.when(pl.col("_ok"))
            .then(pl.col("path_ret") - nifty_ret - cost)
            .otherwise(None),
        )
    else:
        df = df.with_columns(
            nifty_ret=pl.lit(None, dtype=pl.Float64),
            ev_net_excess=pl.lit(None, dtype=pl.Float64),
        )

    cols = [
        "symbol",
        "date",
        "date_only",
        "time_only",
        "atr_pct",
        "entry_px",
        "tp_w",
        "sl_w",
        "tb_eligible",
        "entry_ok",
        "tb_label",
        "path_ret",
        "ev_net_abs",
        "ev_net_excess",
        "nifty_ret",
        "dual_touch_15m",
        "_exit_h",
    ]
    return df.select([c for c in cols if c in df.columns]).rename(
        {"_exit_h": "tb_exit_h"}
    )


def dual_touch_share(labeled: pl.DataFrame) -> dict[str, float | int]:
    """Share of labeled rows whose first-hit 15m bar touched both barriers."""
    ok = labeled.filter(pl.col("tb_label").is_not_null())
    if ok.height == 0:
        return {"n": 0, "dual_touch_share": float("nan"), "n_dual": 0}
    n_dual = int(ok["dual_touch_15m"].sum())
    return {
        "n": ok.height,
        "n_dual": n_dual,
        "dual_touch_share": n_dual / ok.height,
    }


def resolve_fresh_long_first_hit_1m(
    decisions: pl.DataFrame,
    bars_1m: pl.DataFrame,
    *,
    cost: float = ROUND_TRIP_COST,
    penetration: float = TP_PENETRATION,
    mis_exit_bar_end: dt.time = MIS_EXIT_BAR_END,
    max_hold_minutes: int | None = None,
) -> pl.DataFrame:
    """
    Overwrite path outcomes by walking 1m bars after each 15m decision stamp.

    Penetration is applied **symmetrically** to TP and SL (blueprint §9.1).
    Residual same-1m dual touches still break to SL and are counted in
    ``dual_touch_1m``. Vertical matches the 15m MIS stamp (``mis_exit_bar_end``).

    ``decisions`` must carry ``symbol``, ``date``, ``entry_px``, ``tp_w``, ``sl_w``.
    ``bars_1m`` must carry ``symbol``, ``date``, ``high``, ``low``, ``close``.
    """
    need = {"symbol", "date", "entry_px", "tp_w", "sl_w"}
    missing = need - set(decisions.columns)
    if missing:
        raise ValueError(f"decisions missing columns: {sorted(missing)}")

    by_sym: dict[str, tuple[list[dt.datetime], np.ndarray, np.ndarray, np.ndarray]] = {}
    for g in bars_1m.sort(["symbol", "date"]).partition_by("symbol", maintain_order=True):
        by_sym[g["symbol"][0]] = (
            g["date"].to_list(),
            g["high"].to_numpy().astype(np.float64),
            g["low"].to_numpy().astype(np.float64),
            g["close"].to_numpy().astype(np.float64),
        )

    n = decisions.height
    label_out: list[int | None] = [None] * n
    path_out: list[float | None] = [None] * n
    exit_min = np.full(n, -1, dtype=np.int32)
    dual_1m = np.zeros(n, dtype=bool)

    for i, row in enumerate(
        decisions.select(["symbol", "date", "entry_px", "tp_w", "sl_w"]).iter_rows(
            named=True
        )
    ):
        packed = by_sym.get(row["symbol"])
        if packed is None:
            continue
        ts_list, hi, lo, cl = packed
        decision_ts: dt.datetime = row["date"]
        start = _bisect_right_datetime(ts_list, decision_ts)
        if start >= len(ts_list):
            continue

        entry = float(row["entry_px"])
        tp_px = entry * (1.0 + float(row["tp_w"]) + penetration)
        sl_px = entry * (1.0 - float(row["sl_w"]) - penetration)
        day = decision_ts.date()
        deadline = (
            decision_ts + dt.timedelta(minutes=max_hold_minutes)
            if max_hold_minutes is not None
            else None
        )

        event = 0
        dual = False
        exit_i = -1
        for j in range(start, len(ts_list)):
            ts = ts_list[j]
            if ts.date() != day or ts.time() > mis_exit_bar_end:
                break
            if deadline is not None and ts > deadline:
                break
            exit_i = j
            hit_sl = lo[j] <= sl_px
            hit_tp = hi[j] >= tp_px
            if hit_sl and hit_tp:
                dual = True
                event = -1
                break
            if hit_sl:
                event = -1
                break
            if hit_tp:
                event = 1
                break

        if exit_i < start:
            continue

        dual_1m[i] = dual
        exit_min[i] = exit_i - start + 1
        if event == 1:
            label_out[i] = 1
            path_out[i] = float(row["tp_w"])
        elif event == -1:
            label_out[i] = -1
            path_out[i] = -float(row["sl_w"])
        else:
            path_out[i] = cl[exit_i] / entry - 1.0
            label_out[i] = 0

    return decisions.with_columns(
        tb_label=pl.Series(name="tb_label", values=label_out, dtype=pl.Int8),
        path_ret=pl.Series(name="path_ret", values=path_out, dtype=pl.Float64),
        tb_exit_h=pl.Series(name="tb_exit_h", values=exit_min, dtype=pl.Int32),
        dual_touch_1m=pl.Series(name="dual_touch_1m", values=dual_1m, dtype=pl.Boolean),
    ).with_columns(
        ev_net_abs=pl.when(pl.col("tb_label").is_not_null())
        .then(pl.col("path_ret") - cost)
        .otherwise(None),
    )


def _bisect_right_datetime(ts_list: list[dt.datetime], value: dt.datetime) -> int:
    """Return insertion index after any existing entries of ``value``."""
    lo, hi = 0, len(ts_list)
    while lo < hi:
        mid = (lo + hi) // 2
        if ts_list[mid] <= value:
            lo = mid + 1
        else:
            hi = mid
    return lo


def absolute_excess_sign_disagreement(labeled: pl.DataFrame) -> dict[str, float | int]:
    """Rate at which ``ev_net_abs`` and ``ev_net_excess`` disagree in sign."""
    both = labeled.filter(
        pl.col("ev_net_abs").is_not_null() & pl.col("ev_net_excess").is_not_null()
    )
    if both.height == 0:
        return {"n": 0, "disagree_rate": float("nan")}
    disagree = both.filter(
        (pl.col("ev_net_abs") > 0) != (pl.col("ev_net_excess") > 0)
    )
    return {
        "n": both.height,
        "disagree_rate": disagree.height / both.height,
        "n_disagree": disagree.height,
    }
