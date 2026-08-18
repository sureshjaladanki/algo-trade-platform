# Algo Trade Platform

Tier 1 Regime Strategy engine for the Nifty 100 universe, NSE India.

This module provides the macro-gating layer for intraday and swing trading strategies using a cascading tier architecture.

## Structure
- `src/regime/`: Tier 1 Regime classifiers.
  - `types.py`: Enums for Daily (`SUPPORTIVE`, `AMBIGUOUS`, `HOSTILE`, `NO_TRADE`) and Intraday (`TREND_UP`, etc.) regimes.
  - `features.py`: Feature engineering using `polars`. Calculates EMA20 distances, VWAP distances, TOD-normalized returns, etc.
  - `daily.py`: Rule-based pre-open daily classifier to gate the platform.
  - `intraday.py`: 4-state Gaussian HMM trained on 15m normalized emissions to classify intraday environments.
- `docs/regime-tier1-verdict.md`: Detailed architecture decisions and feature selections by independent judges.

## Setup
Built with Python 3.12 and Poetry. Conventions: [docs/repo-conventions.md](docs/repo-conventions.md), [docs/coding-conventions.md](docs/coding-conventions.md).

```bash
poetry install --with dev
```

## Tools
- `polars` for fast, vectorized feature engineering and dataframe manipulations.
- `hmmlearn` for the Intraday 4-State Gaussian HMM.
- `scikit-learn` for basic metrics and pre-processing if needed.
