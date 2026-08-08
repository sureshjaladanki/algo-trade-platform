"""Post–Phase 1 Precision audits — rank 1–2 root-cause + entry composition."""

from __future__ import annotations

import datetime as dt

import polars as pl

from src.labels.triple_barrier import ROUND_TRIP_COST

_RANK_BANDS = (
    ("1-2", (pl.col("horizon_rank") >= 1) & (pl.col("horizon_rank") <= 2)),
    ("3-5", (pl.col("horizon_rank") >= 3) & (pl.col("horizon_rank") <= 5)),
    ("6-8", (pl.col("horizon_rank") >= 6) & (pl.col("horizon_rank") <= 8)),
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


def diagnose_rank_root_cause(trades: pl.DataFrame) -> dict[str, dict]:
    """
    Rank-band root-cause for the Phase 2 skip lock decision.

    Reports fires PnL / exit mix, entry_reason mix, gate-pass rate (all
    episodes), and chase proxies (fresh regime flip, wait delay).
    """
    if trades.height == 0:
        return {}

    out: dict[str, dict] = {}
    for label, mask in _RANK_BANDS:
        band = trades.filter(mask)
        if band.height == 0:
            continue
        out[label] = _rank_band_stats(band)
    return out


def audit_entry_composition(trades: pl.DataFrame) -> dict[str, dict]:
    """
    Setup vs fallback cohort mix — rank / direction / TOD / chase proxies.

    Explains thin-n setup sign flips (e.g. A −5 vs B −20) before any
    setup-or-skip lever.
    """
    fires = trades.filter(pl.col("precision_fire"))
    if fires.height == 0:
        return {}

    out: dict[str, dict] = {}
    for reason in ("setup", "fallback"):
        cohort = fires.filter(pl.col("entry_reason") == reason)
        if cohort.height == 0:
            continue
        out[reason] = _composition_stats(cohort)
    return out


def format_phase2_diagnostics(
    rank_diag: dict[str, dict],
    entry_audit: dict[str, dict],
) -> list[str]:
    """Human-readable lines for rank + entry composition audits."""
    lines: list[str] = []
    if rank_diag:
        lines.append("\nRank root-cause diagnostic:")
        for label, stats in rank_diag.items():
            lines.append(f"   {label}: {_format_flat(stats)}")
    if entry_audit:
        lines.append("\nSetup vs fallback composition:")
        for label, stats in entry_audit.items():
            lines.append(f"   {label}: {_format_flat(stats)}")
    return lines


def flatten_phase2_diagnostics(
    rank_diag: dict[str, dict],
    entry_audit: dict[str, dict],
) -> dict[str, float]:
    """Scalar MLflow metrics for Phase 2 audits."""
    flat: dict[str, float] = {}
    for label, stats in rank_diag.items():
        tag = label.replace("-", "_")
        for key, val in stats.items():
            if isinstance(val, (int, float)):
                flat[f"rankdiag_{tag}_{key}"] = float(val)
    for label, stats in entry_audit.items():
        for key, val in stats.items():
            if isinstance(val, (int, float)):
                flat[f"entryaudit_{label}_{key}"] = float(val)
    return flat


def _rank_band_stats(band: pl.DataFrame) -> dict[str, float | int]:
    n_ep = band.height
    fires = band.filter(pl.col("precision_fire"))
    n_fire = fires.height
    stats: dict[str, float | int] = {
        "episodes": n_ep,
        "fires": n_fire,
        "fire_rate": n_fire / n_ep,
        "gate_pass_rate": float(band["gate_pass"].mean()),
    }
    if "bars_since_regime_flip" in band.columns:
        flip = band.drop_nulls(subset=["bars_since_regime_flip"])
        if flip.height:
            stats["fresh_flip_share"] = (
                flip.filter(pl.col("bars_since_regime_flip") <= 1).height / flip.height
            )
            stats["mean_bars_since_flip"] = float(flip["bars_since_regime_flip"].mean())

    if n_fire == 0:
        return stats

    mean_gross = float(fires["gross_ret"].mean())
    stats.update(
        {
            "mean_gross_ret": mean_gross,
            "mean_net_ret": mean_gross - ROUND_TRIP_COST,
            "tp_rate": fires.filter(pl.col("exit_reason") == "TP").height / n_fire,
            "sl_rate": fires.filter(pl.col("exit_reason") == "SL").height / n_fire,
            "timeout_rate": (
                fires.filter(pl.col("exit_reason") == "TIMEOUT").height / n_fire
            ),
            "setup_share": (
                fires.filter(pl.col("entry_reason") == "setup").height / n_fire
            ),
            "fallback_share": (
                fires.filter(pl.col("entry_reason") == "fallback").height / n_fire
            ),
            "long_share": (
                fires.filter(pl.col("horizon_direction") == "long").height / n_fire
            ),
            "afternoon_cover_share": float(fires["afternoon_cover_risk"].mean()),
        }
    )
    wait = fires.drop_nulls(subset=["wait_minutes"])
    if wait.height:
        stats["mean_wait_minutes"] = float(wait["wait_minutes"].mean())
    return stats


def _composition_stats(cohort: pl.DataFrame) -> dict[str, float | int]:
    n = cohort.height
    mean_gross = float(cohort["gross_ret"].mean())
    stats: dict[str, float | int] = {
        "n": n,
        "mean_gross_ret": mean_gross,
        "mean_net_ret": mean_gross - ROUND_TRIP_COST,
        "long_share": (
            cohort.filter(pl.col("horizon_direction") == "long").height / n
        ),
        "short_share": (
            cohort.filter(pl.col("horizon_direction") == "short").height / n
        ),
        "rank_1_2_share": (
            cohort.filter(pl.col("horizon_rank") <= 2).height / n
        ),
        "rank_3_5_share": (
            cohort.filter(
                (pl.col("horizon_rank") >= 3) & (pl.col("horizon_rank") <= 5)
            ).height
            / n
        ),
        "mean_edge_score": float(cohort["edge_score"].mean()),
        "tp_rate": cohort.filter(pl.col("exit_reason") == "TP").height / n,
        "sl_rate": cohort.filter(pl.col("exit_reason") == "SL").height / n,
        "timeout_rate": cohort.filter(pl.col("exit_reason") == "TIMEOUT").height / n,
    }
    for label, mask in _TOD_BANDS:
        stats[f"tod_{label}_share"] = cohort.filter(mask).height / n
    if "bars_since_regime_flip" in cohort.columns:
        flip = cohort.drop_nulls(subset=["bars_since_regime_flip"])
        if flip.height:
            stats["fresh_flip_share"] = (
                flip.filter(pl.col("bars_since_regime_flip") <= 1).height / flip.height
            )
            stats["mean_bars_since_flip"] = float(flip["bars_since_regime_flip"].mean())
    return stats


def _format_flat(stats: dict) -> str:
    parts = []
    for key, val in stats.items():
        if isinstance(val, float):
            parts.append(f"{key}={val:.4f}")
        else:
            parts.append(f"{key}={val}")
    return "  ".join(parts)
