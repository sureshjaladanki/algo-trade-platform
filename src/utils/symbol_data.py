from pathlib import Path

import polars as pl

from .data import load_csv_data
from .date import filter_by_period


def load_symbol_data(
    csv_path: Path,
    *,
    start_period: str,
    end_period: str,
    datetime_col: str = "date",
) -> pl.DataFrame:
    df = load_csv_data(csv_path, datetime_col=datetime_col)
    return filter_by_period(df, start_period, end_period, datetime_col=datetime_col)
