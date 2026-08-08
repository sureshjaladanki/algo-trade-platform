"""Tier 3 Precision rules engine — bounded-wait entry + frozen TB exits (v1)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

import polars as pl

from src.labels.triple_barrier import TP_PENETRATION
from src.precision.session import (
    AFTERNOON_COVER_START,
    MIS_FLAT_BY,
    TOP_K,
    WAIT_MINUTES,
)

ExitReason = Literal["TP", "SL", "TIMEOUT", "REGIME_FLIP", "MIS_FLATTEN", "SKIP"]

# Feature names kept for documentation / future meta-filter (rules v1 uses them inline).
LONG_FEATURES = [
    "tb_eligible_long",
    "long_tp_w",
    "long_sl_w",
    "dist_to_tp_bps",
    "dist_to_sl_bps",
    "bars_to_vertical",
    "m1_pullback_depth",
    "m1_range_compression",
    "vwap_dist_1m",
    "consec_green_1m",
    "horizon_rank",
    "horizon_score",
    "spread_proxy_bps",
]

SHORT_FEATURES = [
    "tb_eligible_short",
    "short_tp_w",
    "short_sl_w",
    "dist_to_tp_bps",
    "dist_to_sl_bps",
    "bars_to_vertical",
    "m1_bounce_depth",
    "m1_range_compression",
    "vwap_dist_1m",
    "consec_red_1m",
    "afternoon_cover_risk",
    "horizon_rank",
    "horizon_score",
    "spread_proxy_bps",
]

SPREAD_CEILING_LONG_BPS = 40.0
SPREAD_CEILING_SHORT_BPS = 25.0

VWAP_NEAR_BPS = 15.0
PULLBACK_MIN = 0.30
BOUNCE_MIN_BPS = 15.0
MIN_DIST_TO_TP_BPS = 20.0
MIN_DIST_TO_SL_BPS = 10.0
MIN_BARS_TO_VERTICAL = 15.0
MAX_RANGE_COMPRESSION = 3.0

# Phase 1 size schedule: ranks 1–2 full, 3–5 reduced; ranks > TOP_K skipped upstream.
_RANK_SIZE = ((2, 1.0), (TOP_K, 0.7))


def size_mult_from_rank(rank: int | None, *, afternoon_cover_risk: bool = False) -> float:
    """Rank 1–2 → 1.0×, 3–TOP_K → 0.7×; outside TOP_K → skip. Short afternoon ×0.5."""
    if rank is None or rank < 1 or rank > TOP_K:
        return 0.0
    mult = next(size for ceiling, size in _RANK_SIZE if rank <= ceiling)
    return mult * 0.5 if afternoon_cover_risk else mult


def classify_precision(
    registry: pl.DataFrame,
    stock_1m: pl.DataFrame,
    *,
    wait_minutes: int = WAIT_MINUTES,
) -> pl.DataFrame:
    """
    Rules-first Precision: bounded-wait 1m entry → frozen TB exits.

    ``registry.decision_bar`` is the 15m bar-end (actionable) stamp. Bounded wait
    runs on 1m bars ``[decision_bar, decision_bar + wait_minutes)``. Vertical
    timeout stays ``min(decision_bar + H, MIS_FLAT_BY)`` (wall-clock ~15:00).

    Phase 1 selectivity: registry is already TOP_K; episodes below the bar×sleeve
    ``edge_score`` median are skipped (setup and fallback alike).

    Returns one row per decision episode with fire / skip, fill, barriers, exit.
    ``stock_1m`` must already carry Precision 1m features
    (``calculate_precision_features``). Registry must include ``edge_score``.
    """
    if registry.height == 0:
        return _empty_trades()

    registry = registry.with_columns(
        edge_median=pl.col("edge_score")
        .median()
        .over(["decision_bar", "horizon_direction"]),
    )

    by_symbol = {
        str(key[0] if isinstance(key, tuple) else key): grp
        for key, grp in stock_1m.sort(["symbol", "date"]).group_by(
            "symbol", maintain_order=True
        )
    }
    short_sl_blocked: set[tuple[str, dt.date]] = set()
    rows = [
        _process_episode(ep, by_symbol, short_sl_blocked, wait_minutes)
        for ep in registry.iter_rows(named=True)
    ]
    return pl.DataFrame(rows)


def _process_episode(
    ep: dict,
    by_symbol: dict[str, pl.DataFrame],
    short_sl_blocked: set[tuple[str, dt.date]],
    wait_minutes: int,
) -> dict:
    symbol = ep["symbol"]
    direction = ep["horizon_direction"]
    session_day = ep["date_only"]
    decision_bar = ep["decision_bar"]
    vertical_deadline = ep["vertical_deadline"]
    atr_pct = ep["atr_pct"]
    rank = ep["horizon_rank"]
    edge = ep["edge_score"]
    edge_floor = ep["edge_median"]
    tp_w, sl_w, spread_ceiling = _sleeve_geometry(ep, direction)

    base = {
        "symbol": symbol,
        "decision_bar": decision_bar,
        "horizon_direction": direction,
        "horizon_rank": int(rank) if rank is not None else None,
        "horizon_score": ep["horizon_score"],
        "edge_score": edge,
        "daily_regime": ep["daily_regime"],
        "intraday_regime": ep["intraday_regime"],
        "atr_pct": float(atr_pct) if atr_pct is not None else None,
        "tp_w": tp_w,
        "sl_w": sl_w,
        "vertical_deadline": vertical_deadline,
        "tb_label_long": ep.get("tb_label_long"),
        "tb_label_short": ep.get("tb_label_short"),
        "meta_label_pass": None,
    }

    # Shared conviction gate (setup + fallback): require edge ≥ bar×sleeve median.
    if edge < edge_floor:
        return _skip_row(base)

    if direction == "short" and (symbol, session_day) in short_sl_blocked:
        return _skip_row(base)

    bars = by_symbol.get(symbol)
    if bars is None or atr_pct is None or atr_pct <= 0:
        return _skip_row(base)

    entry_window_end = decision_bar + dt.timedelta(minutes=wait_minutes - 1)
    wait_bars = bars.filter(
        (pl.col("date") >= decision_bar) & (pl.col("date") <= entry_window_end)
    ).sort("date")
    if wait_bars.height == 0:
        return _skip_row(base)

    wait_bars = wait_bars.with_columns(
        m1_range_compression=(pl.col("atr_1m_5") / pl.col("close")) / atr_pct,
    )

    fill = _find_entry(
        wait_bars,
        direction=direction,
        decision_close=float(ep["decision_close"]),
        tp_w=tp_w,
        sl_w=sl_w,
        spread_ceiling=spread_ceiling,
        vertical_deadline=vertical_deadline,
    )
    if fill is None:
        return _skip_row(base)

    afternoon_risk = bool(fill["afternoon_cover_risk"])
    size_mult = size_mult_from_rank(
        base["horizon_rank"], afternoon_cover_risk=afternoon_risk
    )
    if size_mult <= 0:
        return _skip_row(base)

    entry_bar = fill["entry_bar_1m"]
    entry_px = float(fill["entry_px"])
    tp_px, sl_px = _absolute_barriers(direction, entry_px, tp_w, sl_w)

    exit_info = _resolve_exit(
        bars.filter(
            (pl.col("date") > entry_bar) & (pl.col("date") <= vertical_deadline)
        ).sort("date"),
        direction=direction,
        entry_px=entry_px,
        tp_px=tp_px,
        sl_px=sl_px,
        vertical_deadline=vertical_deadline,
    )

    if direction == "short" and exit_info["exit_reason"] == "SL":
        short_sl_blocked.add((symbol, session_day))

    return {
        **base,
        "precision_fire": True,
        "entry_bar_1m": entry_bar,
        "entry_px": entry_px,
        "tp_px": tp_px,
        "sl_px": sl_px,
        "size_mult": size_mult,
        "entry_reason": fill["entry_reason"],
        "afternoon_cover_risk": afternoon_risk,
        "exit_bar_1m": exit_info["exit_bar_1m"],
        "exit_px": exit_info["exit_px"],
        "exit_reason": exit_info["exit_reason"],
        "gross_ret": exit_info["gross_ret"],
    }


def _sleeve_geometry(ep: dict, direction: str) -> tuple[float, float, float]:
    if direction == "long":
        return float(ep["long_tp_w"]), float(ep["long_sl_w"]), SPREAD_CEILING_LONG_BPS
    return float(ep["short_tp_w"]), float(ep["short_sl_w"]), SPREAD_CEILING_SHORT_BPS


def _absolute_barriers(
    direction: str, entry_px: float, tp_w: float, sl_w: float
) -> tuple[float, float]:
    if direction == "long":
        return entry_px * (1.0 + tp_w), entry_px * (1.0 - sl_w)
    return entry_px * (1.0 - tp_w), entry_px * (1.0 + sl_w)


def _find_entry(
    wait_bars: pl.DataFrame,
    *,
    direction: str,
    decision_close: float,
    tp_w: float,
    sl_w: float,
    spread_ceiling: float,
    vertical_deadline: dt.datetime,
) -> dict | None:
    """Bounded wait: setup fill when possible, else last-bar fallback."""
    bars = list(wait_bars.iter_rows(named=True))
    last_i = len(bars) - 1
    for i, bar in enumerate(bars):
        fallback = i == last_i
        if not _hard_gates_ok(
            bar,
            direction=direction,
            decision_close=decision_close,
            tp_w=tp_w,
            sl_w=sl_w,
            spread_ceiling=spread_ceiling,
            vertical_deadline=vertical_deadline,
        ):
            if fallback:
                return None
            continue

        if not fallback and not _setup_ok(bar, direction):
            continue

        return {
            "entry_bar_1m": bar["date"],
            "entry_px": float(bar["close"]),
            "entry_reason": "fallback" if fallback else "setup",
            "afternoon_cover_risk": bool(bar["afternoon_cover_risk"]),
        }
    return None


def _hard_gates_ok(
    bar: dict,
    *,
    direction: str,
    decision_close: float,
    tp_w: float,
    sl_w: float,
    spread_ceiling: float,
    vertical_deadline: dt.datetime,
) -> bool:
    spread = bar["spread_proxy_bps"]
    if spread is None or spread > spread_ceiling:
        return False
    if bar["high"] == bar["low"]:
        return False

    last = float(bar["close"])
    dist_tp, dist_sl = _room_to_barriers_bps(
        direction, last, decision_close, tp_w, sl_w
    )
    if dist_tp < MIN_DIST_TO_TP_BPS or dist_sl < MIN_DIST_TO_SL_BPS:
        return False

    bars_left = (vertical_deadline - bar["date"]).total_seconds() / 60.0
    if bars_left < MIN_BARS_TO_VERTICAL:
        return False

    compression = bar["m1_range_compression"]
    if compression is not None and compression > MAX_RANGE_COMPRESSION:
        return False

    if (
        direction == "short"
        and bar["date"].time() >= AFTERNOON_COVER_START
        and (bar["consec_red_1m"] or 0) < 2
    ):
        return False

    return True


def _room_to_barriers_bps(
    direction: str,
    last: float,
    decision_close: float,
    tp_w: float,
    sl_w: float,
) -> tuple[float, float]:
    if direction == "long":
        tp_px = decision_close * (1.0 + tp_w)
        sl_px = decision_close * (1.0 - sl_w)
        return (tp_px / last - 1.0) * 1e4, (last / sl_px - 1.0) * 1e4

    tp_px = decision_close * (1.0 - tp_w)
    sl_px = decision_close * (1.0 + sl_w)
    return (last / tp_px - 1.0) * 1e4, (sl_px / last - 1.0) * 1e4


def _setup_ok(bar: dict, direction: str) -> bool:
    """Pullback-then-reclaim (Long) or bounce-then-breakdown (Short)."""
    if direction == "long":
        near_vwap = abs(bar["vwap_dist_bps"] or 1e9) <= VWAP_NEAR_BPS
        pullback = (bar["m1_pullback_depth"] or 0.0) >= PULLBACK_MIN
        return bool(bar["reclaim_prior_high"]) and (near_vwap or pullback)

    bounce = (bar["m1_bounce_bps"] or 0.0) >= BOUNCE_MIN_BPS
    return bool(bar["break_prior_low"]) and bounce


def _resolve_exit(
    hold_bars: pl.DataFrame,
    *,
    direction: str,
    entry_px: float,
    tp_px: float,
    sl_px: float,
    vertical_deadline: dt.datetime,
) -> dict:
    """Walk 1m bars until TP / SL / MIS / timeout. No trail in v1."""
    for bar in hold_bars.iter_rows(named=True):
        ts = bar["date"]
        high, low, close = float(bar["high"]), float(bar["low"]), float(bar["close"])

        if ts.time() >= MIS_FLAT_BY:
            return _exit_at(ts, close, entry_px, direction, "MIS_FLATTEN")

        hit = _barrier_hit(direction, high, low, tp_px, sl_px)
        if hit is not None:
            reason, px = hit
            return _exit_at(ts, px, entry_px, direction, reason)

        if ts >= vertical_deadline:
            return _exit_at(ts, close, entry_px, direction, "TIMEOUT")

    if hold_bars.height > 0:
        last = hold_bars.row(-1, named=True)
        return _exit_at(
            last["date"], float(last["close"]), entry_px, direction, "TIMEOUT"
        )

    return {
        "exit_bar_1m": vertical_deadline,
        "exit_px": entry_px,
        "exit_reason": "TIMEOUT",
        "gross_ret": 0.0,
    }


def _barrier_hit(
    direction: str,
    high: float,
    low: float,
    tp_px: float,
    sl_px: float,
) -> tuple[str, float] | None:
    """Same-bar TP+SL → SL first (TB conservatism)."""
    if direction == "long":
        if low <= sl_px:
            return "SL", sl_px
        if high >= tp_px * (1.0 + TP_PENETRATION):
            return "TP", tp_px
        return None

    if high >= sl_px:
        return "SL", sl_px
    if low <= tp_px * (1.0 - TP_PENETRATION):
        return "TP", tp_px
    return None


def _exit_at(
    ts: dt.datetime,
    exit_px: float,
    entry_px: float,
    direction: str,
    reason: str,
) -> dict:
    gross = (
        exit_px / entry_px - 1.0
        if direction == "long"
        else entry_px / exit_px - 1.0
    )
    return {
        "exit_bar_1m": ts,
        "exit_px": exit_px,
        "exit_reason": reason,
        "gross_ret": gross,
    }


def _skip_row(base: dict, reason: str = "SKIP") -> dict:
    return {
        **base,
        "precision_fire": False,
        "entry_bar_1m": None,
        "entry_px": None,
        "tp_px": None,
        "sl_px": None,
        "size_mult": 0.0,
        "entry_reason": None,
        "afternoon_cover_risk": False,
        "exit_bar_1m": None,
        "exit_px": None,
        "exit_reason": reason,
        "gross_ret": None,
    }


def _empty_trades() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "symbol": pl.Utf8,
            "decision_bar": pl.Datetime,
            "horizon_direction": pl.Utf8,
            "horizon_rank": pl.Int64,
            "horizon_score": pl.Float64,
            "edge_score": pl.Float64,
            "daily_regime": pl.Utf8,
            "intraday_regime": pl.Utf8,
            "atr_pct": pl.Float64,
            "tp_w": pl.Float64,
            "sl_w": pl.Float64,
            "vertical_deadline": pl.Datetime,
            "tb_label_long": pl.Int8,
            "tb_label_short": pl.Int8,
            "meta_label_pass": pl.Boolean,
            "precision_fire": pl.Boolean,
            "entry_bar_1m": pl.Datetime,
            "entry_px": pl.Float64,
            "tp_px": pl.Float64,
            "sl_px": pl.Float64,
            "size_mult": pl.Float64,
            "entry_reason": pl.Utf8,
            "afternoon_cover_risk": pl.Boolean,
            "exit_bar_1m": pl.Datetime,
            "exit_px": pl.Float64,
            "exit_reason": pl.Utf8,
            "gross_ret": pl.Float64,
        }
    )
