"""Triple-barrier path labels for Tier 2 meta-labeling / entry quality."""

import datetime as dt

import polars as pl

from src.horizon.session import (
    LONG_LAST_ENTRY,
    MIS_EXIT_BAR_END,
    SHORT_LAST_ENTRY,
)
from src.utils.eval_common import H_BARS

# Friction-realism input (signed); NOT an economics-clearing / ship threshold.
ROUND_TRIP_COST = 0.0020  # 20 bps — cost charter signed working c*
ARCHIVE_ROUND_TRIP_COST = 0.0030  # 30 bps stress companion (peek-1 dual readout)
TP_FLOOR_LONG = 3 * ROUND_TRIP_COST  # 60 bps — T1 peek measured; not merged (see stop-memo)
SL_FLOOR = 1.5 * ROUND_TRIP_COST  # 30 bps
TP_FLOOR_SHORT = 2.5 * ROUND_TRIP_COST  # 50 bps
# TP-floor Step 0 candidate (50 bps). Production Long floor stays TP_FLOOR_LONG.
TP_FLOOR_LONG_CANDIDATE = 2.5 * ROUND_TRIP_COST  # 50 bps
DEAD_ZONE = ROUND_TRIP_COST
# Barriers are not assumed to fill on an exact high/low touch: a take-profit must be
# penetrated by this much, while a stop triggers on touch (conservative both ways).
TP_PENETRATION = 0.0002  # 2 bps
# Causal TOD lookback — match Horizon stock_rv_15 denominator.
TOD_LOOKBACK_DAYS = 60
BPS = 1e4


def calculate_triple_barrier_labels(
    stock_df: pl.DataFrame,
    nifty_df: pl.DataFrame,
    horizon_bars: int = H_BARS,
    cost: float = ROUND_TRIP_COST,
    tp_penetration: float = TP_PENETRATION,
    mis_exit_bar_end: dt.time = MIS_EXIT_BAR_END,
    long_last_entry: dt.time = LONG_LAST_ENTRY,
    short_last_entry: dt.time = SHORT_LAST_ENTRY,
    tod_lookback_days: int = TOD_LOOKBACK_DAYS,
) -> pl.DataFrame:
    """
    Hard vertical primary H=6, TOD-rv-scaled TP/SL with cost floors, net-of-cost labels.

    Vol scale (`atr_pct`) is causal same-clock **absolute** `rv_15_mean`
    (typical (H−L)/close for that TOD bucket) — not daily ATR and not the
    dimensionless `stock_rv_15` intensity ratio.

    Long:  TP = max(2.5×atr_pct, 60bps), SL = max(1.0×atr_pct, 30bps)
    Short: TP = max(2.0×atr_pct, 50bps), SL = max(0.9×atr_pct, 30bps)

    Coding: +1 TP-first, -1 SL-first, 0 timeout. The ±cost dead zone applies to
    timeout resolutions only — a barrier hit keeps its sign.

    Barrier hits realize at the barrier price; timeouts realize at the bar `t+H`
    close. `tb_excess_ret_*` is net of `cost` and excess of Nifty over the same
    window (Nifty leg uses the exit bar close — finest resolution available at 15m).
    Entries whose vol-based TP cannot clear the cost floor are marked ineligible.

    Peak-bar / giveback / exit-h columns are report-only diagnostics (MFE-decay
    Step 0). Absolute MFE bps + mfe50-first-bar support TP-floor Step 0.
    Rejected E2 giveback-exit policy is not in this path — see stop-memo.
    """
    stock_df = stock_df.sort(["symbol", "date"])
    nifty_df = nifty_df.sort("date")

    df = (
        stock_df.with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
            entry_time=pl.col("date").dt.time(),
            # Match Horizon range_pct: range vs prior close (lookahead-safe).
            range_pct=(
                (pl.col("high") - pl.col("low"))
                / pl.col("close").shift(1).over("symbol")
            ),
        )
        .join(
            nifty_df.select(["date", pl.col("close").alias("nifty_close")]),
            on="date",
            how="left",
        )
    )

    # Causal TOD baseline: prior sessions only within (symbol, clock bucket).
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
        # Absolute TOD typical range % — barrier denominator (not stock_rv_15).
        atr_pct=pl.col("rv_15_mean"),
        entry_px=pl.col("close"),
        entry_nifty=pl.col("nifty_close"),
    ).with_columns(
        long_tp_vol=2.5 * pl.col("atr_pct"),
        short_tp_vol=2.0 * pl.col("atr_pct"),
        long_tp_w=pl.max_horizontal(2.5 * pl.col("atr_pct"), pl.lit(TP_FLOOR_LONG)),
        long_sl_w=pl.max_horizontal(1.0 * pl.col("atr_pct"), pl.lit(SL_FLOOR)),
        short_tp_w=pl.max_horizontal(2.0 * pl.col("atr_pct"), pl.lit(TP_FLOOR_SHORT)),
        short_sl_w=pl.max_horizontal(0.9 * pl.col("atr_pct"), pl.lit(SL_FLOOR)),
    ).with_columns(
        tb_eligible_long=pl.col("long_tp_vol") >= TP_FLOOR_LONG,
        tb_eligible_short=pl.col("short_tp_vol") >= TP_FLOOR_SHORT,
    )

    for h in range(1, horizon_bars + 1):
        df = df.with_columns(
            **{
                f"_hi_{h}": pl.col("high").shift(-h).over("symbol"),
                f"_lo_{h}": pl.col("low").shift(-h).over("symbol"),
                f"_c_{h}": pl.col("close").shift(-h).over("symbol"),
                f"_nc_{h}": pl.col("nifty_close").shift(-h).over("symbol"),
                f"_t_{h}": pl.col("date").shift(-h).dt.time().over("symbol"),
                f"_d_{h}": pl.col("date").shift(-h).dt.date().over("symbol"),
            }
        )

    df = df.with_columns(
        _long_exit_h=pl.lit(horizon_bars, dtype=pl.Int32),
        _short_exit_h=pl.lit(horizon_bars, dtype=pl.Int32),
        _long_event=pl.lit(0, dtype=pl.Int8),
        _short_event=pl.lit(0, dtype=pl.Int8),
    )

    for h in range(1, horizon_bars + 1):
        in_session = (
            (pl.col(f"_d_{h}") == pl.col("date_only"))
            & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
            & pl.col(f"_c_{h}").is_not_null()
        )
        long_tp = in_session & (
            pl.col(f"_hi_{h}")
            >= pl.col("entry_px") * (1.0 + pl.col("long_tp_w") + tp_penetration)
        )
        long_sl = in_session & (
            pl.col(f"_lo_{h}") <= pl.col("entry_px") * (1.0 - pl.col("long_sl_w"))
        )
        short_tp = in_session & (
            pl.col(f"_lo_{h}")
            <= pl.col("entry_px") * (1.0 - pl.col("short_tp_w") - tp_penetration)
        )
        short_sl = in_session & (
            pl.col(f"_hi_{h}") >= pl.col("entry_px") * (1.0 + pl.col("short_sl_w"))
        )

        still_long = pl.col("_long_event") == 0
        still_short = pl.col("_short_event") == 0
        # Same-bar TP+SL → SL first (conservative).
        df = df.with_columns(
            _long_event=pl.when(still_long & long_sl)
            .then(pl.lit(-1, dtype=pl.Int8))
            .when(still_long & long_tp)
            .then(pl.lit(1, dtype=pl.Int8))
            .otherwise(pl.col("_long_event")),
            _short_event=pl.when(still_short & short_sl)
            .then(pl.lit(-1, dtype=pl.Int8))
            .when(still_short & short_tp)
            .then(pl.lit(1, dtype=pl.Int8))
            .otherwise(pl.col("_short_event")),
            _long_exit_h=pl.when(still_long & (long_sl | long_tp))
            .then(pl.lit(h, dtype=pl.Int32))
            .otherwise(pl.col("_long_exit_h")),
            _short_exit_h=pl.when(still_short & (short_sl | short_tp))
            .then(pl.lit(h, dtype=pl.Int32))
            .otherwise(pl.col("_short_exit_h")),
        )

    def _exit_col(exit_h_col: str, value_prefix: str) -> pl.Expr:
        expr = pl.lit(None, dtype=pl.Float64)
        for h in range(1, horizon_bars + 1):
            in_session = (
                (pl.col(f"_d_{h}") == pl.col("date_only"))
                & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
                & pl.col(f"_c_{h}").is_not_null()
            )
            expr = (
                pl.when((pl.col(exit_h_col) == h) & in_session)
                .then(pl.col(f"{value_prefix}{h}"))
                .otherwise(expr)
            )
        return expr

    def _exit_ok(exit_h_col: str) -> pl.Expr:
        expr = pl.lit(False)
        for h in range(1, horizon_bars + 1):
            in_session = (
                (pl.col(f"_d_{h}") == pl.col("date_only"))
                & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
                & pl.col(f"_c_{h}").is_not_null()
            )
            expr = (
                pl.when((pl.col(exit_h_col) == h) & in_session)
                .then(True)
                .otherwise(expr)
            )
        return expr

    # Max favorable excursion over the in-session H-path (diagnostic / path-density).
    # `move` is a per-bar favorable return: long uses high, short uses low.
    # Strict `>` keeps the earliest bar on ties (when the peak first appears).
    def _mfe_path(move) -> tuple[pl.Expr, pl.Expr]:
        mfe = pl.lit(None, dtype=pl.Float64)
        peak_bar = pl.lit(None, dtype=pl.Int32)
        for h in range(1, horizon_bars + 1):
            m = move(h)
            in_session = (
                (pl.col(f"_d_{h}") == pl.col("date_only"))
                & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
                & m.is_not_null()
            )
            new_peak = in_session & (mfe.is_null() | (m > mfe))
            peak_bar = (
                pl.when(new_peak).then(pl.lit(h, dtype=pl.Int32)).otherwise(peak_bar)
            )
            mfe = pl.when(new_peak).then(m).otherwise(mfe)
        return mfe, peak_bar

    # Peak bar + MFE while the trade is open (bars 1..exit_h) — MFE-decay Step 0.
    def _mfe_until_exit(move, exit_h_col: str) -> tuple[pl.Expr, pl.Expr]:
        mfe = pl.lit(None, dtype=pl.Float64)
        peak_bar = pl.lit(None, dtype=pl.Int32)
        for h in range(1, horizon_bars + 1):
            m = move(h)
            in_session = (
                (pl.col(f"_d_{h}") == pl.col("date_only"))
                & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
                & m.is_not_null()
            )
            eligible = in_session & (pl.col(exit_h_col) >= h)
            new_peak = eligible & (mfe.is_null() | (m > mfe))
            peak_bar = (
                pl.when(new_peak).then(pl.lit(h, dtype=pl.Int32)).otherwise(peak_bar)
            )
            mfe = pl.when(new_peak).then(m).otherwise(mfe)
        return mfe, peak_bar

    # First bar where favorable move clears `threshold` (TP-floor Step 0).
    def _first_touch(move, threshold: float) -> pl.Expr:
        touch = pl.lit(None, dtype=pl.Int32)
        for h in range(1, horizon_bars + 1):
            m = move(h)
            in_session = (
                (pl.col(f"_d_{h}") == pl.col("date_only"))
                & (pl.col(f"_t_{h}") <= mis_exit_bar_end)
                & m.is_not_null()
            )
            hit = in_session & (m >= threshold) & touch.is_null()
            touch = pl.when(hit).then(pl.lit(h, dtype=pl.Int32)).otherwise(touch)
        return touch

    def _long_move(h: int) -> pl.Expr:
        return pl.col(f"_hi_{h}") / pl.col("entry_px") - 1.0

    def _short_move(h: int) -> pl.Expr:
        return 1.0 - pl.col(f"_lo_{h}") / pl.col("entry_px")

    _mfe_long, _abs_peak_long = _mfe_path(_long_move)
    _mfe_short, _abs_peak_short = _mfe_path(_short_move)
    _mfe_long_held, _peak_bar_long = _mfe_until_exit(_long_move, "_long_exit_h")
    _mfe_short_held, _peak_bar_short = _mfe_until_exit(_short_move, "_short_exit_h")
    _mfe50_first_long = _first_touch(_long_move, TP_FLOOR_LONG_CANDIDATE)

    df = df.with_columns(
        _long_exit_close=_exit_col("_long_exit_h", "_c_"),
        _long_exit_nifty=_exit_col("_long_exit_h", "_nc_"),
        _short_exit_close=_exit_col("_short_exit_h", "_c_"),
        _short_exit_nifty=_exit_col("_short_exit_h", "_nc_"),
        _long_ok=_exit_ok("_long_exit_h"),
        _short_ok=_exit_ok("_short_exit_h"),
        _mfe_long=_mfe_long,
        _mfe_short=_mfe_short,
        _abs_peak_long=_abs_peak_long,
        _abs_peak_short=_abs_peak_short,
        _mfe_long_held=_mfe_long_held,
        _mfe_short_held=_mfe_short_held,
        _peak_bar_long=_peak_bar_long,
        _peak_bar_short=_peak_bar_short,
        _mfe50_first_long=_mfe50_first_long,
    ).with_columns(
        # Barrier hits realize at the barrier, not at the exit bar close.
        _long_path_ret=pl.when(pl.col("_long_event") == 1)
        .then(pl.col("long_tp_w"))
        .when(pl.col("_long_event") == -1)
        .then(-pl.col("long_sl_w"))
        .otherwise(pl.col("_long_exit_close") / pl.col("entry_px") - 1.0),
        # Stock-side move for the short sleeve: TP = price fell, SL = price rose.
        _short_path_ret=pl.when(pl.col("_short_event") == 1)
        .then(-pl.col("short_tp_w"))
        .when(pl.col("_short_event") == -1)
        .then(pl.col("short_sl_w"))
        .otherwise(pl.col("_short_exit_close") / pl.col("entry_px") - 1.0),
        _long_nifty_ret=pl.col("_long_exit_nifty") / pl.col("entry_nifty") - 1.0,
        _short_nifty_ret=pl.col("_short_exit_nifty") / pl.col("entry_nifty") - 1.0,
    )

    # Dead zone applies to timeouts only; a resolved barrier keeps its sign.
    long_label = (
        pl.when(~pl.col("_long_ok"))
        .then(None)
        .when(pl.col("_long_event") != 0)
        .then(pl.col("_long_event"))
        .when(pl.col("_long_path_ret").abs() <= DEAD_ZONE)
        .then(pl.lit(0, dtype=pl.Int8))
        .otherwise(pl.lit(0, dtype=pl.Int8))
    )
    short_label = (
        pl.when(~pl.col("_short_ok"))
        .then(None)
        .when(pl.col("_short_event") != 0)
        .then(pl.col("_short_event"))
        .when(pl.col("_short_path_ret").abs() <= DEAD_ZONE)
        .then(pl.lit(0, dtype=pl.Int8))
        .otherwise(pl.lit(0, dtype=pl.Int8))
    )

    df = df.with_columns(
        tb_label_long=pl.when(
            pl.col("tb_eligible_long")
            & (pl.col("entry_time") <= long_last_entry)
            & pl.col("_long_ok")
        )
        .then(long_label)
        .otherwise(None),
        tb_label_short=pl.when(
            pl.col("tb_eligible_short")
            & (pl.col("entry_time") <= short_last_entry)
            & pl.col("_short_ok")
        )
        .then(short_label)
        .otherwise(None),
        tb_excess_ret_long=pl.when(pl.col("_long_ok"))
        .then(pl.col("_long_path_ret") - pl.col("_long_nifty_ret") - cost)
        .otherwise(None),
        tb_excess_ret_short=pl.when(pl.col("_short_ok"))
        .then(
            # Short path PnL is -stock path; excess vs Nifty uses same-window nifty.
            (-pl.col("_short_path_ret")) - (-pl.col("_short_nifty_ret")) - cost
        )
        .otherwise(None)
    )
    # Favorable excursion still held at TB exit (return units). SL → 0 (all given back).
    df = df.with_columns(
        _long_fav_exit=pl.when(pl.col("_long_event") == 1)
        .then(pl.col("long_tp_w"))
        .when(pl.col("_long_event") == -1)
        .then(0.0)
        .otherwise(
            pl.max_horizontal(
                pl.col("_long_exit_close") / pl.col("entry_px") - 1.0,
                pl.lit(0.0),
            )
        ),
        _short_fav_exit=pl.when(pl.col("_short_event") == 1)
        .then(pl.col("short_tp_w"))
        .when(pl.col("_short_event") == -1)
        .then(0.0)
        .otherwise(
            pl.max_horizontal(
                1.0 - pl.col("_short_exit_close") / pl.col("entry_px"),
                pl.lit(0.0),
            )
        ),
    )

    df = df.with_columns(
        # Fraction of side TP floor — path-density Step 0 (not a training feature).
        mfe_frac_long=pl.when(pl.col("_long_ok"))
        .then(pl.col("_mfe_long") / TP_FLOOR_LONG)
        .otherwise(None),
        mfe_frac_short=pl.when(pl.col("_short_ok"))
        .then(pl.col("_mfe_short") / TP_FLOOR_SHORT)
        .otherwise(None),
        # Absolute MFE in bps — TP-floor Step 0 (denominator frozen; not mfe_frac).
        mfe_bps_long=pl.when(pl.col("_long_ok"))
        .then(pl.col("_mfe_long") * BPS)
        .otherwise(None),
        mfe_bps_short=pl.when(pl.col("_short_ok"))
        .then(pl.col("_mfe_short") * BPS)
        .otherwise(None),
        mfe_abs_peak_bar_long=pl.when(pl.col("_long_ok"))
        .then(pl.col("_abs_peak_long"))
        .otherwise(None),
        mfe_abs_peak_bar_short=pl.when(pl.col("_short_ok"))
        .then(pl.col("_abs_peak_short"))
        .otherwise(None),
        # First bar clearing candidate Long floor (50 bps) — SL-contamination input.
        mfe50_first_bar_long=pl.when(pl.col("_long_ok"))
        .then(pl.col("_mfe50_first_long"))
        .otherwise(None),
        # MFE-decay Step 0 — peak while held + giveback vs exit (not training features).
        mfe_peak_bar_long=pl.when(pl.col("_long_ok"))
        .then(pl.col("_peak_bar_long"))
        .otherwise(None),
        mfe_peak_bar_short=pl.when(pl.col("_short_ok"))
        .then(pl.col("_peak_bar_short"))
        .otherwise(None),
        giveback_frac_long=pl.when(pl.col("_long_ok"))
        .then(
            (pl.col("_mfe_long_held") - pl.col("_long_fav_exit")).clip(lower_bound=0.0)
            / TP_FLOOR_LONG
        )
        .otherwise(None),
        giveback_frac_short=pl.when(pl.col("_short_ok"))
        .then(
            (pl.col("_mfe_short_held") - pl.col("_short_fav_exit")).clip(lower_bound=0.0)
            / TP_FLOOR_SHORT
        )
        .otherwise(None),
        tb_exit_h_long=pl.when(pl.col("_long_ok"))
        .then(pl.col("_long_exit_h"))
        .otherwise(None),
        tb_exit_h_short=pl.when(pl.col("_short_ok"))
        .then(pl.col("_short_exit_h"))
        .otherwise(None),
    )

    # Geometry (atr_pct / widths) is frozen at the 15m decision bar for Tier 3.
    return df.select(
        [
            "symbol",
            "date",
            "atr_pct",
            "long_tp_w",
            "long_sl_w",
            "short_tp_w",
            "short_sl_w",
            "tb_label_long",
            "tb_label_short",
            "tb_excess_ret_long",
            "tb_excess_ret_short",
            "tb_eligible_long",
            "tb_eligible_short",
            "mfe_frac_long",
            "mfe_frac_short",
            "mfe_bps_long",
            "mfe_bps_short",
            "mfe_abs_peak_bar_long",
            "mfe_abs_peak_bar_short",
            "mfe50_first_bar_long",
            "mfe_peak_bar_long",
            "mfe_peak_bar_short",
            "giveback_frac_long",
            "giveback_frac_short",
            "tb_exit_h_long",
            "tb_exit_h_short",
        ]
    )
