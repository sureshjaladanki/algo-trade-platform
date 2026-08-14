"""Tier 2 Horizon eval — hygiene flags, sleeve mask, and scored panel prep."""

from __future__ import annotations

import polars as pl

from src.horizon.eval.constants import (
    APPLY_L1_LONG,
    APPLY_S1_SHORT,
    CIRCUIT_RANGE_EPS,
    H_BARS,
    _EXPIRY_WEEKDAY,
    _SLEEVE,
    _TRADEABLE_DAILY,
    side_sign,
)


def annotate_hygiene_flags(df: pl.DataFrame) -> pl.DataFrame:
    """
    Eval-only circuit / expiry flags on the full bar panel.

    Forward circuit look uses the next ``H_BARS`` same-session bars (diagnostic
    only — never a training feature). Idempotent if flags already present.
    """
    if {"is_circuit_bar", "fwd_circuit_hit", "is_expiry_day"}.issubset(df.columns):
        return df

    out = df
    if "date_only" not in out.columns:
        out = out.with_columns(date_only=pl.col("date").dt.date())
    if "range_pct" not in out.columns:
        out = out.with_columns(
            range_pct=(pl.col("high") - pl.col("low"))
            / pl.col("close").shift(1).over("symbol")
        )

    out = out.sort(["symbol", "date"]).with_columns(
        is_circuit_bar=(
            (pl.col("high") == pl.col("low"))
            | (
                pl.col("range_pct").is_not_null()
                & (pl.col("range_pct") <= CIRCUIT_RANGE_EPS)
            )
        ),
        # Thursday for 2018–2019 folds; post-2025 Tuesday change is OOS.
        is_expiry_day=pl.col("date").dt.weekday() == _EXPIRY_WEEKDAY,
    )

    shift_cols: list[pl.Expr] = []
    for h in range(1, H_BARS + 1):
        shift_cols.append(
            pl.col("is_circuit_bar").shift(-h).over("symbol").alias(f"_cir_{h}")
        )
        shift_cols.append(
            pl.col("date_only").shift(-h).over("symbol").alias(f"_d_{h}")
        )
    drop_cols = [f"_cir_{h}" for h in range(1, H_BARS + 1)] + [
        f"_d_{h}" for h in range(1, H_BARS + 1)
    ]
    return (
        out.with_columns(shift_cols)
        .with_columns(
            fwd_circuit_hit=pl.any_horizontal(
                [
                    pl.col(f"_cir_{h}").fill_null(False)
                    & (pl.col(f"_d_{h}") == pl.col("date_only"))
                    for h in range(1, H_BARS + 1)
                ]
            )
        )
        .drop(drop_cols)
    )


def eligible_expr(direction: str) -> pl.Expr:
    """Same sleeve mask as production predict + MIS-safe label + finite score/y."""
    cfg = _SLEEVE[direction]
    return (
        pl.col("daily_regime").is_in(list(_TRADEABLE_DAILY))
        & (pl.col("intraday_regime") == cfg["intraday"])
        & cfg["entry_ok"]("time_only")
        & pl.col(cfg["valid_label"])
        & pl.col("horizon_score").is_finite()
        & pl.col("fwd_excess_ret").is_finite()
    )


def prepare_eval_panel(scored: pl.DataFrame, direction: str) -> pl.DataFrame:
    """
    Cascade-valid scored rows with eval-only sign convention.

    ``eval_score`` is higher = more actionable for both sleeves (Short flips).
    ``adj_excess`` folds Short's "more negative = better" into the same scale.
    Rank is recomputed descending on ``eval_score`` within each bar (matches
    production Long descending / Short ascending after the flip).

    Short applies S1 circuit/UC hygiene when ``APPLY_S1_SHORT`` (v1.1).
    Long applies L1 rank-3 floor when ``APPLY_L1_LONG`` (v1.1).
    """
    # Local imports avoid cycle: panel ↔ long_eval / short_eval.
    from src.horizon.eval.long_eval import apply_l1_rank3_floor
    from src.horizon.eval.short_eval import s1_circuit_ok_expr

    side = side_sign(direction)
    sleeve = _SLEEVE[direction]
    tb_col = sleeve["tb_col"]
    mfe_col = sleeve["mfe_col"]
    mfe_bps_col = sleeve["mfe_bps_col"]
    abs_peak_bar_col = sleeve["abs_peak_bar_col"]
    mfe50_first_bar_col = sleeve["mfe50_first_bar_col"]
    peak_bar_col = sleeve["peak_bar_col"]
    giveback_col = sleeve["giveback_col"]
    exit_h_col = sleeve["exit_h_col"]

    base = annotate_hygiene_flags(scored)
    if "time_only" not in base.columns:
        base = base.with_columns(time_only=pl.col("date").dt.time())

    mask = eligible_expr(direction)
    if direction == "short" and APPLY_S1_SHORT:
        mask = mask & s1_circuit_ok_expr()

    panel = (
        base.filter(mask)
        .with_columns(
            date_only=pl.col("date").dt.date(),
            time_only=pl.col("date").dt.time(),
            eval_score=pl.col("horizon_score") * side,
            adj_excess=pl.col("fwd_excess_ret") * side,
            tb_label=pl.col(tb_col),
            mfe_frac=pl.col(mfe_col),
            mfe_peak_bar=pl.col(peak_bar_col),
            giveback_frac=pl.col(giveback_col),
            tb_exit_h=pl.col(exit_h_col),
            direction=pl.lit(direction),
        )
        .with_columns(
            eval_rank=pl.col("eval_score")
            .rank(method="ordinal", descending=True)
            .over("date")
        )
    )
    # TP-floor Step 0 columns (optional — Short omits mfe50_first_bar).
    extras: list[pl.Expr] = []
    if mfe_bps_col in base.columns:
        extras.append(pl.col(mfe_bps_col).alias("mfe_bps"))
    if abs_peak_bar_col in base.columns:
        extras.append(pl.col(abs_peak_bar_col).alias("mfe_abs_peak_bar"))
    if mfe50_first_bar_col is not None and mfe50_first_bar_col in base.columns:
        extras.append(pl.col(mfe50_first_bar_col).alias("mfe50_first_bar"))
    if extras:
        panel = panel.with_columns(extras)
    if direction == "long" and APPLY_L1_LONG:
        panel = apply_l1_rank3_floor(panel)
    return panel
