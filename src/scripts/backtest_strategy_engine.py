"""
Generate processed CSVs for StrategyEngine dry runs from yfinance.

Compared to `generate_strategy_engine_dry_run_data.py`, this script additionally:
- Clips 1m data to the India cash session (09:15–15:29 IST) for the target date
- Normalizes timestamps/columns into the processed schema expected by the DataAdapter
- Aligns ALL intraday symbols to the INDIA VIX (`regime_symbol`, typically `^INDIAVIX`) minute index
  so StrategyEngine lockstep generators don't desync
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


def fetch_1m_session_df(symbol: str, session_date_str: str, period: str = "7d") -> pd.DataFrame:
    """
    Download 1m data from yfinance, keep only the target calendar day,
    and clip to the India cash session.
    """
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


def generate_dry_run_data(
    target_date_str: str,
) -> None:
    # Parse the target date
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD.")
        return

    # Paths
    config_path = STRATEGY_ENGINE_CONFIG
    output_dir = PROCESSED
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read config
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return

    with open(config_path, "r", encoding="utf-8") as f:
        config: dict[str, Any] = yaml.safe_load(f)

    regime_symbol = config.get("regime_symbol", "") or ""
    advance_decline_symbols = list(config.get("advance_decline_symbols", []))
    trade_symbols_raw = config.get("trade_symbols", {})
    trade_symbols = list(trade_symbols_raw.keys()) if isinstance(trade_symbols_raw, dict) else []

    # Fetch all intraday symbols first, then align + write
    intraday_symbols = sorted({regime_symbol, *advance_decline_symbols, *trade_symbols} - {""})
    if not intraday_symbols:
        print("Error: No intraday symbols found in config.")
        return

    print(f"Fetching 1m session for {target_date_str} ({len(intraday_symbols)} symbols)...")
    intraday_dfs: dict[str, pd.DataFrame] = {}
    for symbol in intraday_symbols:
        try:
            df = fetch_1m_session_df(symbol, target_date_str)
            intraday_dfs[symbol] = df
            print(f"  {symbol}: {len(df)} bars (pre-align)")
        except Exception as e:
            print(f"  Error processing {symbol} (1m session): {e}")
            raise

    master = regime_symbol
    if not master:
        raise RuntimeError("regime_symbol missing in config; cannot align to India VIX master")
    if master not in intraday_dfs or intraday_dfs[master].empty:
        raise RuntimeError(
            f"Master symbol {master} missing/empty; cannot align. "
            f"Ensure India VIX (^INDIAVIX) is included and has data for the session."
        )

    print(f"\nAligning all symbols to master index: {master} ({len(intraday_dfs[master])} rows)")
    master_idx = intraday_dfs[master]["datetime"]
    aligned = {
        sym: df.set_index("datetime").reindex(master_idx).ffill().bfill().reset_index()
        for sym, df in intraday_dfs.items()
    }

    print("\nWriting *_1m_current_day.csv")
    for symbol, df in aligned.items():
        out = output_dir / f"{symbol}_1m_current_day.csv"
        df.to_csv(out, index=False)
        print(f"  {out} ({len(df)} rows)")

    # Trade symbols: refresh 1m history + 1d (30d)
    if trade_symbols:
        print(f"\n--- Trade symbols: 1m history + 1d (30d) up to {target_date_str} ---")
        thirty_days_ago = target_date - timedelta(days=30)
        for symbol in trade_symbols:
            history_output = output_dir / f"{symbol}_1m_history.csv"
            fetch_and_save_1m_history(symbol, target_date, history_output)

            daily_output = output_dir / f"{symbol}_1d_30d.csv"
            fetch_and_save_1d_data(symbol, thirty_days_ago, target_date, daily_output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate aligned 1m current_day + 1m history + 1d data for StrategyEngine dry runs."
    )
    parser.add_argument("--date", type=str, required=True, help="Target session date YYYY-MM-DD")
    args = parser.parse_args()
    generate_dry_run_data(args.date)


if __name__ == "__main__":
    main()
