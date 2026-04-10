# Algo Trade Platform

A Python-based algorithmic trading platform.

## Setup

1. Create a virtual environment (if not already created):
   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:
   - On Windows: `.\venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python src/main.py
```

## Trading Configurations

The platform uses specific intraday trading configurations tailored for each ETF. For a detailed explanation of the rationale behind these settings (such as RSI bands, VWAP stop losses, and Bollinger Bands), please see the [ETF Trading Configuration Rationale](ETF_TRADING_CONFIG.md) document.
