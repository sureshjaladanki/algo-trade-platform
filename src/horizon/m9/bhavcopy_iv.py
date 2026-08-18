"""Parse one NSE FO bhavcopy into ATM IV rows (M9-0 DIY path B)."""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import polars as pl

from src.horizon.m9.black_scholes import implied_volatility
from src.utils.data import load_csv_data
from src.utils.load_config import load_config

MIN_DTE = 7
MAX_DTE = 45
SOURCE_BHAVCOPY_BS = "nse_bhavcopy_bs"
DAYS_PER_YEAR = 365.0

_COL_ALIASES: dict[str, str] = {
    "strike_pr": "strike",
    "strike_price": "strike",
    "settle_pr": "settle",
    "settle_price": "settle",
    "option_typ": "option_type",
    "expiry_dt": "expiry",
    "expiry_date": "expiry",
    "close": "close",
    "symbol": "symbol",
    "instrument": "instrument",
    "timestamp": "timestamp",
}


def nse_fo_symbol(golden_symbol: str) -> str:
    """``RELIANCE.NS`` → ``RELIANCE`` (FO bhavcopy SYMBOL)."""
    if golden_symbol.endswith(".NS"):
        return golden_symbol[: -len(".NS")]
    return golden_symbol


def golden_symbol_from_nse(nse_symbol: str) -> str:
    if nse_symbol.endswith(".NS"):
        return nse_symbol
    return f"{nse_symbol}.NS"


def load_trade_symbols(config_path: Path) -> list[str]:
    """GOLDEN names from ``sectoral_indices[*].trade_symbols``."""
    cfg = load_config(config_path)
    out: list[str] = []
    for sector in (cfg.get("sectoral_indices") or {}).values():
        out.extend(sector.get("trade_symbols") or [])
    return sorted(set(out))


def _normalize_fo_columns(fo: pl.DataFrame) -> pl.DataFrame:
    renamed = {c: c.strip().lower() for c in fo.columns}
    out = fo.rename(renamed)
    mapping = {
        src: dst
        for src, dst in _COL_ALIASES.items()
        if src in out.columns and dst not in out.columns
    }
    if mapping:
        out = out.rename(mapping)
    return out


def _parse_expiry(expr: pl.Expr) -> pl.Expr:
    raw = expr.cast(pl.Utf8).str.strip_chars()
    return (
        raw.str.to_date("%d-%b-%Y", strict=False)
        .fill_null(raw.str.to_date("%d-%b-%y", strict=False))
        .fill_null(raw.str.to_date("%d%b%Y", strict=False))
    )


def _near_fut_spot(
    fo_n: pl.DataFrame,
    nse_names: list[str],
    session_date: dt.date,
) -> pl.DataFrame:
    """Front-month FUTSTK settle (contemporaneous, not split-adjusted)."""
    if "instrument" not in fo_n.columns:
        return pl.DataFrame(
            schema={"nse_symbol": pl.Utf8, "underlying_close": pl.Float64}
        )
    fut = fo_n.filter(
        pl.col("instrument").cast(pl.Utf8).str.to_uppercase().eq("FUTSTK")
        & pl.col("symbol").cast(pl.Utf8).is_in(nse_names)
    )
    if fut.height == 0:
        return pl.DataFrame(
            schema={"nse_symbol": pl.Utf8, "underlying_close": pl.Float64}
        )
    settle = (
        pl.col("settle").cast(pl.Float64, strict=False)
        if "settle" in fut.columns
        else pl.lit(None, dtype=pl.Float64)
    )
    close = (
        pl.col("close").cast(pl.Float64, strict=False)
        if "close" in fut.columns
        else pl.lit(None, dtype=pl.Float64)
    )
    fut = fut.with_columns(
        expiry=_parse_expiry(pl.col("expiry")) if "expiry" in fut.columns else pl.lit(None),
        nse_symbol=pl.col("symbol").cast(pl.Utf8),
        fut_px=settle.fill_null(close),
    ).filter(pl.col("expiry").is_not_null() & (pl.col("fut_px") > 0.0))
    fut = fut.with_columns(
        dte=(pl.col("expiry") - pl.lit(session_date)).dt.total_days().cast(pl.Int32)
    ).filter(pl.col("dte") >= 0)
    if fut.height == 0:
        return pl.DataFrame(
            schema={"nse_symbol": pl.Utf8, "underlying_close": pl.Float64}
        )
    near = fut.group_by("nse_symbol").agg(near_dte=pl.col("dte").min())
    fut = fut.join(near, on="nse_symbol").filter(pl.col("dte") == pl.col("near_dte"))
    return fut.group_by("nse_symbol").agg(underlying_close=pl.col("fut_px").first())


def _near_month_option_chain(
    fo: pl.DataFrame,
    underlyings: pl.DataFrame,
    *,
    session_date: dt.date,
    min_dte: int = MIN_DTE,
    max_dte: int = MAX_DTE,
) -> pl.DataFrame:
    """
    Near-month OPTSTK CE/PE rows with settle premium and FUTSTK spot.

    Empty frame (correct schema) when the zip has no usable chain.
    """
    fo_n = _normalize_fo_columns(fo)
    nse_names = underlyings["symbol"].str.strip_suffix(".NS").unique().to_list()
    opt = fo_n.filter(
        pl.col("instrument").cast(pl.Utf8).str.to_uppercase().is_in(["OPTSTK"])
        & pl.col("option_type").cast(pl.Utf8).str.to_uppercase().is_in(["CE", "PE"])
        & pl.col("symbol").cast(pl.Utf8).is_in(nse_names)
    )
    if opt.height == 0:
        return _empty_chain()

    settle = (
        pl.col("settle").cast(pl.Float64, strict=False)
        if "settle" in opt.columns
        else pl.lit(None, dtype=pl.Float64)
    )
    close = (
        pl.col("close").cast(pl.Float64, strict=False)
        if "close" in opt.columns
        else pl.lit(None, dtype=pl.Float64)
    )
    opt = opt.with_columns(
        expiry=_parse_expiry(pl.col("expiry")),
        strike=pl.col("strike").cast(pl.Float64, strict=False),
        premium=settle.fill_null(close),
        option_type=pl.col("option_type").cast(pl.Utf8).str.to_uppercase(),
        nse_symbol=pl.col("symbol").cast(pl.Utf8),
    ).filter(
        pl.col("expiry").is_not_null()
        & pl.col("strike").is_not_null()
        & (pl.col("premium") > 0.0)
    )
    opt = opt.with_columns(
        dte=(pl.col("expiry") - pl.lit(session_date)).dt.total_days().cast(pl.Int32)
    ).filter((pl.col("dte") >= min_dte) & (pl.col("dte") <= max_dte))
    if opt.height == 0:
        return _empty_chain()

    listed = underlyings.select(
        nse_symbol=pl.col("symbol").str.strip_suffix(".NS"),
        golden_symbol=pl.col("symbol"),
    )
    fut_spot = _near_fut_spot(fo_n, nse_names, session_date)
    spot_df = listed.join(fut_spot, on="nse_symbol", how="left")
    if "close" in underlyings.columns:
        fallback = underlyings.select(
            nse_symbol=pl.col("symbol").str.strip_suffix(".NS"),
            close=pl.col("close"),
        )
        spot_df = (
            spot_df.join(fallback, on="nse_symbol", how="left")
            .with_columns(
                underlying_close=pl.col("underlying_close").fill_null(pl.col("close"))
            )
            .drop("close")
        )
    spot_df = spot_df.filter(pl.col("underlying_close").is_not_null())
    opt = opt.join(spot_df, on="nse_symbol", how="inner")
    if opt.height == 0:
        return _empty_chain()

    near = opt.group_by("nse_symbol").agg(near_dte=pl.col("dte").min())
    return opt.join(near, on="nse_symbol").filter(pl.col("dte") == pl.col("near_dte"))


def extract_atm_iv_rows(
    fo: pl.DataFrame,
    underlyings: pl.DataFrame,
    *,
    session_date: dt.date,
    min_dte: int = MIN_DTE,
    max_dte: int = MAX_DTE,
) -> pl.DataFrame:
    """
    One ATM IV row per GOLDEN symbol that has a usable near-month option.

    ``underlyings`` needs ``symbol`` (GOLDEN). Optional ``close`` is a fallback
    spot when the bhavcopy has no FUTSTK row; production uses futures settle
    so ATM is not matched to split-adjusted GOLDEN closes.
    """
    opt = _near_month_option_chain(
        fo, underlyings, session_date=session_date, min_dte=min_dte, max_dte=max_dte
    )
    if opt.height == 0:
        return _empty_iv()

    opt = opt.with_columns(
        dist=(pl.col("strike") - pl.col("underlying_close")).abs()
    )
    atm_strike = opt.group_by("nse_symbol").agg(atm_dist=pl.col("dist").min())
    opt = opt.join(atm_strike, on="nse_symbol").filter(pl.col("dist") == pl.col("atm_dist"))
    tie = opt.group_by("nse_symbol").agg(pick_strike=pl.col("strike").min())
    opt = opt.join(tie, on="nse_symbol").filter(pl.col("strike") == pl.col("pick_strike"))

    rows: list[dict] = []
    for key, grp in opt.group_by(["nse_symbol", "strike", "expiry", "dte", "underlying_close", "golden_symbol"]):
        nse_symbol, strike, expiry, dte, spot, golden = key
        ivs: list[float] = []
        premium_ce: float | None = None
        premium_pe: float | None = None
        t = float(dte) / DAYS_PER_YEAR
        for rec in grp.iter_rows(named=True):
            is_call = rec["option_type"] == "CE"
            prem = float(rec["premium"])
            if is_call:
                premium_ce = prem
            else:
                premium_pe = prem
            iv = implied_volatility(
                prem,
                float(spot),
                float(strike),
                t,
                is_call=is_call,
            )
            if math.isfinite(iv):
                ivs.append(iv)
        if not ivs:
            continue
        straddle = (
            (premium_ce or 0.0) + (premium_pe or 0.0)
            if premium_ce is not None and premium_pe is not None
            else None
        )
        rows.append(
            {
                "symbol": golden,
                "date_only": session_date,
                "atm_iv_pct": 100.0 * (sum(ivs) / len(ivs)),
                "atm_strike": float(strike),
                "underlying_close": float(spot),
                "expiry": expiry,
                "source": SOURCE_BHAVCOPY_BS,
                "dte": int(dte),
                "premium_ce": premium_ce,
                "premium_pe": premium_pe,
                "straddle": straddle,
            }
        )
    if not rows:
        return _empty_iv()
    return pl.DataFrame(rows).select(_iv_schema_cols())


def _iv_schema_cols() -> list[str]:
    return [
        "symbol",
        "date_only",
        "atm_iv_pct",
        "atm_strike",
        "underlying_close",
        "expiry",
        "source",
        "dte",
        "premium_ce",
        "premium_pe",
        "straddle",
    ]


def _empty_iv() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "symbol": pl.Utf8,
            "date_only": pl.Date,
            "atm_iv_pct": pl.Float64,
            "atm_strike": pl.Float64,
            "underlying_close": pl.Float64,
            "expiry": pl.Date,
            "source": pl.Utf8,
            "dte": pl.Int32,
            "premium_ce": pl.Float64,
            "premium_pe": pl.Float64,
            "straddle": pl.Float64,
        }
    )


def _empty_chain() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "expiry": pl.Date,
            "strike": pl.Float64,
            "premium": pl.Float64,
            "option_type": pl.Utf8,
            "nse_symbol": pl.Utf8,
            "dte": pl.Int32,
            "golden_symbol": pl.Utf8,
            "underlying_close": pl.Float64,
            "near_dte": pl.Int32,
        }
    )


def _empty_marks() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "symbol": pl.Utf8,
            "date_only": pl.Date,
            "expiry": pl.Date,
            "strike": pl.Float64,
            "dte": pl.Int32,
            "underlying_close": pl.Float64,
            "premium_ce": pl.Float64,
            "premium_pe": pl.Float64,
            "straddle": pl.Float64,
            "source": pl.Utf8,
        }
    )


def extract_near_month_straddles(
    fo: pl.DataFrame,
    underlyings: pl.DataFrame,
    *,
    session_date: dt.date,
    min_dte: int = MIN_DTE,
    max_dte: int = MAX_DTE,
    moneyness: float = 0.10,
) -> pl.DataFrame:
    """
    Near-month CE+PE settle straddles within ``moneyness`` of FUTSTK spot.

    Used as V2 held-contract lookup: enter ATM on T, exit same strike/expiry on T+1.
    """
    opt = _near_month_option_chain(
        fo, underlyings, session_date=session_date, min_dte=min_dte, max_dte=max_dte
    )
    if opt.height == 0:
        return _empty_marks()
    opt = opt.filter(
        ((pl.col("strike") / pl.col("underlying_close")) - 1.0).abs() <= moneyness
    )
    if opt.height == 0:
        return _empty_marks()
    wide = (
        opt.group_by(["golden_symbol", "expiry", "strike", "dte", "underlying_close"])
        .agg(
            premium_ce=pl.col("premium")
            .filter(pl.col("option_type") == "CE")
            .first(),
            premium_pe=pl.col("premium")
            .filter(pl.col("option_type") == "PE")
            .first(),
        )
        .filter(
            pl.col("premium_ce").is_not_null() & pl.col("premium_pe").is_not_null()
        )
        .with_columns(
            symbol=pl.col("golden_symbol"),
            date_only=pl.lit(session_date).cast(pl.Date),
            straddle=pl.col("premium_ce") + pl.col("premium_pe"),
            source=pl.lit(SOURCE_BHAVCOPY_BS),
        )
        .drop("golden_symbol")
        .select(
            "symbol",
            "date_only",
            "expiry",
            "strike",
            "dte",
            "underlying_close",
            "premium_ce",
            "premium_pe",
            "straddle",
            "source",
        )
    )
    if wide.height == 0:
        return _empty_marks()
    return wide


def load_golden_daily_closes(
    symbols: list[str],
    parquet_dir: Path,
    start: dt.date,
    end: dt.date,
    *,
    csv_dir: Path | None = None,
) -> pl.DataFrame:
    """Session close per GOLDEN symbol from parquet, falling back to GOLDEN CSV."""
    csv_root = csv_dir if csv_dir is not None else Path("data/GOLDEN")
    frames: list[pl.DataFrame] = []
    for sym in symbols:
        path_pq = parquet_dir / f"{sym}.parquet"
        path_csv = csv_root / f"{sym}.csv"
        if path_pq.exists():
            daily = (
                pl.scan_parquet(path_pq)
                .select("date", "close")
                .with_columns(date_only=pl.col("date").dt.date())
                .filter((pl.col("date_only") >= start) & (pl.col("date_only") <= end))
                .group_by("date_only")
                .agg(close=pl.col("close").last())
                .with_columns(symbol=pl.lit(sym))
                .collect()
            )
        elif path_csv.exists():
            raw = load_csv_data(path_csv, datetime_col="date").select("date", "close")
            daily = (
                raw.with_columns(date_only=pl.col("date").dt.date())
                .filter((pl.col("date_only") >= start) & (pl.col("date_only") <= end))
                .group_by("date_only")
                .agg(close=pl.col("close").last())
                .with_columns(symbol=pl.lit(sym))
            )
        else:
            continue
        if daily.height:
            frames.append(daily)
    if not frames:
        return pl.DataFrame(
            schema={"date_only": pl.Date, "close": pl.Float64, "symbol": pl.Utf8}
        )
    return pl.concat(frames)
