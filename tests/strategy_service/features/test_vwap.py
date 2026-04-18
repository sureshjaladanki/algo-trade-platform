import unittest
import pandas as pd
from src.strategy_service.features.vwap import add_vwap


class TestVWAP(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv(
            "data/raw/NIFTYBEES.NS_1m_7d.csv", parse_dates=["datetime"]
        )
        self.df.set_index("datetime", inplace=True)

    def test_add_vwap(self):
        result = add_vwap(self.df.copy())

        self.assertIn("vwap", result.columns)
        self.assertTrue(pd.isna(result["vwap"].iloc[0]))
        self.assertTrue(len(result["vwap"]) == len(self.df))

        # Check that it calculates values (not all NaNs)
        self.assertFalse(result["vwap"].isna().all())
        self.assertTrue(pd.api.types.is_numeric_dtype(result["vwap"]))


if __name__ == "__main__":
    unittest.main()
