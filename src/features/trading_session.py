import polars as pl
from typing import Mapping

from ..constants import DEFAULT_TRADING_SESSIONS


def add_trading_session(
    df: pl.DataFrame,
    *,
    trading_sessions: Mapping[str, int] = DEFAULT_TRADING_SESSIONS,
) -> pl.DataFrame:
    """
    Adds a categorical `trading_session` feature based on `minute_of_day`.

    `trading_sessions` is an ordered mapping of session name -> end minute_of_day
    (inclusive). The first session in the mapping is used as the default for any
    time outside the explicitly defined windows.

    Requires `minute_of_day` column to already exist in `df`.
    """
    if "minute_of_day" not in df.columns:
        return df

    session_names = list(trading_sessions.keys())
    if not session_names:
        return df

    session_enum = pl.Enum(session_names)

    # Start with the default session
    session_expr = pl.lit(session_names[0])

    # Iterate in reverse to build the nested 'otherwise' structure:
    # when(cond1).then(val1).otherwise(when(cond2).then(val2).otherwise(default))
    for name, end_minute in reversed(list(trading_sessions.items())):
        session_expr = (
            pl.when(pl.col("minute_of_day") <= end_minute)
            .then(pl.lit(name))
            .otherwise(session_expr)
        )

    # Cast to Enum for efficiency and alias the column
    session_expr = session_expr.cast(session_enum).alias("trading_session")

    return df.with_columns(session_expr)
