import unittest
import pandas as pd
from src.strategy_service.features.rsi import add_rsi

class TestRSI(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv('data/raw/NIFTYBEES.NS_1m_7d.csv', parse_dates=['datetime'])
        self.df.set_index('datetime', inplace=True)

    def test_add_rsi(self):
        period = 14
        result = add_rsi(self.df.copy(), rsi_period=period)
        
        col_name = f'rsi_{period}'
        self.assertIn(col_name, result.columns)
        
        # Check that it calculates values (not all NaNs)
        self.assertFalse(result[col_name].isna().all())
        # First value should be NaN
        self.assertTrue(pd.isna(result[col_name].iloc[0]))
        self.assertTrue(pd.api.types.is_numeric_dtype(result[col_name]))

if __name__ == '__main__':
    unittest.main()
