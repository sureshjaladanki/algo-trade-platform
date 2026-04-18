import unittest
import pandas as pd
from datetime import time
from src.strategy_service.features.minute_of_day import add_minute_of_day


class TestMinuteOfDay(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv(
            "data/raw/NIFTYBEES.NS_1m_7d.csv", parse_dates=["datetime"]
        )

    def test_add_minute_of_day_datetime_index(self):
        df = self.df.copy()
        df.set_index("datetime", inplace=True)

        result = add_minute_of_day(df)

        self.assertIn("minute_of_day", result.columns)
        self.assertFalse(result["minute_of_day"].isna().all())
        # Check that it extracted time correctly
        self.assertIsInstance(result["minute_of_day"].iloc[0], time)

    def test_add_minute_of_day_datetime_column(self):
        df = self.df.copy()

        result = add_minute_of_day(df)

        self.assertIn("minute_of_day", result.columns)
        self.assertFalse(result["minute_of_day"].isna().all())
        self.assertIsInstance(result["minute_of_day"].iloc[0], time)


if __name__ == "__main__":
    unittest.main()
