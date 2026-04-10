import argparse
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from growwapi import GrowwAPI

# Ensure the scripts directory is in the path to import auth_groww
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from auth_groww import init_groww_token

def parse_period_to_days(period: str) -> int:
    """Convert period string (e.g., '7d', '1mo', '1y') to number of days."""
    period = period.lower()
    if period.endswith('d'):
        return int(period[:-1])
    elif period.endswith('mo'):
        return int(period[:-2]) * 30
    elif period.endswith('y'):
        return int(period[:-1]) * 365
    else:
        raise ValueError(f"Unsupported period format: {period}. Use 'd', 'mo', or 'y'.")

def map_interval_to_groww_format(interval: str) -> str:
    """Convert interval string (e.g., '1m', '5m', '1h', '1d') to Groww API format."""
    interval = interval.lower()
    mapping = {
        '1m': '1minute',
        '2m': '2minute',
        '3m': '3minute',
        '5m': '5minute',
        '10m': '10minute',
        '15m': '15minute',
        '30m': '30minute',
        '1h': '1hour',
        '4h': '4hour',
        '1d': '1day',
        '1wk': '1week',
        '1mo': '1month'
    }
    if interval not in mapping:
        raise ValueError(f"Unsupported interval format: {interval}. Supported: {list(mapping.keys())}")
    return mapping[interval]

def fetch_groww_ticks(symbol: str, interval: str, period: str):
    """
    Pulls historical data (ticks/candles) from Groww Official API using the Python SDK.
    
    :param symbol: Ticker symbol (e.g., 'RELIANCE', 'NIFTYBEES')
    :param interval: Data interval (e.g., '1m', '5m', '15m', '1h', '1d')
    :param period: Data period to download (e.g., '1d', '7d', '1mo', '1y')
    """
    print("Attempting to get Groww API access token...")
    try:
        token = init_groww_token()
    except Exception as e:
        print(f"Error: Could not compute Groww API access token. {e}")
        sys.exit(1)

    if not token:
        print("Error: Groww API access token is required for the official API.")
        sys.exit(1)

    print(f"Fetching data from Groww API for {symbol} | Interval: {interval} | Period: {period}...")
    
    try:
        days = parse_period_to_days(period)
        groww_interval = map_interval_to_groww_format(interval)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    # Format times to yyyy-MM-dd HH:mm:ss
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # Construct Groww Symbol (assuming NSE CASH segment for equities/ETFs by default)
    groww_symbol = f"NSE-{symbol}"
    
    # Initialize Groww API
    groww = GrowwAPI(token)
    
    try:
        # Fetch historical candles using the Python SDK
        data = groww.get_historical_candles(
            exchange=groww.EXCHANGE_NSE,
            segment=groww.SEGMENT_CASH,
            groww_symbol=groww_symbol,
            start_time=start_time_str,
            end_time=end_time_str,
            candle_interval=groww_interval
        )
    except Exception as e:
        print(f"Error: Failed to fetch data from Groww API. {e}")
        sys.exit(1)
        
    if not data:
        print(f"Error: Invalid response or no data found for {symbol}.")
        sys.exit(1)
        
    # The SDK might return the payload directly or the full response
    if "candles" in data:
        candles = data["candles"]
    elif "payload" in data and "candles" in data["payload"]:
        candles = data["payload"]["candles"]
    else:
        print(f"Error: Invalid response structure for {symbol}.")
        print(data)
        sys.exit(1)
        
    if not candles:
        print(f"Error: No data found for {symbol} in the given period.")
        sys.exit(1)
        
    # Groww official API candles format: [timestamp, open, high, low, close, volume, open_interest]
    df = pd.DataFrame(candles, columns=["Timestamp", "Open", "High", "Low", "Close", "Volume", "Open_Interest"])
    
    # Convert timestamp (yyyy-MM-ddTHH:mm:ss) to datetime
    df["Datetime"] = pd.to_datetime(df["Timestamp"]).dt.tz_localize("Asia/Kolkata")
    df.set_index("Datetime", inplace=True)
    df.drop(columns=["Timestamp"], inplace=True)
    
    # Ensure the target directory exists
    output_dir = os.path.join("data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{symbol}_{interval}_{period}_groww.csv"
    filepath = os.path.join(output_dir, filename)
    
    # Write to CSV
    df.to_csv(filepath)
    print(f"Successfully downloaded {len(df)} rows.")
    print(f"Data saved to: {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull historical tick/candle data from Groww Official API.")
    parser.add_argument("--symbol", type=str, required=True, help="Ticker symbol (e.g., RELIANCE, NIFTYBEES)")
    parser.add_argument("--interval", type=str, required=True, help="Tick interval (e.g., 1m, 5m, 1h, 1d)")
    parser.add_argument("--period", type=str, required=True, help="Data period (e.g., 1d, 7d, 1mo, 1y)")
    
    args = parser.parse_args()
    
    fetch_groww_ticks(args.symbol, args.interval, args.period)
