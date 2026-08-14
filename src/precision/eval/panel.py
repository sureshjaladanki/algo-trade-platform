"""Tier 3 Precision eval — episode panel (attemptable / naive EV / PrecNet)."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.horizon.eval.constants import CIRCUIT_RANGE_EPS
from src.labels.triple_barrier import ROUND_TRIP_COST
from src.precision.eval.constants import (
    _EXPIRY_WEEKDAY,
    _STRUCTURAL_SKIPS,
    k_for,
    last_entry_for,
    tb_label_col,
)
from src.precision.precision import resolve_frozen_path
from src.regime.intraday import NSE_OPEN_BLEED_BAR


def prepare_eval_panel(
    trades: pl.DataFrame,
    features_1m: pl.DataFrame,
    direction: str,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Sleeve episode panel with naive decision-close TB path and Precision net.

    Returns ``(gated, raw_sleeve)``. ``raw_sleeve`` is the unfiltered direction
    slice (P0 K / MIS checks). ``gated`` applies locked K, drops auction bleed /
    past last-entry / non-attemptable / circuit-blocked rows.
    """
    sleeve = trades.filter(pl.col("horizon_direction") == direction)
    if "date_only" not in sleeve.columns:
        sleeve = sleeve.with_columns(date_only=pl.col("decision_bar").dt.date())
    if "time_only" not in sleeve.columns:
        sleeve = sleeve.with_columns(time_only=pl.col("decision_bar").dt.time())

    tb_col = tb_label_col(direction)
    sleeve = sleeve.with_columns(
        tb_label=pl.col(tb_col) if tb_col in sleeve.columns else pl.lit(None),
        is_expiry_day=pl.col("decision_bar").dt.weekday() == _EXPIRY_WEEKDAY,
        auction_bleed=pl.col("time_only") == NSE_OPEN_BLEED_BAR,
        past_last_entry=pl.col("time_only") > last_entry_for(direction),
    )
    sleeve = _attach_path_columns(sleeve, features_1m)
    sleeve = sleeve.with_columns(
        prec_net=pl.when(pl.col("precision_fire"))
        .then(pl.col("gross_ret") - ROUND_TRIP_COST)
        .otherwise(None),
        timing_lift=pl.when(pl.col("precision_fire"))
        .then((pl.col("gross_ret") - ROUND_TRIP_COST) - pl.col("naive_net"))
        .otherwise(None),
    )

    k = k_for(direction)
    gated = sleeve.filter(
        (pl.col("horizon_rank") <= k)
        & (~pl.col("auction_bleed"))
        & (~pl.col("past_last_entry"))
        & pl.col("attemptable")
        & (~pl.col("circuit_block"))
    )
    return gated, sleeve


def _attach_path_columns(
    sleeve: pl.DataFrame, features_1m: pl.DataFrame
) -> pl.DataFrame:
    """NaiveTBPathEV + attemptable / circuit flags via the production 1m walk."""
    if sleeve.height == 0:
        return sleeve.with_columns(
            naive_net=pl.lit(None, dtype=pl.Float64),
            attemptable=pl.lit(False),
            circuit_block=pl.lit(False),
        )

    by_symbol = {
        str(key[0] if isinstance(key, tuple) else key): grp
        for key, grp in features_1m.sort(["symbol", "date"]).group_by(
            "symbol", maintain_order=True
        )
    }
    naive_nets: list[float | None] = []
    attemptable: list[bool] = []
    circuit_block: list[bool] = []
    for ep in sleeve.iter_rows(named=True):
        net, att, cir = _naive_path(ep, by_symbol)
        naive_nets.append(net)
        attemptable.append(att)
        circuit_block.append(cir)
    return sleeve.with_columns(
        naive_net=pl.Series("naive_net", naive_nets, dtype=pl.Float64),
        attemptable=pl.Series("attemptable", attemptable, dtype=pl.Boolean),
        circuit_block=pl.Series("circuit_block", circuit_block, dtype=pl.Boolean),
    )


def _naive_path(
    ep: dict, by_symbol: dict[str, pl.DataFrame]
) -> tuple[float | None, bool, bool]:
    """
    Decision-close entry, frozen TP/SL widths, vertical = decision_bar + H.

    Structural unattemptables (missing 1m / empty hold / halt at decision)
    return attemptable=False. Circuit-pinned SL/MIS exits are circuit_block.
    """
    skip = ep.get("exit_reason")
    if skip in _STRUCTURAL_SKIPS:
        return None, False, False

    bars = by_symbol.get(str(ep["symbol"]))
    decision_close = ep.get("decision_close")
    tp_w, sl_w = ep.get("tp_w"), ep.get("sl_w")
    vertical = ep.get("vertical_deadline")
    decision_bar = ep["decision_bar"]
    if (
        bars is None
        or decision_close is None
        or tp_w is None
        or sl_w is None
        or vertical is None
    ):
        return None, False, False

    dec_1m = bars.filter(pl.col("date") == decision_bar)
    circuit_decision = False
    if dec_1m.height:
        row = dec_1m.row(0, named=True)
        circuit_decision = _is_circuit_bar(row)
    if circuit_decision:
        return None, False, True

    hold = bars.filter(
        (pl.col("date") > decision_bar) & (pl.col("date") <= vertical)
    ).sort("date")
    if hold.height == 0:
        return None, False, False

    path = resolve_frozen_path(
        hold,
        direction=ep["horizon_direction"],
        entry_px=float(decision_close),
        tp_w=float(tp_w),
        sl_w=float(sl_w),
        vertical_deadline=vertical,
    )
    circuit_exit = _circuit_at(bars, path["exit_bar_1m"], path["exit_reason"])
    naive_net = float(path["gross_ret"]) - ROUND_TRIP_COST
    return naive_net, True, circuit_exit


def _is_circuit_bar(row: dict) -> bool:
    high, low, close = row.get("high"), row.get("low"), row.get("close")
    if high is None or low is None:
        return False
    if high == low:
        return True
    if close is None or close == 0:
        return False
    return abs(high - low) / abs(close) <= CIRCUIT_RANGE_EPS


def _circuit_at(
    bars: pl.DataFrame, exit_bar: dt.datetime | None, exit_reason: str
) -> bool:
    """Circuit-pinned SL / MIS exits (Short UC traps) — exclude from gated P1–P3."""
    if exit_bar is None or exit_reason not in ("SL", "MIS_FLATTEN"):
        return False
    hit = bars.filter(pl.col("date") == exit_bar)
    if hit.height == 0:
        return False
    return _is_circuit_bar(hit.row(0, named=True))
