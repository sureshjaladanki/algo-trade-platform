import pytest
import pandas as pd
import numpy as np
from src.strategy_service.features.adx import add_adx

@pytest.fixture
def sample_data():
    """Generate a sample dataframe with high, low, and close prices."""
    # ADX requires high, low, and close columns, and enough data points
    # (usually at least 2 * period rows) to calculate properly.
    dates = pd.date_range(start='2026-01-01', periods=100, freq='1min')
    
    # Create an artificial upward trend
    base_price = np.linspace(100, 150, 100)
    
    df = pd.DataFrame({
        'high': base_price + 2 + np.random.normal(0, 0.5, 100),
        'low': base_price - 2 - np.random.normal(0, 0.5, 100),
        'close': base_price + np.random.normal(0, 0.2, 100),
    }, index=dates)
    
    return df

def test_add_adx_default_period(sample_data):
    """Test ADX calculation with the default period (70)."""
    df = add_adx(sample_data.copy())
    
    # Check if the 'adx_70' column was successfully added
    assert 'adx_70' in df.columns
    
    # The first few rows will be NaN due to the rolling calculation window,
    # but the last rows should have valid float values.
    assert df['adx_70'].isna().iloc[0]
    assert not df['adx_70'].isna().iloc[-1]
    
    # ADX values should be between 0 and 100 (allow small floating point variance)
    valid_adx = df['adx_70'].dropna()
    assert (valid_adx >= -0.001).all()
    assert (valid_adx <= 100.001).all()

def test_add_adx_custom_period(sample_data):
    """Test ADX calculation with a custom period."""
    custom_period = 20
    df = add_adx(sample_data.copy(), period=custom_period)
    
    assert f'adx_{custom_period}' in df.columns
    assert not df[f'adx_{custom_period}'].isna().iloc[-1]

def test_add_adx_custom_resample_period(sample_data):
    """Test ADX calculation with a custom resample period."""
    # Using a 10-minute resample period instead of default 5
    df = add_adx(sample_data.copy(), period=70, resample_period=10)
    
    assert 'adx_70' in df.columns
    assert not df['adx_70'].isna().iloc[-1]
    
    # Verify that the values are forward-filled correctly by checking if 
    # consecutive rows within the resample period have the same ADX value
    # (Since we resampled by 10 minutes, blocks of 10 rows should have identical ADX values at the end)
    valid_adx = df['adx_70'].dropna()
    if len(valid_adx) >= 2:
        # The last two rows should be identical because they fall within the same 10-minute forward-fill block
        assert valid_adx.iloc[-1] == valid_adx.iloc[-2]

def test_add_adx_insufficient_data():
    """Test ADX behavior when there is not enough data to calculate it."""
    # Create a dataframe with only 5 rows (less than the default period)
    dates = pd.date_range(start='2026-01-01', periods=5, freq='1min')
    df = pd.DataFrame({
        'high': [10, 11, 12, 13, 14],
        'low': [8, 9, 10, 11, 12],
        'close': [9, 10, 11, 12, 13]
    }, index=dates)
    
    # This shouldn't crash. Depending on pandas-ta version, it might return None
    # or a dataframe full of NaNs. Our wrapper should handle it gracefully.
    result = add_adx(df.copy(), period=70)
    
    assert isinstance(result, pd.DataFrame)
    # If the column was added, it should be entirely NaN
    if 'adx_70' in result.columns:
        assert result['adx_70'].isna().all()
