"""Daily ATM IV store contract for M9 V1 (single-name).

Until ``data/GOLDEN_IV/atm_iv_daily.parquet`` exists, ``load_atm_iv_daily`` raises
with a pointer to the M9-0 acquisition doc.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

DEFAULT_IV_PATH = Path("data/GOLDEN_IV/atm_iv_daily.parquet")

REQUIRED_COLS: tuple[str, ...] = (
    "symbol",
    "date_only",
    "atm_iv_pct",
)


class IvStoreMissingError(FileNotFoundError):
    """Raised when the M9-0 IV panel has not been materialised."""


def load_atm_iv_daily(path: Path = DEFAULT_IV_PATH) -> pl.DataFrame:
    """Load the daily ATM IV panel; fail fast if M9-0 is incomplete."""
    if not path.exists():
        raise IvStoreMissingError(
            f"ATM IV store not found at {path}. "
            "Acquire single-name IV per docs/next/horizon-m9-0-data-acquisition.md "
            "before running authority V1."
        )
    df = pl.read_parquet(path)
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"IV store missing columns {missing}")
    return df.select(
        [
            pl.col("symbol").cast(pl.Utf8),
            pl.col("date_only").cast(pl.Date),
            pl.col("atm_iv_pct").cast(pl.Float64),
            *[
                pl.col(c)
                for c in (
                    "atm_strike",
                    "underlying_close",
                    "expiry",
                    "source",
                    "dte",
                    "premium_ce",
                    "premium_pe",
                    "straddle",
                )
                if c in df.columns
            ],
        ]
    )


def attach_lagged_atm_iv(
    panel: pl.DataFrame,
    iv: pl.DataFrame,
    *,
    symbol_col: str = "symbol",
    date_col: str = "date_only",
) -> pl.DataFrame:
    """
    Join last ATM IV strictly before the panel date (no same-session look-ahead).

    IV marked on T becomes legal on T+1; holidays asof to the last prior mark.
    """
    # IV marked on T is legal from T+1 (no same-session look-ahead).
    # asof-backward then covers holidays: last mark strictly before the bar date.
    legal = (
        iv.sort([symbol_col, date_col])
        .select([symbol_col, date_col, "atm_iv_pct"])
        .with_columns(
            **{date_col: pl.col(date_col).dt.offset_by("1d")}
        )
    )
    return (
        panel.sort([symbol_col, date_col])
        .join_asof(
            legal.sort([symbol_col, date_col]),
            by=symbol_col,
            on=date_col,
            strategy="backward",
            check_sortedness=False,
        )
    )


def coverage_report(
    panel: pl.DataFrame,
    *,
    iv_col: str = "atm_iv_pct",
) -> dict[str, float | int]:
    """Share of rows with usable IV — M9-0 coverage gate input."""
    n = panel.height
    if n == 0:
        return {"n": 0, "n_iv": 0, "coverage": float("nan")}
    n_iv = int(panel[iv_col].is_not_null().sum())
    return {"n": n, "n_iv": n_iv, "coverage": n_iv / n}
