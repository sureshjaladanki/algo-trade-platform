"""M9-0 FO bhavcopy ATM IV extraction + BS inversion."""

from __future__ import annotations

import datetime as dt
import math

import polars as pl

from src.experiments.eval_horizon_m9_v1_index import INDEX_OPPORTUNITY_FEATURES
from src.horizon.fresh.opportunity import OPPORTUNITY_FEATURES
from src.horizon.m9.bhavcopy_iv import extract_atm_iv_rows, nse_fo_symbol
from src.horizon.m9.black_scholes import black_scholes_price, implied_volatility


def test_index_opportunity_features_drop_volume_z() -> None:
    assert "volume_z" in OPPORTUNITY_FEATURES
    assert "volume_z" not in INDEX_OPPORTUNITY_FEATURES
    assert set(INDEX_OPPORTUNITY_FEATURES) == set(OPPORTUNITY_FEATURES) - {"volume_z"}


def test_bs_roundtrip_atm() -> None:
    spot, strike, t, sigma = 1000.0, 1000.0, 30.0 / 365.0, 0.25
    call = black_scholes_price(spot, strike, t, sigma, is_call=True)
    put = black_scholes_price(spot, strike, t, sigma, is_call=False)
    assert abs(implied_volatility(call, spot, strike, t, is_call=True) - sigma) < 1e-4
    assert abs(implied_volatility(put, spot, strike, t, is_call=False) - sigma) < 1e-4


def test_nse_fo_symbol_strips_ns() -> None:
    assert nse_fo_symbol("RELIANCE.NS") == "RELIANCE"
    assert nse_fo_symbol("BAJAJ-AUTO.NS") == "BAJAJ-AUTO"


def test_extract_atm_iv_near_month_and_no_future_expiry_leak() -> None:
    session = dt.date(2018, 1, 2)
    t_near = 30.0 / 365.0
    sigma = 0.20
    spot = 1000.0
    rows = []
    for strike in (900.0, 1000.0, 1100.0):
        for typ, is_call in (("CE", True), ("PE", False)):
            prem = black_scholes_price(spot, strike, t_near, sigma, is_call=is_call)
            rows.append(
                {
                    "INSTRUMENT": "OPTSTK",
                    "SYMBOL": "RELIANCE",
                    "EXPIRY_DT": "01-Feb-2018",
                    "STRIKE_PR": strike,
                    "OPTION_TYP": typ,
                    "CLOSE": prem,
                    "SETTLE_PR": prem,
                }
            )
    # Farther expiry still inside [7, 45] at 40% IV must not beat near-month.
    t_far = 44.0 / 365.0
    prem_far = black_scholes_price(spot, 1000.0, t_far, 0.40, is_call=True)
    rows.append(
        {
            "INSTRUMENT": "OPTSTK",
            "SYMBOL": "RELIANCE",
            "EXPIRY_DT": "15-Feb-2018",
            "STRIKE_PR": 1000.0,
            "OPTION_TYP": "CE",
            "CLOSE": prem_far,
            "SETTLE_PR": prem_far,
        }
    )
    # DTE=3 weekly - outside [7, 45]
    rows.append(
        {
            "INSTRUMENT": "OPTSTK",
            "SYMBOL": "RELIANCE",
            "EXPIRY_DT": "05-Jan-2018",
            "STRIKE_PR": 1000.0,
            "OPTION_TYP": "CE",
            "CLOSE": 10.0,
            "SETTLE_PR": 10.0,
        }
    )
    fo = pl.DataFrame(rows)
    under = pl.DataFrame({"symbol": ["RELIANCE.NS"], "close": [spot]})
    out = extract_atm_iv_rows(fo, under, session_date=session)
    assert out.height == 1
    assert out["symbol"][0] == "RELIANCE.NS"
    assert out["atm_strike"][0] == 1000.0
    assert out["dte"][0] == 30
    assert math.isclose(out["atm_iv_pct"][0], 20.0, abs_tol=0.15)
    assert out["date_only"][0] == session
    assert out["straddle"][0] is not None and out["straddle"][0] > 0.0


def test_extract_atm_prefers_futstk_settle_over_adjusted_close() -> None:
    session = dt.date(2018, 1, 2)
    t = 30.0 / 365.0
    sigma = 0.20
    fut_spot = 1000.0
    prem = black_scholes_price(fut_spot, 1000.0, t, sigma, is_call=True)
    fo = pl.DataFrame(
        [
            {
                "INSTRUMENT": "FUTSTK",
                "SYMBOL": "RELIANCE",
                "EXPIRY_DT": "01-Feb-2018",
                "STRIKE_PR": 0.0,
                "OPTION_TYP": "XX",
                "CLOSE": fut_spot,
                "SETTLE_PR": fut_spot,
            },
            {
                "INSTRUMENT": "OPTSTK",
                "SYMBOL": "RELIANCE",
                "EXPIRY_DT": "01-Feb-2018",
                "STRIKE_PR": 1000.0,
                "OPTION_TYP": "CE",
                "CLOSE": prem,
                "SETTLE_PR": prem,
            },
        ]
    )
    # Split-adjusted GOLDEN close would pick the wrong strike if used as spot.
    under = pl.DataFrame({"symbol": ["RELIANCE.NS"], "close": [250.0]})
    out = extract_atm_iv_rows(fo, under, session_date=session)
    assert out.height == 1
    assert out["underlying_close"][0] == fut_spot
    assert math.isclose(out["atm_iv_pct"][0], 20.0, abs_tol=0.2)
