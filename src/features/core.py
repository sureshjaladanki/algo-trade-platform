import polars as pl


def ema(col: str, span: int) -> pl.Expr:
    """Exponential Moving Average"""
    return pl.col(col).ewm_mean(span=span, ignore_nulls=True)

def true_range(high: str = "high", low: str = "low", close: str = "close") -> pl.Expr:
    """True Range"""
    h, lo, c = pl.col(high), pl.col(low), pl.col(close)
    prev_c = c.shift(1)
    return pl.max_horizontal(
        h - lo,
        (h - prev_c).abs(),
        (lo - prev_c).abs()
    )

def atr(high: str = "high", low: str = "low", close: str = "close", window: int = 14) -> pl.Expr:
    """Average True Range"""
    return true_range(high, low, close).rolling_mean(window)

def log_return(col: str = "close") -> pl.Expr:
    """Logarithmic Return"""
    c = pl.col(col)
    return (c / c.shift(1)).log()

def pct_return(col: str = "close") -> pl.Expr:
    """Percentage Return"""
    c = pl.col(col)
    return (c / c.shift(1)) - 1.0

def pct_distance(col: str, ref: str) -> pl.Expr:
    """Percentage distance of col from ref"""
    c, r = pl.col(col), pl.col(ref)
    return (c - r) / r

def gap(open_col: str = "open", close_col: str = "close") -> pl.Expr:
    """Gap between current open and previous close"""
    return pl.col(open_col) - pl.col(close_col).shift(1)

def rolling_median(col: str, window: int) -> pl.Expr:
    """Rolling Median"""
    return pl.col(col).rolling_median(window)

def z_score(col: str, mean: str, std: str) -> pl.Expr:
    """Z-Score calculation using pre-computed mean and std"""
    return (pl.col(col) - pl.col(mean)) / pl.col(std)

def range_pct(high: str = "high", low: str = "low", close: str = "close") -> pl.Expr:
    """Range as a percentage of close"""
    return (pl.col(high) - pl.col(low)) / pl.col(close)

def vwap(high: str = "high", low: str = "low", close: str = "close", volume: str = "volume") -> pl.Expr:
    """
    Volume Weighted Average Price.
    Note: For intraday data, this should typically be applied within a group_by("date") context to reset daily.
    """
    h, lo, c, v = pl.col(high), pl.col(low), pl.col(close), pl.col(volume)
    typical_price = (h + lo + c) / 3
    return (typical_price * v).cum_sum() / v.cum_sum()
