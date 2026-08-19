"""Daily OHLCV panel from GOLDEN minute bars."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import polars as pl

from src.events.benchmark import build_after_tax_passive
from src.events.membership import membership_pairs
from src.events.paths import (
    DAILY_PANEL_PARQUET,
    DERIVED_DIR,
    GOLDEN_DIR,
    NIFTY_CSV_NAME,
)

SESSION_CLOSE_CUTOFF = dt.time(15, 15)
_SPLIT_RATIOS = (2.0, 3.0, 4.0, 5.0, 10.0, 20.0, 0.5, 1.0 / 3.0, 0.25, 0.2, 0.1)
_SPLIT_TOL = 0.01


class CorporateActionError(RuntimeError):
    """Unadjusted split-like gap; do not silently build returns."""


def is_equity_bar_file(path: Path) -> bool:
    name = path.name
    if name.startswith(("^", "NIFTY")):
        return False
    return name.endswith(".NS.csv")


def symbol_from_bar_file(path: Path) -> str:
    return path.name[: -len(".csv")]


def list_index_price_files(golden_dir: Path) -> list[str]:
    names = sorted(p.name for p in golden_dir.glob("*.csv"))
    return [n for n in names if n.startswith(("^", "NIFTY"))]


def _aggregate_minute_file(path: Path, symbol: str) -> pl.DataFrame:
    return (
        pl.scan_csv(path, try_parse_dates=True)
        .filter(
            (pl.col("open") > 0)
            & (pl.col("high") > 0)
            & (pl.col("low") > 0)
            & (pl.col("close") > 0)
        )
        .with_columns(session_dt=pl.col("date"), date=pl.col("date").dt.date())
        .group_by("date")
        .agg(
            symbol=pl.lit(symbol),
            open=pl.col("open").sort_by("session_dt").first(),
            high=pl.col("high").max(),
            low=pl.col("low").min(),
            close=pl.col("close").sort_by("session_dt").last(),
            volume=pl.col("volume").sum(),
            last_bar_time=pl.col("session_dt").dt.time().max(),
            n_bars=pl.len(),
        )
        .collect()
    )


def _drop_trailing_incomplete(daily: pl.DataFrame) -> pl.DataFrame:
    """Drop the last calendar date when its last bar is before the close cutoff."""
    if daily.height == 0:
        raise RuntimeError("empty daily frame")
    last_date = daily.select(pl.col("date").max()).item()
    last_time = daily.filter(pl.col("date") == last_date)["last_bar_time"][0]
    if last_time < SESSION_CLOSE_CUTOFF:
        return daily.filter(pl.col("date") < last_date)
    return daily


def _assert_positive_ohlc(daily: pl.DataFrame, *, symbol: str) -> None:
    bad = daily.filter(
        (pl.col("open") <= 0)
        | (pl.col("high") <= 0)
        | (pl.col("low") <= 0)
        | (pl.col("close") <= 0)
        | pl.col("close").is_null()
    )
    if bad.height:
        day = bad["date"][0]
        raise RuntimeError(f"{symbol}: non-positive or null OHLC on {day}")


def _matches_split_ratio(ratio_col: pl.Expr) -> pl.Expr:
    return pl.any_horizontal(
        [
            (ratio_col - factor).abs() <= _SPLIT_TOL * factor
            for factor in _SPLIT_RATIOS
        ]
    )


def drop_isolated_price_glitches(panel: pl.DataFrame) -> pl.DataFrame:
    """Drop sessions that are split-like prints, not corporate actions.

    Two cases: (1) close/open matches a split factor — the session is internally
    inconsistent; (2) a close-to-close split spike that the next session reverses.
    Persistent level shifts still fail in ``assert_no_unadjusted_splits``.
    """
    ranked = panel.sort(["symbol", "date"]).with_columns(
        prev_close=pl.col("close").shift(1).over("symbol"),
        next_close=pl.col("close").shift(-1).over("symbol"),
        open_close_ratio=pl.col("close") / pl.col("open"),
    )
    ratio = pl.col("close") / pl.col("prev_close")
    revert = pl.col("next_close") / pl.col("close")
    isolated = (
        pl.col("prev_close").is_not_null()
        & pl.col("next_close").is_not_null()
        & _matches_split_ratio(ratio)
        & (((ratio * revert) - 1.0).abs() <= 0.03)
    )
    broken_session = _matches_split_ratio(pl.col("open_close_ratio"))
    return ranked.filter(~isolated & ~broken_session).drop(
        "prev_close", "next_close", "open_close_ratio"
    )


def assert_no_unadjusted_splits(panel: pl.DataFrame) -> None:
    """Fail if a close-to-close ratio matches a split factor.

    GOLDEN is usable for returns only if those gaps are already adjusted.
    There is no corporate-action table on this branch.
    """
    ranked = panel.sort(["symbol", "date"]).with_columns(
        prev_close=pl.col("close").shift(1).over("symbol"),
        ratio=pl.col("close") / pl.col("close").shift(1).over("symbol"),
    )
    for factor in _SPLIT_RATIOS:
        hits = ranked.filter(
            pl.col("prev_close").is_not_null()
            & ((pl.col("ratio") - factor).abs() <= _SPLIT_TOL * factor)
        )
        if hits.height:
            row = hits.row(0, named=True)
            raise CorporateActionError(
                f"{row['symbol']} {row['date']}: close ratio {row['ratio']:.4f} "
                f"matches split {factor:g} and no corporate-action table is present"
            )


def load_nifty_daily(golden_dir: Path) -> pl.DataFrame:
    path = golden_dir / NIFTY_CSV_NAME
    daily = _aggregate_minute_file(path, "^NSEI")
    _assert_positive_ohlc(daily, symbol="^NSEI")
    daily = _drop_trailing_incomplete(daily)
    return daily.select("date", "open", "high", "low", "close", "volume").sort("date")


def _load_equity_daily(golden_dir: Path, session_dates: pl.Series) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    calendar = set(session_dates.to_list())
    for path in sorted(golden_dir.glob("*.csv")):
        if not is_equity_bar_file(path):
            continue
        symbol = symbol_from_bar_file(path)
        daily = _aggregate_minute_file(path, symbol)
        _assert_positive_ohlc(daily, symbol=symbol)
        daily = daily.filter(pl.col("date").is_in(list(calendar)))
        frames.append(
            daily.select("symbol", "date", "open", "high", "low", "close", "volume")
        )
    if not frames:
        raise RuntimeError(f"no equity GOLDEN CSVs under {golden_dir}")
    return pl.concat(frames).sort(["symbol", "date"])


def build_daily_panel(golden_dir: Path | None = None) -> pl.DataFrame:
    """Symbol-date OHLCV, Nifty close, Nifty-50 membership flag."""
    src = golden_dir if golden_dir is not None else GOLDEN_DIR
    nifty = load_nifty_daily(src)
    equities = _load_equity_daily(src, nifty["date"])
    panel = equities.join(
        nifty.select("date", pl.col("close").alias("nifty_close")),
        on="date",
        how="left",
    )
    missing_nifty = panel.filter(pl.col("nifty_close").is_null())
    if missing_nifty.height:
        row = missing_nifty.row(0, named=True)
        raise RuntimeError(
            f"{row['symbol']} {row['date']}: equity session has no Nifty close"
        )
    dates = panel.select("date").unique().to_series().to_list()
    pairs = membership_pairs(dates)
    panel = panel.join(
        pairs.with_columns(is_nifty50_member=pl.lit(True)),
        on=["date", "symbol"],
        how="left",
    ).with_columns(
        is_nifty50_member=pl.col("is_nifty50_member").fill_null(False)
    )
    panel = drop_isolated_price_glitches(panel)
    assert_no_unadjusted_splits(panel)
    return panel.select(
        "symbol",
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "is_nifty50_member",
        "nifty_close",
    ).sort(["symbol", "date"])


def load_or_build_daily_panel(
    golden_dir: Path | None = None,
    cache_path: Path | None = None,
    *,
    rebuild: bool = False,
) -> pl.DataFrame:
    dest = cache_path if cache_path is not None else DAILY_PANEL_PARQUET
    if dest.exists() and not rebuild:
        return pl.read_parquet(dest)
    panel = build_daily_panel(golden_dir)
    dest.parent.mkdir(parents=True, exist_ok=True)
    panel.write_parquet(dest)
    return panel


def main() -> None:
    panel = load_or_build_daily_panel(rebuild=True)
    bench = build_after_tax_passive(load_nifty_daily(GOLDEN_DIR))
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    bench.write_parquet(DERIVED_DIR / "after_tax_passive.parquet")
    print(
        f"daily_panel rows={panel.height} "
        f"symbols={panel['symbol'].n_unique()} "
        f"dates={panel['date'].min()}..{panel['date'].max()}"
    )
    print(
        f"after_tax_passive {bench['date'].min()}..{bench['date'].max()} "
        f"terminal={bench['after_tax_wealth'][-1]:.4f}"
    )


if __name__ == "__main__":
    main()
