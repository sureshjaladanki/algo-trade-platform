"""Tier 3 Precision rules engine — bounded-wait entry + frozen TB exits (v1)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

import polars as pl

from src.labels.triple_barrier import TP_PENETRATION
from src.precision.session import (
    AFTERNOON_COVER_START,
    DECISION_BAR_MINUTES,
    HORIZON_MINUTES,
    MIS_FLAT_BY,
    TOP_K,
    WAIT_MINUTES,
    long_entry_ok_expr,
    short_entry_ok_expr,
)
from src.regime.types import DailyRegime, IntradayRegime

ExitReason = Literal["TP", "SL", "TIMEOUT", "REGIME_FLIP", "MIS_FLATTEN", "SKIP"]

TRADEABLE_DAILY_REGIMES = [
    DailyRegime.SUPPORTIVE.value,
    DailyRegime.AMBIGUOUS.value,
]

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


def build_decision_registry(
    horizon_scored: pl.DataFrame,
    top_k: int = TOP_K,
) -> pl.DataFrame:
    """
    Narrow Horizon scores to the Precision universe (top-K / bottom-K + TB gates).

    Expects columns from `predict_horizon_gbm` joined with TB geometry.
    """
    required = {
        "symbol",
        "date",
        "horizon_rank",
        "horizon_score",
        "horizon_direction",
        "daily_regime",
        "intraday_regime",
        "close",
        "atr_pct",
        "long_tp_w",
        "long_sl_w",
        "short_tp_w",
        "short_sl_w",
        "tb_eligible_long",
        "tb_eligible_short",
    }
    missing = required - set(horizon_scored.columns)
    if missing:
        raise ValueError(f"horizon_scored missing columns: {sorted(missing)}")

    df = horizon_scored.with_columns(
        date_only=pl.col("date").dt.date(),
        time_only=pl.col("date").dt.time(),
        decision_bar=pl.col("date"),
        decision_close=pl.col("close"),
    )

    long_mask = (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_UP.value)
        & (pl.col("horizon_direction") == "long")
        & pl.col("tb_eligible_long")
        & long_entry_ok_expr("time_only")
        & (pl.col("horizon_rank") <= top_k)
    )
    short_mask = (
        pl.col("daily_regime").is_in(TRADEABLE_DAILY_REGIMES)
        & (pl.col("intraday_regime") == IntradayRegime.TREND_DOWN.value)
        & (pl.col("horizon_direction") == "short")
        & pl.col("tb_eligible_short")
        & short_entry_ok_expr("time_only")
        & (pl.col("horizon_rank") <= top_k)
    )

    # HIGH_VOL / HOSTILE: no new Precision entries (cascade contract).
    blocked = pl.col("intraday_regime").is_in(
        [IntradayRegime.HIGH_VOL.value, IntradayRegime.NO_TRADE.value]
    ) | (pl.col("daily_regime") == DailyRegime.NO_TRADE.value)

    # MIS flatten is calendar-day 15:00 (bar-start clock), not decision+60 alone.
    mis_deadline = (
        pl.col("decision_bar").dt.truncate("1d")
        + dt.timedelta(
            hours=MIS_FLAT_BY.hour,
            minutes=MIS_FLAT_BY.minute,
        )
    )
    registry = df.filter((long_mask | short_mask) & ~blocked).with_columns(
        vertical_deadline=pl.min_horizontal(
            pl.col("decision_bar") + dt.timedelta(minutes=HORIZON_MINUTES),
            mis_deadline,
        ),
        wait_start=pl.col("decision_bar")
        + dt.timedelta(minutes=DECISION_BAR_MINUTES),
    )
    return registry.sort(["decision_bar", "horizon_direction", "horizon_rank"])


def run_precision_rules(
    registry: pl.DataFrame,
    stock_1m: pl.DataFrame,
    *,
    wait_minutes: int = WAIT_MINUTES,
) -> pl.DataFrame:
    """
    Rules-first Precision: bounded-wait 1m entry → frozen TB exits.

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
        symbol = ep["symbol"]
        direction = ep["horizon_direction"]
        session_day = ep["date_only"]
        wait_start = ep["wait_start"]
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
            "decision_bar": ep["decision_bar"],
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
            rows.append(_skip_row(base, "SKIP"))
            continue

        bars = by_symbol.get(symbol)
        if bars is None or atr_pct is None or atr_pct <= 0:
            rows.append(_skip_row(base, "SKIP"))
            continue

        wait_end = wait_start + dt.timedelta(minutes=wait_minutes - 1)
        wait_bars = bars.filter(
            (pl.col("date") >= wait_start) & (pl.col("date") <= wait_end)
        ).sort("date")

        if wait_bars.height == 0:
            rows.append(_skip_row(base, "SKIP"))
            continue

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
            rows.append(_skip_row(base, "SKIP"))
            continue

        afternoon_risk = bool(fill.get("afternoon_cover_risk", False))
        size_mult = size_mult_from_rank(rank, afternoon_cover_risk=afternoon_risk)
        if size_mult <= 0:
            rows.append(_skip_row(base, "SKIP"))
            continue

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

        rows.append(
            {
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
        )

    if not rows:
        return _empty_trades()
    return pl.DataFrame(rows)


def _find_entry(
    wait_bars: pl.DataFrame,
    *,
    direction: str,
    decision_close: float,
    tp_w: float,
    sl_w: float,
    spread_ceiling: float,
    vertical_deadline,
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
    vertical_deadline,
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

    t = bar["date"].time() if hasattr(bar["date"], "time") else bar.get("time_only")
    if direction == "short" and t is not None and t >= AFTERNOON_COVER_START:
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
    vertical_deadline,
) -> dict:
    """Walk 1m bars until TP / SL / MIS / timeout. No trail in v1."""
    for bar in hold_bars.iter_rows(named=True):
        ts = bar["date"]
        high = float(bar["high"])
        low = float(bar["low"])
        close = float(bar["close"])
        t = ts.time() if hasattr(ts, "time") else None

        if t is not None and t >= MIS_FLAT_BY:
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


def _exit_at(ts, exit_px: float, entry_px: float, direction: str, reason: str) -> dict:
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


def summarize_precision_trades(trades: pl.DataFrame) -> dict:
    """Hit-rate / PnL diagnostics vs TB label expectations."""
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
    out["mean_size_mult"] = float(fires["size_mult"].mean())
    for reason in ("TP", "SL", "TIMEOUT", "MIS_FLATTEN"):
        out[f"exit_{reason.lower()}"] = fires.filter(
            pl.col("exit_reason") == reason
        ).height

    for direction, label_col in (
        ("long", "tb_label_long"),
        ("short", "tb_label_short"),
    ):
        subset = fires.filter(pl.col("horizon_direction") == direction).drop_nulls(
            subset=[label_col]
        )
        if subset.height == 0:
            continue
        tb_tp = subset.filter(pl.col(label_col) == 1).height
        prec_tp = subset.filter(pl.col("exit_reason") == "TP").height
        out[f"{direction}_n"] = subset.height
        out[f"{direction}_tb_tp_rate"] = tb_tp / subset.height
        out[f"{direction}_prec_tp_rate"] = prec_tp / subset.height

    return out
