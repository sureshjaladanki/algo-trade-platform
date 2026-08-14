"""Tier 3 Precision eval — report-only diagnostics (P4–P11, P1r, P2n, P3s)."""

from __future__ import annotations

import datetime as dt

import numpy as np
import polars as pl

from src.labels.triple_barrier import ARCHIVE_ROUND_TRIP_COST, ROUND_TRIP_COST
from src.precision.eval.constants import MetricResult, k_for
from src.precision.precision import (
    SPREAD_CEILING_LONG_BPS,
    SPREAD_CEILING_SHORT_BPS,
    _hard_gates_ok,
    resolve_frozen_path,
)
from src.precision.session import WAIT_MINUTES

_RANK_BANDS = (
    ("1-2", (pl.col("horizon_rank") >= 1) & (pl.col("horizon_rank") <= 2)),
    ("3-5", (pl.col("horizon_rank") >= 3) & (pl.col("horizon_rank") <= 5)),
)
_TOD_BANDS = (
    ("morning", pl.col("decision_bar").dt.time() < dt.time(11, 0)),
    (
        "midday",
        (pl.col("decision_bar").dt.time() >= dt.time(11, 0))
        & (pl.col("decision_bar").dt.time() < dt.time(13, 0)),
    ),
    ("afternoon", pl.col("decision_bar").dt.time() >= dt.time(13, 0)),
)


def diagnostic_metrics(
    gated: pl.DataFrame,
    direction: str,
    features_1m: pl.DataFrame,
    rng: np.random.Generator,
) -> list[MetricResult]:
    """P4–P11 plus P1r / P2n / P3s companions. Never ship-lock alone."""
    results: list[MetricResult] = []
    results.extend(p4_exit_mix(gated, direction))
    results.extend(p5_setup_fallback(gated, direction))
    results.extend(p6_rank_bands(gated, direction))
    results.extend(p7_edge_quartiles(gated, direction))
    results.append(p8_coverage(gated, direction))
    results.extend(p9_fill_hygiene(gated, direction))
    results.extend(p11_monetization(gated, direction))
    results.extend(p1r_skip_reasons(gated, direction))
    results.extend(p3s_companions(gated, direction))
    results.append(p2n_drift_null(gated, direction, features_1m, rng))
    return results


def p4_exit_mix(gated: pl.DataFrame, direction: str) -> list[MetricResult]:
    fires = _fires(gated)
    n = fires.height
    if n == 0:
        return [MetricResult("P4to", direction, None, None, None, 0, None, "empty")]

    def _rate(reason: str) -> float:
        return fires.filter(pl.col("exit_reason") == reason).height / n

    tp, sl, timeout, mis = (
        _rate("TP"),
        _rate("SL"),
        _rate("TIMEOUT"),
        _rate("MIS_FLATTEN"),
    )
    labeled0 = fires.filter(pl.col("tb_label") == 0)
    to_among_0 = (
        labeled0.filter(pl.col("exit_reason") == "TIMEOUT").height / labeled0.height
        if labeled0.height
        else float("nan")
    )
    return [
        MetricResult(
            "P4to",
            direction,
            timeout,
            None,
            None,
            n,
            None,
            (
                f"TP={tp:.3f} SL={sl:.3f} TO={timeout:.3f} MIS={mis:.3f} "
                f"TO|tb0={to_among_0:.3f} n0={labeled0.height}"
            ),
        )
    ]


def p5_setup_fallback(gated: pl.DataFrame, direction: str) -> list[MetricResult]:
    fires = _fires(gated)
    setup = fires.filter(pl.col("entry_reason") == "setup")
    fallback = fires.filter(pl.col("entry_reason") == "fallback")
    n_s, n_f = setup.height, fallback.height
    if n_s == 0 or n_f == 0:
        return [
            MetricResult(
                "P5",
                direction,
                None,
                None,
                None,
                fires.height,
                None,
                f"setup_n={n_s} fallback_n={n_f}",
            )
        ]
    mean_s = float(setup["prec_net"].mean())
    mean_f = float(fallback["prec_net"].mean())
    return [
        MetricResult(
            "P5",
            direction,
            mean_s - mean_f,
            None,
            None,
            fires.height,
            None,
            f"setup={mean_s:.4f} n={n_s} fallback={mean_f:.4f} n={n_f}",
        )
    ]


def p6_rank_bands(gated: pl.DataFrame, direction: str) -> list[MetricResult]:
    """Horizon inversion bleed detector — not a Precision ship gate."""
    k = k_for(direction)
    results: list[MetricResult] = []
    nets: dict[str, float] = {}
    for label, mask in _RANK_BANDS:
        if label == "3-5" and k < 3:
            continue
        band = gated.filter(mask)
        fires = band.filter(pl.col("precision_fire"))
        n_ep, n_fire = band.height, fires.height
        fire_rate = n_fire / n_ep if n_ep else 0.0
        mean_net = float(fires["prec_net"].mean()) if n_fire else float("nan")
        nets[label] = mean_net
        name = "P6_12" if label == "1-2" else "P6_35"
        results.append(
            MetricResult(
                name,
                direction,
                mean_net if n_fire else None,
                None,
                None,
                n_fire,
                None,
                f"fire_rate={fire_rate:.3f} episodes={n_ep}",
            )
        )
    if "1-2" in nets and "3-5" in nets and np.isfinite(nets["1-2"]) and np.isfinite(
        nets["3-5"]
    ):
        results.append(
            MetricResult(
                "P6",
                direction,
                nets["1-2"] - nets["3-5"],
                None,
                None,
                gated.filter(pl.col("precision_fire")).height,
                None,
                "rank1-2 minus 3-5 (Horizon bleed)",
            )
        )
    return results


def p7_edge_quartiles(gated: pl.DataFrame, direction: str) -> list[MetricResult]:
    """Sleeve-separate edge_score quartiles. Pooled raw scores are forbidden."""
    fires = _fires(gated).drop_nulls(subset=["edge_score", "prec_net"])
    if fires.height < 4:
        return [MetricResult("P7", direction, None, None, None, fires.height, None, "thin")]

    q25, q50, q75 = fires.select(
        pl.col("edge_score").quantile(0.25).alias("q25"),
        pl.col("edge_score").quantile(0.50).alias("q50"),
        pl.col("edge_score").quantile(0.75).alias("q75"),
    ).row(0)
    bands = (
        ("Q1", fires.filter(pl.col("edge_score") <= q25)),
        ("Q2", fires.filter(
            (pl.col("edge_score") > q25) & (pl.col("edge_score") <= q50)
        )),
        ("Q3", fires.filter(
            (pl.col("edge_score") > q50) & (pl.col("edge_score") <= q75)
        )),
        ("Q4", fires.filter(pl.col("edge_score") > q75)),
    )
    means = []
    parts = []
    for label, subset in bands:
        m = float(subset["prec_net"].mean()) if subset.height else float("nan")
        means.append(m)
        parts.append(f"{label}={m:.4f} n={subset.height}")
    q4_q1 = (
        means[3] - means[0]
        if np.isfinite(means[0]) and np.isfinite(means[3])
        else None
    )
    return [
        MetricResult(
            "P7",
            direction,
            q4_q1,
            None,
            None,
            fires.height,
            None,
            " ".join(parts),
        )
    ]


def p8_coverage(gated: pl.DataFrame, direction: str) -> MetricResult:
    n_ep = gated.height
    fires = gated.filter(pl.col("precision_fire"))
    n_fire = fires.height
    n_sess = gated.select(pl.col("date_only").n_unique()).item() if n_ep else 0
    fire_rate = n_fire / n_ep if n_ep else 0.0
    gate_pass = (
        float(gated["gate_pass"].mean()) if "gate_pass" in gated.columns else float("nan")
    )
    return MetricResult(
        "P8",
        direction,
        fire_rate,
        None,
        None,
        n_ep,
        None,
        f"fires={n_fire} sess={n_sess} gate_pass={gate_pass:.3f}",
    )


def p9_fill_hygiene(gated: pl.DataFrame, direction: str) -> list[MetricResult]:
    fires = _fires(gated)
    n = fires.height
    if n == 0:
        return [MetricResult("P9", direction, None, None, None, 0, None, "empty")]

    wait = fires.drop_nulls(subset=["wait_minutes"])
    mean_wait = float(wait["wait_minutes"].mean()) if wait.height else float("nan")
    spread = fires.drop_nulls(subset=["spread_proxy_bps"])
    mean_spread = (
        float(spread["spread_proxy_bps"].mean()) if spread.height else float("nan")
    )
    room_tp = (
        float(fires["dist_to_tp_bps"].mean())
        if "dist_to_tp_bps" in fires.columns
        else float("nan")
    )
    afternoon = (
        float(fires["afternoon_cover_risk"].mean())
        if "afternoon_cover_risk" in fires.columns
        else float("nan")
    )
    fresh = (
        float(fires["fresh_flip"].mean()) if "fresh_flip" in fires.columns else float("nan")
    )
    n_exp = int(fires.filter(pl.col("is_expiry_day")).height)
    tod = " ".join(
        f"{label}={fires.filter(mask).height / n:.2f}" for label, mask in _TOD_BANDS
    )
    return [
        MetricResult(
            "P9",
            direction,
            mean_wait if np.isfinite(mean_wait) else None,
            None,
            None,
            n,
            None,
            (
                f"wait={mean_wait:.2f} spread={mean_spread:.1f} "
                f"room_tp={room_tp:.1f} cover={afternoon:.3f} "
                f"fresh_flip={fresh:.3f} expiry_n={n_exp} {tod}"
            ),
        )
    ]


def p11_monetization(gated: pl.DataFrame, direction: str) -> list[MetricResult]:
    fires = _fires(gated).drop_nulls(subset=["tb_label"])
    n = fires.height
    if n == 0:
        return [MetricResult("P11", direction, None, None, None, 0, None, "empty")]
    tb_tp = fires.filter(pl.col("tb_label") == 1).height / n
    prec_tp = fires.filter(pl.col("exit_reason") == "TP").height / n
    overfire = fires.filter(pl.col("tb_label") != 1).height / n
    return [
        MetricResult(
            "P11",
            direction,
            prec_tp - tb_tp,
            None,
            None,
            n,
            None,
            f"prec_tp={prec_tp:.3f} tb_tp={tb_tp:.3f} overfire_non+1={overfire:.3f}",
        )
    ]


def p1r_skip_reasons(gated: pl.DataFrame, direction: str) -> list[MetricResult]:
    """mean(Naive | skip=r) − mean(Naive | Fired) per skip reason."""
    finite = gated.filter(pl.col("naive_net").is_finite())
    fired = finite.filter(pl.col("precision_fire"))
    skipped = finite.filter(~pl.col("precision_fire"))
    if fired.height == 0 or skipped.height == 0:
        return [MetricResult("P1r", direction, None, None, None, 0, None, "empty")]

    fire_mean = float(fired["naive_net"].mean())
    reasons = (
        skipped.drop_nulls(subset=["exit_reason"])
        .get_column("exit_reason")
        .unique()
        .sort()
        .to_list()
    )
    _REASON_TAG = {
        "CONVICTION": "conv",
        "HARD_GATE": "hard",
        "NO_REENTRY": "reent",
        "MISSING_PATH": "path",
        "EMPTY_WAIT": "wait",
        "NO_CHASE": "chase",
        "RANK_SKIP": "rank",
        "SIZE": "size",
    }
    results: list[MetricResult] = []
    for reason in reasons:
        bucket = skipped.filter(pl.col("exit_reason") == reason)
        point = float(bucket["naive_net"].mean()) - fire_mean
        tag = _REASON_TAG.get(str(reason), str(reason)[:4])
        results.append(
            MetricResult(
                f"P1r_{tag}",
                direction,
                point,
                None,
                None,
                bucket.height,
                None,
                f"skip={reason} vs fired {fire_mean:.4f}",
            )
        )
    if not results:
        results.append(
            MetricResult("P1r", direction, None, None, None, skipped.height, None, "no reasons")
        )
    return results


def p3s_companions(gated: pl.DataFrame, direction: str) -> list[MetricResult]:
    fires = _fires(gated)
    n = fires.height
    if n == 0:
        return [
            MetricResult("P3s", direction, None, None, None, 0, None, "empty"),
            MetricResult("P3sz", direction, None, None, None, 0, None, "empty"),
        ]
    stress = float((fires["gross_ret"] - ARCHIVE_ROUND_TRIP_COST).mean())
    sized = fires.filter(pl.col("size_mult") > 0)
    if sized.height:
        w = sized["size_mult"].to_numpy()
        x = (sized["gross_ret"] - ROUND_TRIP_COST).to_numpy()
        sized_mean = float(np.average(x, weights=w))
    else:
        sized_mean = None
    return [
        MetricResult(
            "P3s",
            direction,
            stress,
            None,
            None,
            n,
            None,
            f"c={ARCHIVE_ROUND_TRIP_COST:.4f} archive stress",
        ),
        MetricResult(
            "P3sz",
            direction,
            sized_mean,
            None,
            None,
            sized.height,
            None,
            "size-weighted companion (not a gate)",
        ),
    ]


def p2n_drift_null(
    gated: pl.DataFrame,
    direction: str,
    features_1m: pl.DataFrame,
    rng: np.random.Generator,
) -> MetricResult:
    """
    Random 1m fill inside the wait window (hard gates still applied).

    If random timing ≈ Precision P2, the lift may be post-signal drift.
    """
    fires = gated.filter(
        pl.col("precision_fire")
        & pl.col("naive_net").is_finite()
        & pl.col("decision_close").is_not_null()
    )
    if fires.height == 0:
        return MetricResult("P2n", direction, None, None, None, 0, None, "empty")

    by_symbol = {
        str(key[0] if isinstance(key, tuple) else key): grp
        for key, grp in features_1m.sort(["symbol", "date"]).group_by(
            "symbol", maintain_order=True
        )
    }
    lifts: list[float] = []
    for ep in fires.iter_rows(named=True):
        net = _random_fill_net(ep, by_symbol, rng)
        if net is None:
            continue
        lifts.append(net - float(ep["naive_net"]))

    n = len(lifts)
    if n == 0:
        return MetricResult("P2n", direction, None, None, None, 0, None, "no random fills")
    point = float(np.mean(lifts))
    return MetricResult(
        "P2n",
        direction,
        point,
        None,
        None,
        n,
        None,
        "random wait-window fill vs naive (drift-null)",
    )


def _fires(gated: pl.DataFrame) -> pl.DataFrame:
    return gated.filter(pl.col("precision_fire") & pl.col("prec_net").is_finite())


def _random_fill_net(
    ep: dict,
    by_symbol: dict[str, pl.DataFrame],
    rng: np.random.Generator,
) -> float | None:
    bars = by_symbol.get(str(ep["symbol"]))
    atr = ep.get("atr_pct")
    decision_bar = ep["decision_bar"]
    decision_close = ep["decision_close"]
    vertical = ep["vertical_deadline"]
    if bars is None or atr is None or atr <= 0:
        return None

    entry_window_end = decision_bar + dt.timedelta(minutes=WAIT_MINUTES - 1)
    wait = bars.filter(
        (pl.col("date") >= decision_bar) & (pl.col("date") <= entry_window_end)
    ).sort("date")
    if wait.height == 0:
        return None
    wait = wait.with_columns(
        m1_range_compression=(pl.col("atr_1m_5") / pl.col("close")) / atr,
    )
    ceiling = (
        SPREAD_CEILING_LONG_BPS
        if ep["horizon_direction"] == "long"
        else SPREAD_CEILING_SHORT_BPS
    )
    eligible = [
        row
        for row in wait.iter_rows(named=True)
        if _hard_gates_ok(
            row,
            direction=ep["horizon_direction"],
            decision_close=float(decision_close),
            tp_w=float(ep["tp_w"]),
            sl_w=float(ep["sl_w"]),
            spread_ceiling=ceiling,
            vertical_deadline=vertical,
        )
    ]
    if not eligible:
        return None
    bar = eligible[int(rng.integers(0, len(eligible)))]
    hold = bars.filter(
        (pl.col("date") > bar["date"]) & (pl.col("date") <= vertical)
    ).sort("date")
    path = resolve_frozen_path(
        hold,
        direction=ep["horizon_direction"],
        entry_px=float(bar["close"]),
        tp_w=float(ep["tp_w"]),
        sl_w=float(ep["sl_w"]),
        vertical_deadline=vertical,
    )
    return float(path["gross_ret"]) - ROUND_TRIP_COST
