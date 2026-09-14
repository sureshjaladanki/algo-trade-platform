"""R0 step-up identity. Illustration is not Exit."""

from datetime import date
from pathlib import Path

import pytest

from src.books.step_up import (
    ILLUSTRATION_INR_PER_USD_ACQUIRE,
    ILLUSTRATION_INR_PER_USD_NOW,
    ILLUSTRATION_USD_COST,
    ILLUSTRATION_USD_VALUE,
    REAL_LOTS_PATH,
    STEP_UP_HURDLE_BPS,
    Lot,
    illustration_score,
    load_lots,
    r0_passes,
    real_lots_present,
    score_lots,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "r0" / "illustration_lots.csv"


def test_illustration_matches_plan_worked_example() -> None:
    score = illustration_score()
    assert score.source == "illustration"
    assert score.usd_unrealised == pytest.approx(200_000.0)
    assert score.inr_unrealised == pytest.approx(24_400_000.0)
    assert score.fx_accretion_inr == pytest.approx(6_000_000.0)
    assert score.tax_if_sold_after_cliff == pytest.approx(3_172_000.0)
    assert score.tax_stcg_short_lots == pytest.approx(0.0)
    # Plan text rounds tax to ~USD 34,500 / 400k = ~863 bps; exact is tax/INR value.
    assert score.step_up_bps_of_capital == pytest.approx(861.96, abs=0.05)
    assert score.step_up_bps_of_capital >= STEP_UP_HURDLE_BPS


def test_illustration_is_not_exit() -> None:
    assert not r0_passes(illustration_score())
    if real_lots_present():
        score = score_lots(
            load_lots(REAL_LOTS_PATH),
            cliff_date=date(2028, 3, 31),
            source="real",
        )
        assert r0_passes(score)


def test_short_lot_uses_slab_at_cliff() -> None:
    lot = Lot(
        acquisition_date=date(2027, 6, 1),
        usd_cost=ILLUSTRATION_USD_COST,
        usd_value=ILLUSTRATION_USD_VALUE,
        inr_per_usd_acquire=ILLUSTRATION_INR_PER_USD_ACQUIRE,
        inr_per_usd_now=ILLUSTRATION_INR_PER_USD_NOW,
    )
    score = score_lots((lot,), cliff_date=date(2028, 3, 31), source="illustration")
    assert score.tax_stcg_short_lots == pytest.approx(0.312 * 24_400_000.0)
    assert score.tax_if_sold_after_cliff == pytest.approx(score.tax_stcg_short_lots)


def test_load_lots_fixture_round_trips() -> None:
    lots = load_lots(FIXTURE)
    assert len(lots) == 1
    assert lots[0].usd_cost == ILLUSTRATION_USD_COST
    assert lots[0].usd_value == ILLUSTRATION_USD_VALUE
    score = score_lots(lots, cliff_date=date(2028, 3, 31), source="real")
    assert r0_passes(score)
