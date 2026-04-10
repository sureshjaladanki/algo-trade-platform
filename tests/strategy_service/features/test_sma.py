import unittest
import pandas as pd
from src.strategy_service.features.sma import add_sma

class TestSMA(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv('data/raw/NIFTYBEES.NS_1m_7d.csv', parse_dates=['datetime'])
        self.df.set_index('datetime', inplace=True)

    def test_add_sma(self):
        period = 10
        result = add_sma(self.df.copy(), period=period)
        
        col_name = f'sma_{period}'
        self.assertIn(col_name, result.columns)
        
        # First 9 rows should be NaN for a period of 10
        self.assertTrue(pd.isna(result[col_name].iloc[8]))
        self.assertFalse(pd.isna(result[col_name].iloc[9]))
        
        # Check that it calculates values (not all NaNs)
        self.assertFalse(result[col_name].isna().all())
        self.assertTrue(pd.api.types.is_numeric_dtype(result[col_name]))

if __name__ == '__main__':
    unittest.main()
