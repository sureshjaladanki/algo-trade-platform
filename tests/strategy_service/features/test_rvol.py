import unittest
import pandas as pd
from src.strategy_service.features.rvol import get_volume_profile


class TestRVOL(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv(
            "data/raw/NIFTYBEES.NS_1m_7d.csv", parse_dates=["datetime"]
        )
        self.df.set_index("datetime", inplace=True)

    def test_get_volume_profile(self):
        result = get_volume_profile(self.df.copy())

        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) > 0)

        # Check that values are numeric
        first_val = list(result.values())[0]
        self.assertTrue(isinstance(first_val, (int, float)))

    def test_get_volume_profile_empty(self):
        df = pd.DataFrame()
        result = get_volume_profile(df)
        self.assertEqual(result, {})

    def test_get_volume_profile_no_volume(self):
        df = self.df.copy().drop(columns=["volume"])
        result = get_volume_profile(df)
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
