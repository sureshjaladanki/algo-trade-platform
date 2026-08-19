import datetime as dt

import polars as pl
import pytest

from src.events.f1 import WindowSpec, measure_window


def test_addition_and_deletion_have_opposite_trade_sign() -> None:
    d0 = dt.date(2020, 1, 2)
    d1 = dt.date(2020, 1, 3)
    calendar = [d0, d1]
    panel = pl.DataFrame(
        {
            "symbol": ["FOO.NS", "FOO.NS"],
            "date": [d0, d1],
            "close": [100.0, 110.0],
            "nifty_close": [200.0, 210.0],
        }
    )
    spec = WindowSpec("w", -1, 0, fade=False, role="test")
    adds = measure_window(
        panel,
        pl.DataFrame(
            {
                "family": ["nifty_50"],
                "symbol": ["FOO.NS"],
                "event_type": ["addition"],
                "effective_date": [d1],
            }
        ),
        spec,
        calendar,
    )
    dels = measure_window(
        panel,
        pl.DataFrame(
            {
                "family": ["nifty_50"],
                "symbol": ["FOO.NS"],
                "event_type": ["deletion"],
                "effective_date": [d1],
            }
        ),
        spec,
        calendar,
    )
    assert adds["trade_residual_bps"][0] == pytest.approx(500.0)
    assert dels["trade_residual_bps"][0] == pytest.approx(-500.0)
