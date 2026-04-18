import pytest
import pandas as pd
import numpy as np
from src.strategy_service.features.atr import get_atr


@pytest.fixture
def sample_ohlcv_data():
    """Creates a sample OHLCV DataFrame for testing."""
    # Create 20 periods of dummy data
    dates = pd.date_range(start="2023-01-01", periods=20, freq="D")
    np.random.seed(42)

    # Generate some realistic-looking price data
    close_prices = 100 + np.random.randn(20).cumsum()
    high_prices = close_prices + np.random.uniform(0.5, 2.0, 20)
    low_prices = close_prices - np.random.uniform(0.5, 2.0, 20)

    df = pd.DataFrame(
        {
            "open": close_prices - np.random.uniform(-1, 1, 20),
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": np.random.randint(1000, 10000, 20),
        },
        index=dates,
    )

    return df


def test_get_atr_valid_data(sample_ohlcv_data):
    """Test ATR calculation with valid data and default period."""
    result = get_atr(sample_ohlcv_data)

    assert isinstance(result, dict)
    assert "prev_atr" in result
    assert "prev_close" in result
    assert isinstance(result["prev_atr"], float)
    assert isinstance(result["prev_close"], float)

    # Check if close matches the last row's close
    expected_close = float(sample_ohlcv_data["close"].iloc[-1])
    assert result["prev_close"] == expected_close


def test_get_atr_custom_period(sample_ohlcv_data):
    """Test ATR calculation with a custom period."""
    result = get_atr(sample_ohlcv_data, period=7)

    assert isinstance(result, dict)
    assert "prev_atr" in result
    assert "prev_close" in result
    assert isinstance(result["prev_atr"], float)


def test_get_atr_empty_dataframe():
    """Test ATR calculation with an empty DataFrame."""
    empty_df = pd.DataFrame()
    result = get_atr(empty_df)

    assert isinstance(result, dict)
    assert len(result) == 0


def test_get_atr_missing_columns():
    """Test ATR calculation with missing required columns."""
    # Missing 'low' and 'high'
    df = pd.DataFrame(
        {
            "open": [100, 101, 102],
            "close": [101, 102, 103],
            "volume": [1000, 1500, 1200],
        }
    )

    result = get_atr(df)

    assert isinstance(result, dict)
    assert len(result) == 0


def test_get_atr_insufficient_data():
    """Test ATR calculation with fewer rows than the period."""
    # Create a DataFrame with only 5 rows, but default period is 14
    dates = pd.date_range(start="2023-01-01", periods=5, freq="D")
    df = pd.DataFrame(
        {
            "open": [100] * 5,
            "high": [105] * 5,
            "low": [95] * 5,
            "close": [102] * 5,
            "volume": [1000] * 5,
        },
        index=dates,
    )

    result = get_atr(df, period=14)

    # pandas-ta might return NaN for all rows if there's not enough data
    # Our function should handle this gracefully and return an empty dict
    assert isinstance(result, dict)
    assert len(result) == 0
