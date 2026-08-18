"""M9 IV store contract tests."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl
import pytest

from src.horizon.m9.iv_store import (
    IvStoreMissingError,
    attach_lagged_atm_iv,
    coverage_report,
    load_atm_iv_daily,
)


def test_load_atm_iv_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(IvStoreMissingError):
        load_atm_iv_daily(tmp_path / "missing.parquet")


def test_attach_lagged_iv_uses_prior_session() -> None:
    iv = pl.DataFrame(
        {
            "symbol": ["A", "A", "A"],
            "date_only": [dt.date(2018, 1, 1), dt.date(2018, 1, 2), dt.date(2018, 1, 3)],
            "atm_iv_pct": [10.0, 20.0, 30.0],
        }
    )
    panel = pl.DataFrame(
        {
            "symbol": ["A", "A"],
            "date_only": [dt.date(2018, 1, 2), dt.date(2018, 1, 3)],
            "x": [1.0, 2.0],
        }
    )
    out = attach_lagged_atm_iv(panel, iv)
    assert out["atm_iv_pct"].to_list() == [10.0, 20.0]
    cov = coverage_report(out)
    assert cov["coverage"] == 1.0


def test_attach_lagged_iv_asof_skips_gap_and_same_day() -> None:
    iv = pl.DataFrame(
        {
            "symbol": ["A", "A"],
            "date_only": [dt.date(2018, 1, 2), dt.date(2018, 1, 3)],
            "atm_iv_pct": [11.0, 22.0],
        }
    )
    panel = pl.DataFrame(
        {
            "symbol": ["A", "A", "A"],
            "date_only": [
                dt.date(2018, 1, 2),
                dt.date(2018, 1, 4),
                dt.date(2018, 1, 5),
            ],
        }
    )
    out = attach_lagged_atm_iv(panel, iv)
    assert out["atm_iv_pct"].to_list() == [None, 22.0, 22.0]

