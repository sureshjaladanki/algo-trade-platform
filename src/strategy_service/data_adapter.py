from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd


class IDataAdapter(ABC):
    @abstractmethod
    def read_1m_candles_history_dataframe(self, symbol: str) -> pd.DataFrame:
        """Fetch 1-minute candle history for a given symbol."""
        pass

    @abstractmethod
    def read_1d_candles_history_dataframe(self, symbol: str) -> pd.DataFrame:
        """Fetch 1-day candle history for a given symbol."""
        pass

    @abstractmethod
    def process_next_1m_candle(self, symbol: str):
        """Yield 1-minute candles that have closed by reading from current day data."""
        pass


class DataAdapter(IDataAdapter):
    def __init__(self):
        self.data_path = Path("data/processed")

    def _read_dataframe(self, filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        return df

    def read_1m_candles_history_dataframe(self, symbol: str) -> pd.DataFrame:
        return self._read_dataframe(f"{self.data_path}/{symbol}_1m_history.csv")

    def read_1d_candles_history_dataframe(self, symbol: str) -> pd.DataFrame:
        return self._read_dataframe(f"{self.data_path}/{symbol}_1d_30d.csv")

    def process_next_1m_candle(self, symbol: str):
        """Yield 1-minute candles that have closed by reading from current day data."""
        filepath = f"{self.data_path}/{symbol}_1m_current_day.csv"
        df = self._read_dataframe(filepath)

        for _, candle in df.iterrows():
            yield candle
