"""Materialize ``data/GOLDEN`` 1m CSV → Parquet for lazy Polars iteration.

CSV remains the source of truth until row counts and smoke hashes match.
Idempotent: re-running overwrites a symbol's parquet file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl

from src.utils.data import load_csv_data

DEFAULT_CSV_DIR = Path("data/GOLDEN")
DEFAULT_PARQUET_DIR = Path("data/GOLDEN_PARQUET")


@dataclass(frozen=True)
class MaterializeResult:
    symbol: str
    csv_rows: int
    parquet_rows: int
    parquet_path: Path

    @property
    def ok(self) -> bool:
        return self.csv_rows == self.parquet_rows


def symbol_from_csv_name(path: Path) -> str:
    """``ABB.NS.csv`` → ``ABB.NS``."""
    return path.stem


def list_golden_csv(csv_dir: Path = DEFAULT_CSV_DIR) -> list[Path]:
    return sorted(csv_dir.glob("*.csv"))


def materialize_symbol(
    csv_path: Path,
    parquet_dir: Path = DEFAULT_PARQUET_DIR,
) -> MaterializeResult:
    """Load one CSV via the shared loader and write a matching Parquet file."""
    parquet_dir.mkdir(parents=True, exist_ok=True)
    symbol = symbol_from_csv_name(csv_path)
    df = load_csv_data(csv_path, datetime_col="date")
    out = parquet_dir / f"{symbol}.parquet"
    df.write_parquet(out)
    # Round-trip count check against the written file (not a second CSV parse).
    n_parquet = pl.scan_parquet(out).select(pl.len()).collect().item()
    return MaterializeResult(
        symbol=symbol,
        csv_rows=df.height,
        parquet_rows=int(n_parquet),
        parquet_path=out,
    )


def materialize_golden(
    csv_dir: Path = DEFAULT_CSV_DIR,
    parquet_dir: Path = DEFAULT_PARQUET_DIR,
    *,
    symbols: list[str] | None = None,
) -> list[MaterializeResult]:
    """Materialize all (or selected) GOLDEN symbols. Safe to re-run."""
    paths = list_golden_csv(csv_dir)
    if symbols is not None:
        want = set(symbols)
        paths = [p for p in paths if symbol_from_csv_name(p) in want]
    return [materialize_symbol(p, parquet_dir) for p in paths]


def load_1m_lazy(
    symbol: str,
    parquet_dir: Path = DEFAULT_PARQUET_DIR,
) -> pl.LazyFrame:
    path = parquet_dir / f"{symbol}.parquet"
    return pl.scan_parquet(path)


def smoke_round_trip(
    symbol: str,
    csv_dir: Path = DEFAULT_CSV_DIR,
    parquet_dir: Path = DEFAULT_PARQUET_DIR,
) -> MaterializeResult:
    """Materialize one symbol and assert CSV vs Parquet row counts match."""
    csv_path = csv_dir / f"{symbol}.csv"
    result = materialize_symbol(csv_path, parquet_dir)
    if not result.ok:
        raise AssertionError(
            f"row-count mismatch {symbol}: csv={result.csv_rows} "
            f"parquet={result.parquet_rows}"
        )
    return result
