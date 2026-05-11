import polars as pl


def parse_period(period_str: str) -> tuple[int, int]:
    if "-" in period_str:
        start, end = period_str.split("-")
        start_year = int(start)
        if len(end) == 2:
            end_year = int(start[:2] + end)
        else:
            end_year = int(end)
        return start_year, end_year
    else:
        return int(period_str), int(period_str)


def filter_by_period(
    df: pl.DataFrame, start_year: int, end_year: int, datetime_col: str = "date"
) -> pl.DataFrame:
    return df.filter(
        (pl.col(datetime_col).dt.year() >= start_year)
        & (pl.col(datetime_col).dt.year() <= end_year)
    )
