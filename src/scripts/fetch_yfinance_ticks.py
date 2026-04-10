import argparse
import yfinance as yf
import sys
import os

def fetch_yfinance_ticks(symbol: str, interval: str, period: str):
    """
    Pulls historical data (ticks/candles) from yfinance.
    
    :param symbol: Ticker symbol (e.g., 'AAPL', '^NSEI')
    :param interval: Data interval (e.g., '1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
    :param period: Data period to download (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
    """
    print(f"Fetching data for {symbol} | Interval: {interval} | Period: {period}...")
    
    ticker = yf.Ticker(symbol)
    
    # In yfinance, 'period' refers to the time length (e.g., 1d, 1mo) 
    # and 'interval' refers to the duration of each tick/candle (e.g., 1m, 1h).
    df = ticker.history(period=period, interval=interval)
    
    if df.empty:
        print(f"Error: No data found for {symbol} with interval='{interval}' and period='{period}'.")
        print("Please check if the symbol is correct and if the combination of interval and period is supported by Yahoo Finance.")
        sys.exit(1)
        
    # Ensure the target directory exists
    output_dir = os.path.join("data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"{symbol}_{interval}_{period}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # Convert column headers and index name to lowercase
    df.columns = df.columns.str.lower()
    if df.index.name:
        df.index.name = df.index.name.lower()
        
    # Write to CSV
    df.to_csv(filepath)
    print(f"Successfully downloaded {len(df)} rows.")
    print(f"Data saved to: {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pull historical tick/candle data from yfinance.")
    parser.add_argument("--symbol", type=str, required=True, help="Ticker symbol (e.g., AAPL, MSFT, ^NSEI)")
    parser.add_argument("--interval", type=str, required=True, help="Tick interval (e.g., 1m, 5m, 1h, 1d)")
    parser.add_argument("--period", type=str, required=True, help="Data period (e.g., 1d, 5d, 1mo, 1y, max)")
    
    args = parser.parse_args()
    
    fetch_yfinance_ticks(args.symbol, args.interval, args.period)
