import unittest
import pandas as pd
from src.strategy_service.features.bb import add_bb

class TestBB(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv('data/raw/NIFTYBEES.NS_1m_7d.csv', parse_dates=['datetime'])
        self.df.set_index('datetime', inplace=True)

    def test_add_bb(self):
        period = 20
        std_dev = 2.0
        result = add_bb(self.df.copy(), period=period, std_dev=std_dev)
        
        self.assertIn('bb_lower', result.columns)
        self.assertIn('bb_upper', result.columns)
        self.assertIn('bb_width_pct', result.columns)
        self.assertIn('expected_profit_pct_long', result.columns)
        self.assertIn('expected_profit_pct_short', result.columns)
        
        # First 19 rows should be NaN for a period of 20
        self.assertTrue(pd.isna(result['bb_lower'].iloc[18]))
        self.assertFalse(pd.isna(result['bb_lower'].iloc[19]))
        
        # Check that it calculates values (not all NaNs)
        self.assertFalse(result['bb_lower'].isna().all())
        self.assertFalse(result['bb_upper'].isna().all())
        self.assertFalse(result['bb_width_pct'].isna().all())
        self.assertFalse(result['expected_profit_pct_long'].isna().all())
        self.assertFalse(result['expected_profit_pct_short'].isna().all())
        
        self.assertTrue(pd.api.types.is_numeric_dtype(result['bb_lower']))
        self.assertTrue(pd.api.types.is_numeric_dtype(result['bb_upper']))
        self.assertTrue(pd.api.types.is_numeric_dtype(result['bb_width_pct']))
        self.assertTrue(pd.api.types.is_numeric_dtype(result['expected_profit_pct_long']))
        self.assertTrue(pd.api.types.is_numeric_dtype(result['expected_profit_pct_short']))
        
        # Basic math check for the calculated columns on a valid row
        valid_row = result.iloc[20]
        expected_width = ((valid_row['bb_upper'] - valid_row['bb_lower']) / valid_row['close']) * 100
        expected_long = ((valid_row['bb_upper'] - valid_row['close']) / valid_row['close']) * 100
        expected_short = ((valid_row['close'] - valid_row['bb_lower']) / valid_row['close']) * 100
        
        self.assertAlmostEqual(valid_row['bb_width_pct'], expected_width)
        self.assertAlmostEqual(valid_row['expected_profit_pct_long'], expected_long)
        self.assertAlmostEqual(valid_row['expected_profit_pct_short'], expected_short)

if __name__ == '__main__':
    unittest.main()
