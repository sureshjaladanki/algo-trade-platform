import math

import polars as pl

TOTAL_MINUTES = 1440.0


def add_cyclical_time(
    df: pl.DataFrame, minute_col: str = "minute_of_day"
) -> pl.DataFrame:
    """Encode minute-of-day as sin/cos over a 24-hour cycle."""
    df = df.with_columns(
        [
            (
                (2 * math.pi * pl.col(minute_col) / TOTAL_MINUTES).sin()
            ).alias(f"{minute_col}_sin"),
            (
                (2 * math.pi * pl.col(minute_col) / TOTAL_MINUTES).cos()
            ).alias(f"{minute_col}_cos"),
        ]
    )

    return df