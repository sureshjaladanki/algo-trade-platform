import argparse
import yaml
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta

def fetch_and_save_1m_data(symbol, start_date, end_date, output_file):
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    print(f"Fetching 1m data for {symbol} from {start_str} to {end_str}...")
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_str, end=end_str, interval="1m")
        
        if df.empty:
            print(f"  Warning: No data found for {symbol} on {start_str}")
            return False
            
        # Clean up columns and index
        df.columns = df.columns.str.lower()
        df.index.name = 'datetime'
            
        df.to_csv(output_file)
        print(f"  Saved {len(df)} rows to {output_file}")
        return True
        
    except Exception as e:
        print(f"  Error processing {symbol}: {e}")
        return False

def fetch_and_save_1d_data(symbol, start_date, end_date, output_file):
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    print(f"Fetching 1d data for {symbol} from {start_str} to {end_str}...")
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_str, end=end_str, interval="1d")
        
        if df.empty:
            print(f"  Warning: No 1d data found for {symbol} between {start_str} and {end_str}")
            return False
            
        # Clean up columns and index
        df.columns = df.columns.str.lower()
        df.index.name = 'datetime'
            
        df.to_csv(output_file)
        print(f"  Saved {len(df)} rows to {output_file}")
        return True
        
    except Exception as e:
        print(f"  Error processing {symbol} (1d): {e}")
        return False

def fetch_and_save_1m_history(symbol, end_date, output_file):
    end_str = end_date.strftime("%Y-%m-%d")
    print(f"Fetching max 1m history (7d) for {symbol} up to {end_str}...")
    try:
        ticker = yf.Ticker(symbol)
        # Fetch 7 days of data up to the end_date
        # Note: yfinance limits 1m data to the last 7 days from today,
        # but we can filter it to only include data before end_date
        df = ticker.history(period="7d", interval="1m")
        
        if df.empty:
            print(f"  Warning: No 1m history data found for {symbol}")
            return False
            
        # Filter to only include data before end_date
        # df.index is timezone-aware, so we compare with date strings or convert
        df = df[df.index < end_str]
        
        if df.empty:
            print(f"  Warning: No 1m history data found for {symbol} before {end_str}")
            return False
            
        # Clean up columns and index
        df.columns = df.columns.str.lower()
        df.index.name = 'datetime'
            
        df.to_csv(output_file)
        print(f"  Saved {len(df)} rows to {output_file}")
        return True
        
    except Exception as e:
        print(f"  Error processing {symbol} (1m history): {e}")
        return False

def generate_dry_run_data(target_date_str):
    # Parse the target date
    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        # yfinance requires the end date to be the next day to include the target day
        next_date = target_date + timedelta(days=1)
        
    except ValueError:
        print("Error: Invalid date format. Please use YYYY-MM-DD.")
        return

    # Paths
    config_path = Path("config/strategy_engine.yml")
    output_dir = Path("data/processed")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read config
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        return
        
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
        
    # Process regime_symbol
    regime_symbol = config.get("regime_symbol", "")
    if regime_symbol:
        print(f"\n--- Processing {regime_symbol} regime_symbol ---")
        output_file = output_dir / f"{regime_symbol}_1m_current_day.csv"
        fetch_and_save_1m_data(regime_symbol, target_date, next_date, output_file)
        
    # Process advance_decline_symbols
    advance_decline_symbols = config.get("advance_decline_symbols", [])
    if advance_decline_symbols:
        print(f"\n--- Processing {len(advance_decline_symbols)} advance_decline_symbols ---")
        for symbol in advance_decline_symbols:
            output_file = output_dir / f"{symbol}_1m_current_day.csv"
            fetch_and_save_1m_data(symbol, target_date, next_date, output_file)
            
    # Process trade_symbols
    trade_symbols_raw = config.get("trade_symbols", {})
    trade_symbols = list(trade_symbols_raw.keys())
            
    if trade_symbols:
        print(f"\n--- Processing {len(trade_symbols)} trade_symbols ---")
        for symbol in trade_symbols:
            # Current day
            current_output = output_dir / f"{symbol}_1m_current_day.csv"
            fetch_and_save_1m_data(symbol, target_date, next_date, current_output)
            
            # Max 1m history (7 days) up to T - 1
            history_output = output_dir / f"{symbol}_1m_history.csv"
            fetch_and_save_1m_history(symbol, target_date, history_output)
            
            # 30 days 1d data up to T - 1
            thirty_days_ago = target_date - timedelta(days=30)
            thirty_days_output = output_dir / f"{symbol}_1d_30d.csv"
            fetch_and_save_1d_data(symbol, thirty_days_ago, target_date, thirty_days_output)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 1m and 1d ticks for tracked/trade symbols for a specific day.")
    parser.add_argument("--date", type=str, required=True, help="Target date in YYYY-MM-DD format")
    
    args = parser.parse_args()
    generate_dry_run_data(args.date)
