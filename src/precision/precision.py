"""Tier 3 Precision rules engine — bounded-wait entry + frozen TB exits (v1)."""

from __future__ import annotations

import datetime as dt
import math
from typing import Literal

import polars as pl

from src.labels.triple_barrier import ROUND_TRIP_COST, TP_PENETRATION
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

# Liquidity ceilings (bps of 1m range / close). Short is tighter.
SPREAD_CEILING_LONG_BPS = 40.0
SPREAD_CEILING_SHORT_BPS = 25.0

# Entry setup thresholds.
VWAP_NEAR_BPS = 15.0
PULLBACK_MIN = 0.30
BOUNCE_MIN_BPS = 15.0
# Skip if room-to-target collapsed or already inside SL buffer.
MIN_DIST_TO_TP_BPS = 20.0
MIN_DIST_TO_SL_BPS = 10.0
# Near-zero runway (minutes).
MIN_BARS_TO_VERTICAL = 15.0


def size_mult_from_rank(rank: int | None, *, afternoon_cover_risk: bool = False) -> float:
    """
    Rank-based size from Tier 2. Skip (0) outside top/bottom 8.

    rank 1–2 → 1.0×, 3–5 → 0.7×, 6–8 → 0.4×; Short afternoon cover ×0.5.
    """
    if rank is None or rank < 1 or rank > TOP_K:
        return 0.0
    if rank <= 2:
        mult = 1.0
    elif rank <= 5:
        mult = 0.7
    else:
        mult = 0.4
    if afternoon_cover_risk:
        mult *= 0.5
    return mult


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

    Returns one row per decision episode with fire / skip, fill, barriers, exit.
    `stock_1m` must already carry Precision 1m features
    (`calculate_precision_features`).
    """
    if registry.height == 0:
        return _empty_trades()

    stock_1m = stock_1m.sort(["symbol", "date"])
    by_symbol: dict[str, pl.DataFrame] = {}
    for key, grp in stock_1m.group_by("symbol", maintain_order=True):
        sym = key[0] if isinstance(key, tuple) else key
        by_symbol[str(sym)] = grp

    rows: list[dict] = []
    # Short no-reentry after SL: (symbol, session_date) → blocked.
    short_sl_blocked: set[tuple[str, dt.date]] = set()

    for ep in registry.iter_rows(named=True):
        rows.append(
            _process_episode(
                ep, by_symbol, short_sl_blocked, wait_minutes
            )
        )

    if not rows:
        return _empty_trades()
    return pl.DataFrame(rows)


def _process_episode(
    ep: dict,
    by_symbol: dict[str, pl.DataFrame],
    short_sl_blocked: set[tuple[str, dt.date]],
    wait_minutes: int,
) -> dict:
    """Process a single decision episode through the precision timing rules."""
    symbol = ep["symbol"]
    direction = ep["horizon_direction"]
    session_day = ep["date_only"]
    decision_bar = ep["decision_bar"]
    vertical_deadline = ep["vertical_deadline"]
    decision_close = float(ep["decision_close"])
    atr_pct = float(ep["atr_pct"]) if ep["atr_pct"] is not None else None
    rank = int(ep["horizon_rank"]) if ep["horizon_rank"] is not None else None
    score = ep["horizon_score"]

    if direction == "long":
        tp_w = float(ep["long_tp_w"])
        sl_w = float(ep["long_sl_w"])
        spread_ceiling = SPREAD_CEILING_LONG_BPS
    else:
        tp_w = float(ep["short_tp_w"])
        sl_w = float(ep["short_sl_w"])
        spread_ceiling = SPREAD_CEILING_SHORT_BPS

    base = {
        "symbol": symbol,
        "decision_bar": decision_bar,
        "horizon_direction": direction,
        "horizon_rank": rank,
        "horizon_score": score,
        "daily_regime": ep["daily_regime"],
        "intraday_regime": ep["intraday_regime"],
        "atr_pct": atr_pct,
        "tp_w": tp_w,
        "sl_w": sl_w,
        "vertical_deadline": vertical_deadline,
        "tb_label_long": ep.get("tb_label_long"),
        "tb_label_short": ep.get("tb_label_short"),
        "meta_label_pass": None,
    }

    if direction == "short" and (symbol, session_day) in short_sl_blocked:
        return _skip_row(base, "SKIP")

    bars = by_symbol.get(symbol)
    if bars is None or atr_pct is None or atr_pct <= 0:
        return _skip_row(base, "SKIP")

    # Bounded wait: 1m bars from decision_bar through the next wait_minutes.
    entry_window_end = decision_bar + dt.timedelta(minutes=wait_minutes - 1)
    wait_bars = bars.filter(
        (pl.col("date") >= decision_bar) & (pl.col("date") <= entry_window_end)
    ).sort("date")

    if wait_bars.height == 0:
        return _skip_row(base, "SKIP")

    # Compression = (ATR_1m% / TB atr_pct). Skip gap / halt-distorted bars.
    wait_bars = wait_bars.with_columns(
        m1_range_compression=(pl.col("atr_1m_5") / pl.col("close"))
        / pl.lit(atr_pct),
    )

    fill = _find_entry(
        wait_bars,
        direction=direction,
        decision_close=decision_close,
        tp_w=tp_w,
        sl_w=sl_w,
        spread_ceiling=spread_ceiling,
        vertical_deadline=vertical_deadline,
    )
    if fill is None:
        return _skip_row(base, "SKIP")

    afternoon_risk = bool(fill.get("afternoon_cover_risk", False))
    size_mult = size_mult_from_rank(rank, afternoon_cover_risk=afternoon_risk)
    if size_mult <= 0:
        return _skip_row(base, "SKIP")

    entry_bar = fill["entry_bar_1m"]
    entry_px = float(fill["entry_px"])
    if direction == "long":
        tp_px = entry_px * (1.0 + tp_w)
        sl_px = entry_px * (1.0 - sl_w)
    else:
        tp_px = entry_px * (1.0 - tp_w)
        sl_px = entry_px * (1.0 + sl_w)

    hold_bars = bars.filter(
        (pl.col("date") > entry_bar) & (pl.col("date") <= vertical_deadline)
    ).sort("date")

    exit_info = _resolve_exit(
        hold_bars,
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
    """Bounded wait: setup → fill, else fallback on last wait bar."""
    n = wait_bars.height
    for i, bar in enumerate(wait_bars.iter_rows(named=True)):
        is_fallback = i == n - 1
        gate = _entry_hard_gates(
            bar,
            direction=direction,
            decision_close=decision_close,
            tp_w=tp_w,
            sl_w=sl_w,
            spread_ceiling=spread_ceiling,
            vertical_deadline=vertical_deadline,
        )
        if not gate["ok"]:
            if is_fallback:
                return None
            continue

        setup = True if is_fallback else _entry_setup(bar, direction=direction)
        if not setup:
            continue

        # v1 backtest: fill at trigger-bar close (no bid/ask or slippage model yet).
        return {
            "entry_bar_1m": bar["date"],
            "entry_px": float(bar["close"]),
            "entry_reason": "fallback" if is_fallback else "setup",
            "afternoon_cover_risk": bool(bar.get("afternoon_cover_risk", False)),
        }
    return None


def _entry_hard_gates(
    bar: dict,
    *,
    direction: str,
    decision_close: float,
    tp_w: float,
    sl_w: float,
    spread_ceiling: float,
    vertical_deadline: dt.datetime,
) -> dict:
    last = float(bar["close"])
    spread = bar.get("spread_proxy_bps")
    if spread is None or spread > spread_ceiling:
        return {"ok": False}

    # Halt / flat print proxy.
    if bar.get("high") == bar.get("low"):
        return {"ok": False}

    if direction == "long":
        tp_px = decision_close * (1.0 + tp_w)
        sl_px = decision_close * (1.0 - sl_w)
        dist_tp = (tp_px / last - 1.0) * 1e4
        dist_sl = (last / sl_px - 1.0) * 1e4
    else:
        tp_px = decision_close * (1.0 - tp_w)
        sl_px = decision_close * (1.0 + sl_w)
        dist_tp = (last / tp_px - 1.0) * 1e4
        dist_sl = (sl_px / last - 1.0) * 1e4

    if dist_tp < MIN_DIST_TO_TP_BPS or dist_sl < MIN_DIST_TO_SL_BPS:
        return {"ok": False}

    bars_left = (vertical_deadline - bar["date"]).total_seconds() / 60.0
    if bars_left < MIN_BARS_TO_VERTICAL:
        return {"ok": False}

    compression = bar.get("m1_range_compression")
    # Compression vs TB atr is attached later; when present, skip distorted bars.
    if compression is not None and compression > 3.0:
        return {"ok": False}

    t = bar["date"].time()
    if direction == "short" and t >= AFTERNOON_COVER_START:
        consec = bar.get("consec_red_1m") or 0
        if consec < 2:
            return {"ok": False}

    return {"ok": True}


def _entry_setup(bar: dict, *, direction: str) -> bool:
    """Pullback-then-reclaim (Long) or bounce-then-breakdown (Short)."""
    if direction == "long":
        near_vwap = abs(bar.get("vwap_dist_bps") or 1e9) <= VWAP_NEAR_BPS
        pullback = (bar.get("m1_pullback_depth") or 0.0) >= PULLBACK_MIN
        reclaim = bool(bar.get("reclaim_prior_high"))
        return reclaim and (near_vwap or pullback)

    bounce = (bar.get("m1_bounce_bps") or 0.0) >= BOUNCE_MIN_BPS
    breakdown = bool(bar.get("break_prior_low"))
    return breakdown and bounce


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
        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])

        if ts.time() >= MIS_FLAT_BY:
            return _exit_at(ts, close, entry_px, direction, "MIS_FLATTEN")

        if direction == "long":
            # Same-bar TP+SL → SL first (matches TB conservatism).
            if low <= sl_px:
                return _exit_at(ts, sl_px, entry_px, direction, "SL")
            if high >= tp_px * (1.0 + TP_PENETRATION):
                return _exit_at(ts, tp_px, entry_px, direction, "TP")
        else:
            if high >= sl_px:
                return _exit_at(ts, sl_px, entry_px, direction, "SL")
            if low <= tp_px * (1.0 - TP_PENETRATION):
                return _exit_at(ts, tp_px, entry_px, direction, "TP")

        if ts >= vertical_deadline:
            return _exit_at(ts, close, entry_px, direction, "TIMEOUT")

    # Data ended before deadline — realize at last available close, not entry.
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


def _exit_at(ts: dt.datetime, exit_px: float, entry_px: float, direction: str, reason: str) -> dict:
    if direction == "long":
        gross = exit_px / entry_px - 1.0
    else:
        gross = entry_px / exit_px - 1.0
    return {
        "exit_bar_1m": ts,
        "exit_px": exit_px,
        "exit_reason": reason,
        "gross_ret": gross,
    }


def _skip_row(base: dict, reason: str) -> dict:
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


def _slice_stats(
    fires: pl.DataFrame,
    *,
    label_col: str | None = None,
) -> dict[str, float | int]:
    """Per-slice n / gross / net / exit mix (+ optional TB TP rate)."""
    n = fires.height
    if n == 0:
        return {"n": 0}

    mean_gross = float(fires["gross_ret"].mean())
    stats: dict[str, float | int] = {
        "n": n,
        "mean_gross_ret": mean_gross,
        "mean_net_ret": mean_gross - ROUND_TRIP_COST,
        "mean_size_mult": float(fires["size_mult"].mean()),
        "tp_rate": fires.filter(pl.col("exit_reason") == "TP").height / n,
        "sl_rate": fires.filter(pl.col("exit_reason") == "SL").height / n,
        "timeout_rate": fires.filter(pl.col("exit_reason") == "TIMEOUT").height / n,
        "mis_flatten_rate": (
            fires.filter(pl.col("exit_reason") == "MIS_FLATTEN").height / n
        ),
    }
    if label_col is not None and label_col in fires.columns:
        labeled = fires.drop_nulls(subset=[label_col])
        if labeled.height > 0:
            stats["tb_tp_rate"] = (
                labeled.filter(pl.col(label_col) == 1).height / labeled.height
            )
            stats["prec_tp_rate"] = (
                labeled.filter(pl.col("exit_reason") == "TP").height / labeled.height
            )
    return stats


def summarize_precision_trades(trades: pl.DataFrame) -> dict:
    """
    Hit-rate / PnL diagnostics vs TB label expectations.

    Top-level scalars stay MLflow-friendly. Nested dicts under ``by_*`` break
    down fires by entry reason, Horizon rank band, direction, and score quartile
    for A/B diagnosis (setup vs fallback, K-tighten, sleeve skew).
    """
    if trades.height == 0:
        return {"episodes": 0, "fires": 0, "fire_rate": 0.0}

    fires = trades.filter(pl.col("precision_fire"))
    n = trades.height
    n_fire = fires.height
    out: dict = {
        "episodes": n,
        "fires": n_fire,
        "fire_rate": n_fire / n if n else 0.0,
    }
    if n_fire == 0:
        return out

    out["mean_gross_ret"] = float(fires["gross_ret"].mean())
    out["mean_net_ret"] = out["mean_gross_ret"] - ROUND_TRIP_COST
    out["mean_size_mult"] = float(fires["size_mult"].mean())
    for reason in ("TP", "SL", "TIMEOUT", "MIS_FLATTEN"):
        out[f"exit_{reason.lower()}"] = fires.filter(
            pl.col("exit_reason") == reason
        ).height

    # Direction + TB label alignment (legacy top-level keys kept for MLflow).
    by_direction: dict[str, dict] = {}
    for direction, label_col in (
        ("long", "tb_label_long"),
        ("short", "tb_label_short"),
    ):
        subset = fires.filter(pl.col("horizon_direction") == direction)
        if subset.height == 0:
            continue
        stats = _slice_stats(subset, label_col=label_col)
        by_direction[direction] = stats
        out[f"{direction}_n"] = stats["n"]
        if "tb_tp_rate" in stats:
            out[f"{direction}_tb_tp_rate"] = stats["tb_tp_rate"]
            out[f"{direction}_prec_tp_rate"] = stats["prec_tp_rate"]
    out["by_direction"] = by_direction

    # Setup vs fallback fills.
    by_entry: dict[str, dict] = {}
    if "entry_reason" in fires.columns:
        for reason in ("setup", "fallback"):
            subset = fires.filter(pl.col("entry_reason") == reason)
            if subset.height == 0:
                continue
            by_entry[reason] = _slice_stats(subset)
    out["by_entry_reason"] = by_entry

    # Rank bands match size_mult_from_rank buckets.
    by_rank: dict[str, dict] = {}
    if "horizon_rank" in fires.columns:
        rank_bands = (
            ("1-2", pl.col("horizon_rank") <= 2),
            (
                "3-5",
                (pl.col("horizon_rank") >= 3) & (pl.col("horizon_rank") <= 5),
            ),
            (
                "6-8",
                (pl.col("horizon_rank") >= 6) & (pl.col("horizon_rank") <= 8),
            ),
        )
        for label, mask in rank_bands:
            subset = fires.filter(mask)
            if subset.height == 0:
                continue
            by_rank[label] = _slice_stats(subset)
    out["by_rank"] = by_rank

    # Score quartiles among fires (Q1 = weakest scores).
    by_score: dict[str, dict] = {}
    if "horizon_score" in fires.columns:
        scored = fires.drop_nulls(subset=["horizon_score"])
        if scored.height >= 4:
            qs = scored.select(
                q25=pl.col("horizon_score").quantile(0.25),
                q50=pl.col("horizon_score").quantile(0.50),
                q75=pl.col("horizon_score").quantile(0.75),
            ).row(0, named=True)
            q25, q50, q75 = qs["q25"], qs["q50"], qs["q75"]
            score_bands = (
                ("Q1_weak", pl.col("horizon_score") <= q25),
                (
                    "Q2",
                    (pl.col("horizon_score") > q25) & (pl.col("horizon_score") <= q50),
                ),
                (
                    "Q3",
                    (pl.col("horizon_score") > q50) & (pl.col("horizon_score") <= q75),
                ),
                ("Q4_strong", pl.col("horizon_score") > q75),
            )
            for label, mask in score_bands:
                subset = scored.filter(mask)
                if subset.height == 0:
                    continue
                by_score[label] = _slice_stats(subset)
    out["by_score_quartile"] = by_score

    return out


def format_precision_summary(summary: dict) -> list[str]:
    """Human-readable lines for the Precision summary dict (incl. nested slices)."""
    lines = ["Precision summary:"]
    skip = {"by_direction", "by_entry_reason", "by_rank", "by_score_quartile"}
    for key, val in summary.items():
        if key in skip:
            continue
        if isinstance(val, float):
            lines.append(f"   {key}: {val:.4f}")
        else:
            lines.append(f"   {key}: {val}")

    def _append_group(title: str, group: dict | None) -> None:
        if not group:
            return
        lines.append(f"\n{title}:")
        for name, stats in group.items():
            parts = [f"n={stats.get('n', 0)}"]
            for metric in (
                "mean_gross_ret",
                "mean_net_ret",
                "tp_rate",
                "sl_rate",
                "timeout_rate",
                "tb_tp_rate",
                "prec_tp_rate",
            ):
                if metric in stats and isinstance(stats[metric], float):
                    parts.append(f"{metric}={stats[metric]:.4f}")
            lines.append(f"   {name}: " + "  ".join(parts))

    _append_group("By entry reason", summary.get("by_entry_reason"))
    _append_group("By rank", summary.get("by_rank"))
    _append_group("By direction", summary.get("by_direction"))
    _append_group("By score quartile", summary.get("by_score_quartile"))
    return lines


def flatten_precision_summary_metrics(summary: dict) -> dict[str, float]:
    """Flatten nested summary slices into scalar MLflow metrics."""
    flat: dict[str, float] = {}
    for key, val in summary.items():
        if isinstance(val, (int, float)) and math.isfinite(float(val)):
            flat[key] = float(val)
    for group_key, prefix in (
        ("by_entry_reason", "entry"),
        ("by_rank", "rank"),
        ("by_direction", "dir"),
        ("by_score_quartile", "score"),
    ):
        group = summary.get(group_key) or {}
        for name, stats in group.items():
            tag = str(name).replace("-", "_").lower()
            for metric, mval in stats.items():
                if isinstance(mval, (int, float)) and math.isfinite(float(mval)):
                    flat[f"{prefix}_{tag}_{metric}"] = float(mval)
    return flat
