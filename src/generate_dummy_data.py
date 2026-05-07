import polars as pl
from datetime import datetime, timedelta
import numpy as np

def generate_dummy_data(output_path: str = "dummy_1m_data.csv", rows: int = 10000):
    """
    Generates a dummy 1-minute OHLCV dataset for testing the pipeline.
    """
    start_time = datetime(2023, 1, 1, 9, 30)
    timestamps = [start_time + timedelta(minutes=i) for i in range(rows)]
    
    # Generate random walk for close price
    np.random.seed(42)
    returns = np.random.normal(loc=0.00001, scale=0.001, size=rows)
    close_prices = 100.0 * np.exp(np.cumsum(returns))
    
    # Generate open, high, low based on close
    open_prices = close_prices * np.random.normal(1.0, 0.0005, size=rows)
    high_prices = np.maximum(open_prices, close_prices) * np.random.uniform(1.0, 1.001, size=rows)
    low_prices = np.minimum(open_prices, close_prices) * np.random.uniform(0.999, 1.0, size=rows)
    volumes = np.random.randint(100, 10000, size=rows)
    
    df = pl.DataFrame({
        "timestamp": timestamps,
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "volume": volumes
    })
    
    df.write_csv(output_path)
    print(f"Dummy data generated at {output_path} with {rows} rows.")

if __name__ == "__main__":
    generate_dummy_data()
