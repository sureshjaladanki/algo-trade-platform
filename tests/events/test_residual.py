import datetime as dt

import polars as pl
import pytest

from src.events.residual import residual_bps, window_residual_bps


def test_residual_is_stock_minus_nifty() -> None:
    # stock +10%, nifty +5% → +500 bps
    assert residual_bps(100.0, 110.0, 200.0, 210.0) == pytest.approx(500.0)


def test_window_residual_skips_missing_close() -> None:
    panel = pl.DataFrame(
        {
            "symbol": ["FOO.NS"],
            "date": [dt.date(2020, 1, 2)],
            "close": [110.0],
            "nifty_close": [210.0],
        }
    )
    assert (
        window_residual_bps(panel, "FOO.NS", dt.date(2020, 1, 1), dt.date(2020, 1, 2))
        is None
    )
