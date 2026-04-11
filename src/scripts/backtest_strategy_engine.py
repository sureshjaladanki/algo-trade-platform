"""
Generate processed CSVs for StrategyEngine dry runs from yfinance.

Consolidated responsibilities (formerly split with prep_intraday_current_day.py):
- Fetch 1m bars for regime, advance/decline, and trade symbols for a target session date.
- Clip to India cash session (09:15–15:29 IST) and normalize columns for DataAdapter.
- Align all symbols to a common minute index (master = JUNIORBEES.NS if present, else first
  trade symbol with data) so the engine's lockstep generators do not desync.
- For trade symbols only: refresh *_1m_history.csv (7d 1m before target date) and *_1d_30d.csv.

Optional: append a prior session CSV into one symbol's *_1m_history.csv before writing new
current_day files. For that symbol only, the yfinance 1m history refresh is skipped so the
append is not overwritten.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
import yfinance as yf

PROCESSED = Path("data/processed")
SESSION_START = "09:15"
SESSION_END = "15:29"
STRATEGY_ENGINE_CONFIG = Path("config/strategy_engine.yml")


def _yf_to_processed(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    df = df.rename_axis("datetime")
    df = df.reset_index()
    if df["datetime"].dt.tz is None:
        df["datetime"] = df["datetime"].dt.tz_localize("Asia/Kolkata")
    else:
        df["datetime"] = df["datetime"].dt.tz_convert("Asia/Kolkata")
    for col in ("dividends", "stock splits"):
        if col not in df.columns:
            df[col] = 0.0
    return df[
        ["datetime", "open", "high", "low", "close", "volume", "dividends", "stock splits"]
    ].copy()


def fetch_1m_session(symbol: str, session_date_str: str, period: str = "7d") -> pd.DataFrame:
    """Download 1m from yfinance, keep one calendar day, clip to cash session."""
    raw = yf.Ticker(symbol).history(period=period, interval="1m")
    if raw.empty:
        raise RuntimeError(f"No yfinance 1m data for {symbol}")
    proc = _yf_to_processed(raw)
    day = pd.Timestamp(session_date_str).date()
    proc = proc.loc[proc["datetime"].dt.date == day].copy()
    t0 = pd.Timestamp(f"{session_date_str} {SESSION_START}+05:30")
    t1 = pd.Timestamp(f"{session_date_str} {SESSION_END}+05:30")
    proc = proc.loc[proc["datetime"].between(t0, t1, inclusive="both")]
    return proc.sort_values("datetime", ignore_index=True)


def align_to_master(dfs: dict[str, pd.DataFrame], master: str) -> dict[str, pd.DataFrame]:
    idx = dfs[master]["datetime"]
    return {
        sym: d.set_index("datetime").reindex(idx).ffill().bfill().reset_index()
        for sym, d in dfs.items()
    }


def append_prior_day_to_history(symbol: str, prior_csv: Path, history_csv: Path) -> None:
    prior = pd.read_csv(prior_csv, parse_dates=["datetime"])
    hist = pd.read_csv(history_csv, parse_dates=["datetime"])
    (
        pd.concat([hist, prior], ignore_index=True)
        .drop_duplicates(subset=["datetime"], keep="last")
        .sort_values("datetime", ignore_index=True)
        .to_csv(history_csv, index=False)
    )


def pick_master_symbol(trade_symbols: list[str], raw_dfs: dict[str, pd.DataFrame]) -> str:
    for cand in ("JUNIORBEES.NS",):
        if cand in raw_dfs and not raw_dfs[cand].empty:
            return cand
    for s in sorted(trade_symbols):
        if s in raw_dfs and not raw_dfs[s].empty:
            return s
    for s in sorted(raw_dfs.keys()):
        if not raw_dfs[s].empty:
            return s
    raise RuntimeError("No non-empty intraday dataframe; cannot pick master for alignment")


def _load_engine_symbols(config_path: Path) -> tuple[str, list[str], list[str]]:
    """
    Returns (regime_symbol, advance_decline_symbols, trade_symbol_names).
    """
    with open(config_path, "r", encoding="utf-8") as f:
        config: dict[str, Any] = yaml.safe_load(f)

    regime = config.get("regime_symbol", "") or ""
    advance_decline = list(config.get("advance_decline_symbols", []))
    trade_map = config.get("trade_symbols", {})
    trade_keys = list(trade_map.keys()) if isinstance(trade_map, dict) else []
    return regime, advance_decline, trade_keys


def _all_intraday_symbols(
    regime: str, advance_decline: list[str], trade_symbols: list[str]
) -> list[str]:
    return sorted({regime, *advance_decline, *trade_symbols} - {""})


def fetch_and_save_1d_data(
    symbol: str, start_date: datetime, end_date: datetime, output_file: Path
) -> bool:
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"Fetching 1d data for {symbol} from {start_str} to {end_str}...")
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_str, end=end_str, interval="1d")

        if df.empty:
            print(f"  Warning: No 1d data found for {symbol} between {start_str} and {end_str}")
            return False

        df.columns = df.columns.str.lower()
        df.index.name = "datetime"

        df.to_csv(output_file)
        print(f"  Saved {len(df)} rows to {output_file}")
        return True

    except Exception as e:
        print(f"  Error processing {symbol} (1d): {e}")
        return False


def fetch_and_save_1m_history(symbol: str, end_date: datetime, output_file: Path) -> bool:
    end_str = end_date.strftime("%Y-%m-%d")
    print(f"Fetching max 1m history (7d) for {symbol} up to {end_str}...")
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="7d", interval="1m")

        if df.empty:
            print(f"  Warning: No 1m history data found for {symbol}")
            return False

        df = df[df.index < end_str]

        if df.empty:
            print(f"  Warning: No 1m history data found for {symbol} before {end_str}")
            return False

        df.columns = df.columns.str.lower()
        df.index.name = "datetime"

        df.to_csv(output_file)
        print(f"  Saved {len(df)} rows to {output_file}")
        return True

    except Exception as e:
        print(f"  Error processing {symbol} (1m history): {e}")
        return False


def _fetch_session_bars(symbols: list[str], target_date_str: str) -> dict[str, pd.DataFrame]:
    print(f"Fetching aligned 1m session for {target_date_str} ({len(symbols)} symbols)...")
    raw_dfs: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        try:
            raw_dfs[sym] = fetch_1m_session(sym, target_date_str)
            print(f"  {sym}: {len(raw_dfs[sym])} bars (pre-align)")
        except Exception as e:
            print(f"  Error {sym}: {e}")
            raise
    return raw_dfs


def _write_current_day_csvs(aligned: dict[str, pd.DataFrame], output_dir: Path) -> None:
    print("Writing *_1m_current_day.csv")
    for sym, d in aligned.items():
        path = output_dir / f"{sym}_1m_current_day.csv"
        d.to_csv(path, index=False)
        print(f"  {path} ({len(d)} rows)")


def _refresh_trade_symbol_history_and_daily(
    trade_symbols: list[str],
    target_date: datetime,
    target_date_str: str,
    output_dir: Path,
    skip_history_for: set[str],
) -> None:
    print(f"\n--- Trade symbols: 1m history + 1d (30d) up to {target_date_str} ---")
    if skip_history_for:
        print(
            f"  (Skipping 1m history yfinance refresh for {skip_history_for} "
            f"after --append-prior-to-history; file already updated.)"
        )
    thirty_days_ago = target_date - timedelta(days=30)
    for symbol in trade_symbols:
        history_output = output_dir / f"{symbol}_1m_history.csv"
        if symbol not in skip_history_for:
            fetch_and_save_1m_history(symbol, target_date, history_output)
        daily_output = output_dir / f"{symbol}_1d_30d.csv"
        fetch_and_save_1d_data(symbol, thirty_days_ago, target_date, daily_output)


def generate_dry_run_data(
    target_date_str: str,
    append_prior: tuple[str, Path] | None = None,
    master_symbol: str | None = None,
) -> None:
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD.")
        return

    output_dir = PROCESSED
    output_dir.mkdir(parents=True, exist_ok=True)

    if not STRATEGY_ENGINE_CONFIG.exists():
        print(f"Error: Config file not found at {STRATEGY_ENGINE_CONFIG}")
        return

    regime_symbol, advance_decline_symbols, trade_symbols = _load_engine_symbols(
        STRATEGY_ENGINE_CONFIG
    )
    symbols = _all_intraday_symbols(regime_symbol, advance_decline_symbols, trade_symbols)

    if append_prior:
        sym, prior_path = append_prior[0], Path(append_prior[1])
        history_csv = output_dir / f"{sym}_1m_history.csv"
        append_prior_day_to_history(sym, prior_path, history_csv)
        print(f"Appended prior session into {history_csv}\n")

    raw_dfs = _fetch_session_bars(symbols, target_date_str)

    master = master_symbol or pick_master_symbol(trade_symbols, raw_dfs)
    print(f"Aligning all symbols to master index: {master} ({len(raw_dfs[master])} rows)\n")
    aligned = align_to_master(raw_dfs, master)

    _write_current_day_csvs(aligned, output_dir)

    if trade_symbols:
        skip_hist = {append_prior[0]} if append_prior else set()
        _refresh_trade_symbol_history_and_daily(
            trade_symbols, target_date, target_date_str, output_dir, skip_hist
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate aligned 1m current_day + 1m history + 1d data for StrategyEngine dry runs."
    )
    parser.add_argument("--date", type=str, required=True, help="Target session date YYYY-MM-DD")
    parser.add_argument(
        "--append-prior-to-history",
        nargs=2,
        metavar=("SYMBOL", "PRIOR_CSV"),
        help="Append PRIOR_CSV into SYMBOL_1m_history.csv before current_day write; skips yf 1m history refresh for SYMBOL only",
    )
    parser.add_argument(
        "--master",
        type=str,
        default=None,
        help="Symbol to use as datetime index master for alignment (default: JUNIORBEES.NS or first trade symbol)",
    )
    args = parser.parse_args()
    append = tuple(args.append_prior_to_history) if args.append_prior_to_history else None
    generate_dry_run_data(args.date, append_prior=append, master_symbol=args.master)


if __name__ == "__main__":
    main()
