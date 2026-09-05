"""Book P after-tax arithmetic. Live TRI reconciliation is P1's stop, not this unit test."""

from decimal import Decimal

from src.books.packaged import packaged_after_tax, self_run_after_tax, verdict
from src.tax import ltcg, stcg


def test_packaged_one_redemption_ltcg() -> None:
    path = packaged_after_tax(
        start_tri=Decimal(100),
        end_tri=Decimal(200),
        ter=Decimal("0.0030"),
        exit_load=Decimal("0.01"),
        holding_years=Decimal(5),
        capital=Decimal(5000000),
    )
    gross = Decimal(2)
    net = gross * (Decimal(1) - Decimal("0.0030")) ** Decimal(5)
    pretax = Decimal(5000000) * net
    assert path.tax == ltcg(pretax - Decimal(5000000), Decimal(0))
    assert path.terminal == pretax - path.tax


def test_self_run_uses_stcg_and_costs() -> None:
    path = self_run_after_tax(
        start_tri=Decimal(100),
        end_tri=Decimal(200),
        turnover=Decimal("0.30"),
        holding_years=Decimal(1),
        capital=Decimal(5000000),
    )
    assert path.tax == stcg(Decimal(5000000) * Decimal("0.30"))
    assert path.friction > 0


def test_verdict_bands() -> None:
    assert verdict(Decimal(150)).kind == "packaged"
    assert verdict(Decimal(-150)).kind == "self_run"
    assert verdict(Decimal(40)).kind == "tie_buy_fund"
