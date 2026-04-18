import pandas as pd
from typing import Dict
import pandas_ta as ta


def add_ad_regime(
    df: pd.DataFrame,
    component_dfs: Dict[str, pd.DataFrame],
    fast_period: int = 5,
    slow_period: int = 21,
) -> pd.DataFrame:
    """
    Add advance/decline breadth and derived regime columns aligned to ``df``'s index.

    For each row (bar), counts how many component symbols advanced or declined versus
    the prior bar's close on the same index grid:

    - **Advance:** ``close > prior close``
    - **Decline:** ``close < prior close``
    - **Unchanged:** equal to prior close; neither advance nor decline

    Columns written on ``df`` (when ``component_dfs`` is non-empty):

    - ``ad_net_breadth``: advances minus declines per bar
    - ``ad_cumulative``: cumulative sum of net breadth
    - ``ad_ema``: EMA of the cumulative line (length ``period``)
    - ``ad_roc``: rate of change of the cumulative line (length ``int(period / 4)``)

    Args:
        df: Target DataFrame (index must align with component series after reindex).
        component_dfs: Symbol -> OHLCV DataFrame; each must have a ``close`` column.
        period: EMA length for ``ad_ema``; also scales the ROC lookback.

    Returns:
        ``df`` with breadth/regime columns added, or unchanged if ``component_dfs`` is empty.
    """
    if not component_dfs:
        return df

    # Extract close prices into a 2D matrix (columns = symbols, index = time)
    closes = pd.DataFrame(
        {sym: df["close"] for sym, df in component_dfs.items()}
    ).reindex(df.index)

    # Industry standard: compare current close to previous close
    prev_closes = closes.shift(1)

    advances = (closes > prev_closes).sum(axis=1)
    declines = (closes < prev_closes).sum(axis=1)

    # 1. Calculate the net breadth (Advances - Declines)
    df["ad_net_breadth"] = advances - declines

    # 2. Calculate the Cumulative A/D Line
    # This transforms 1-minute 'flicker' into a continuous trend
    df["ad_cumulative"] = df["ad_net_breadth"].cumsum()

    # 3. An EMA helps identify the 'Regime' direction
    df[f"ad_ema_{fast_period}"] = ta.ema(df["ad_cumulative"], length=fast_period)
    df[f"ad_ema_{slow_period}"] = ta.ema(df["ad_cumulative"], length=slow_period)

    return df
