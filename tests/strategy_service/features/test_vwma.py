import unittest
import pandas as pd

from src.strategy_service.features.vwma import add_vwma


class TestVWMA(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv('data/raw/NIFTYBEES.NS_1m_7d.csv', parse_dates=['datetime'])
        self.df.set_index('datetime', inplace=True)

    def test_add_vwma(self):
        period = 10
        result = add_vwma(self.df.copy(), period=period)

        col_name = f'vwma_{period}'
        self.assertIn(col_name, result.columns)

        # VWMA uses a rolling window; first (period - 1) values should be NaN
        self.assertTrue(pd.isna(result[col_name].iloc[8]))
        self.assertFalse(pd.isna(result[col_name].iloc[9]))

        # Check that it calculates values (not all NaNs)
        self.assertFalse(result[col_name].isna().all())
        self.assertTrue(pd.api.types.is_numeric_dtype(result[col_name]))


if __name__ == '__main__':
    unittest.main()

