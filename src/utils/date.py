import polars as pl


def parse_period_range(period_range: str) -> tuple[str, str]:
    """Parse a period string into (start_period, end_period).

    Supported formats:
      - yyyy-yyyy (e.g. 2015-2018)
      - mm/yyyy-mm/yyyy (e.g. 03/2020-03/2021)
    """
    period_range = period_range.strip()
    if "-" not in period_range:
        return period_range, period_range
        
    start, end = period_range.split("-", 1)
    return start.strip(), end.strip()


def parse_period(period: str) -> tuple[int, int]:
    """Convert a period string (yyyy or mm/yyyy) to a datetime.date."""
    if "/" in period:
        month_str, year_str = period.split("/")
        month, year = int(month_str), int(year_str)
    else:
        month, year = None, int(period)
    
    return month, year


def filter_by_period(
    df: pl.DataFrame,
    start_period: str,
    end_period: str,
    datetime_col: str = "date",
) -> pl.DataFrame:
    start_month, start_year = parse_period(start_period)
    end_month, end_year = parse_period(end_period)

    year_col = pl.col(datetime_col).dt.year()
    month_col = pl.col(datetime_col).dt.month()

    if start_month is None:
        start_cond = year_col >= start_year
    else:
        start_cond = (year_col > start_year) | ((year_col == start_year) & (month_col >= start_month))

    if end_month is None:
        end_cond = year_col <= end_year
    else:
        end_cond = (year_col < end_year) | ((year_col == end_year) & (month_col <= end_month))

    return df.filter(start_cond & end_cond)
