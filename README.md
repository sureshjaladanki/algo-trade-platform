# Algo Trade Platform

A Python-based algorithmic trading platform.

## License

This project is licensed for **non-commercial use only** under the PolyForm Noncommercial License 1.0.0. See [`LICENSE`](LICENSE).

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

The platform uses specific intraday trading configurations tailored for each ETF.

- See [ETF Trading Configuration Rationale](ETF_TRADING_CONFIG.md) for strategy parameters and the current behavior.
- See [ETF Trading System Design](ETF_TRADING_SYSTEM.md) for the event-driven microservices architecture (Redis Streams, services, message contracts).
