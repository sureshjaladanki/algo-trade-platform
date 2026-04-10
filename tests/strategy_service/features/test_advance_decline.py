import unittest
import pandas as pd
from src.strategy_service.features.advance_decline import add_ad_ratio

class TestAdvanceDecline(unittest.TestCase):
    def setUp(self):
        self.main_df = pd.read_csv('data/raw/NIFTYBEES.NS_1m_7d.csv', parse_dates=['datetime'])
        self.main_df.set_index('datetime', inplace=True)
        
        # Load 6 real stocks for components
        stocks = [
            'RELIANCE.NS', 'INFY.NS', 'ICICIBANK.NS', 
            'HINDUNILVR.NS', 'HDFCBANK.NS', 'BHARTIARTL.NS'
        ]
        
        self.component_dfs = {}
        for stock in stocks:
            df = pd.read_csv(f'data/raw/{stock}_1m_7d.csv', parse_dates=['datetime'])
            df.set_index('datetime', inplace=True)
            self.component_dfs[stock] = df

    def test_add_ad_ratio(self):
        result = add_ad_ratio(self.main_df.copy(), self.component_dfs)
        self.assertIn('ad_ratio', result.columns)
        
        # Check that it calculates values (not all NaNs)
        self.assertFalse(result['ad_ratio'].isna().all())
        # The first row should be 0.0 since there's no previous close to compare
        self.assertEqual(result['ad_ratio'].iloc[0], 0.0)
        # Check that we have valid float values
        self.assertTrue(pd.api.types.is_numeric_dtype(result['ad_ratio']))

    def test_add_ad_ratio_empty_components(self):
        result = add_ad_ratio(self.main_df.copy(), {})
        self.assertNotIn('ad_ratio', result.columns)

if __name__ == '__main__':
    unittest.main()
