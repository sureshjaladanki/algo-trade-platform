"""Smoke tests — fresh package import + Parquet round-trip (M0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.horizon.fresh import C_STAR, C_STAR_BPS, ROUND_TRIP_COST
from src.horizon.fresh.folds import FOLDS, PURGED_CV_SPIRIT
from src.horizon.fresh.parquet_store import smoke_round_trip
from src.horizon.fresh.production_lock import FROZEN_SURFACES


def test_friction_aliases() -> None:
    assert ROUND_TRIP_COST == 0.0020
    assert C_STAR == ROUND_TRIP_COST
    assert C_STAR_BPS == 20.0


def test_folds_ab_present() -> None:
    assert set(FOLDS) == {"A", "B"}
    assert PURGED_CV_SPIRIT.train_days == 420


def test_production_lock_surfaces() -> None:
    assert any("LONG_TOP_K" in s for s in FROZEN_SURFACES)


def test_parquet_smoke_abb() -> None:
    root = Path(__file__).resolve().parents[3]
    csv_dir = root / "data" / "GOLDEN"
    if not (csv_dir / "ABB.NS.csv").exists():
        pytest.skip("GOLDEN CSV not present")
    result = smoke_round_trip(
        "ABB.NS",
        csv_dir=csv_dir,
        parquet_dir=root / "data" / "GOLDEN_PARQUET",
    )
    assert result.ok
    assert result.csv_rows > 0
