import unittest
import pandas as pd
from src.strategy_service.features.advance_decline import add_ad_regime

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
        result = add_ad_regime(self.main_df.copy(), self.component_dfs)
        self.assertIn('ad_net_breadth', result.columns)
        self.assertIn('ad_cumulative', result.columns)
        self.assertIn('ad_ema_5', result.columns)
        self.assertIn('ad_ema_21', result.columns)
        
        # Check that it calculates values (not all NaNs)
        self.assertFalse(result['ad_net_breadth'].isna().all())
        self.assertFalse(result['ad_cumulative'].isna().all())
        self.assertTrue(pd.api.types.is_numeric_dtype(result['ad_net_breadth']))
        self.assertTrue(pd.api.types.is_numeric_dtype(result['ad_cumulative']))

    def test_add_ad_ratio_empty_components(self):
        result = add_ad_regime(self.main_df.copy(), {})
        self.assertNotIn('ad_net_breadth', result.columns)
        self.assertNotIn('ad_cumulative', result.columns)
        self.assertNotIn('ad_ema_5', result.columns)
        self.assertNotIn('ad_ema_21', result.columns)

if __name__ == '__main__':
    unittest.main()
