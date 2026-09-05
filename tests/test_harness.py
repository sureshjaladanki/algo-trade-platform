"""H0: MDE, pre-registration load, spec budget, look-ahead, Nifty 50 TRI benchmark."""

from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal
from pathlib import Path

import polars as pl
import pytest

from src.harness import (
    SPEC_BUDGET,
    PreRegistrationError,
    SpecBudgetError,
    benchmark,
    date_shift_test,
    load_all_preregistrations,
    load_preregistration,
    mde,
    spec_budget_guard,
)

PREREG = Path(__file__).resolve().parents[1] / "docs" / "next"


def test_mde_blueprint_section_5_1() -> None:
    assert mde(0.005, 5) == pytest.approx(0.0063, rel=0.01)
    assert mde(0.08, 20) == pytest.approx(0.0501, rel=0.01)
    assert mde(0.10, 15) == pytest.approx(0.0723, rel=0.01)
    assert mde(0.039, 0.09) == pytest.approx(0.364, rel=0.01)
    assert mde(0.039, 1) == pytest.approx(0.109, rel=0.01)
    assert mde(0.039, 20) == pytest.approx(0.0244, rel=0.01)


def test_mde_rejects_non_default_power() -> None:
    with pytest.raises(ValueError, match="80% power"):
        mde(0.08, 20, power=0.90)


def test_spec_budget_refuses_sixth() -> None:
    spec_budget_guard(4)
    spec_budget_guard(SPEC_BUDGET - 1)
    with pytest.raises(SpecBudgetError, match="6"):
        spec_budget_guard(5)


def test_date_shift_catches_planted_look_ahead() -> None:
    panel = pl.DataFrame(
        {
            "symbol": ["X", "X", "X", "Y", "Y", "Y"],
            "session_date": [
                date(2020, 1, 1),
                date(2020, 1, 2),
                date(2020, 1, 3),
                date(2020, 1, 1),
                date(2020, 1, 2),
                date(2020, 1, 3),
            ],
            "unadj_close": [10.0, 11.0, 12.0, 20.0, 22.0, 24.0],
        }
    )

    def lag(frame: pl.DataFrame) -> pl.Series:
        return (
            frame.sort(["symbol", "session_date"])
            .with_columns(pl.col("unadj_close").shift(1).over("symbol").alias("feat"))
            .get_column("feat")
        )

    date_shift_test(panel, lag)

    future = {
        (r["session_date"], r["symbol"]): nxt
        for r, nxt in zip(
            panel.iter_rows(named=True),
            panel.with_columns(pl.col("unadj_close").shift(-1).over("symbol")).get_column(
                "unadj_close"
            ),
            strict=True,
        )
    }

    def leak(frame: pl.DataFrame) -> pl.Series:
        values = [future[(r["session_date"], r["symbol"])] for r in frame.iter_rows(named=True)]
        return pl.Series("feat", values)

    with pytest.raises(AssertionError, match="unchanged"):
        date_shift_test(panel, leak)


def test_benchmark_ter_and_ltcg_on_realisation() -> None:
    capital = Decimal(1000000)
    dates = [date(2020, 1, 1), date(2021, 1, 1)]
    tri = [Decimal(100), Decimal(110)]
    nav = benchmark(capital, dates, tri)
    t_years = Decimal(366) / Decimal(365)
    net = Decimal("1.10") * (Decimal(1) - Decimal("0.0004")) ** t_years
    gain = capital * (net - Decimal(1))
    expected = capital + gain - gain * Decimal("0.13")
    assert nav == expected
    assert nav < capital * Decimal("1.10")


def test_load_all_preregistrations_and_sha() -> None:
    records = load_all_preregistrations(PREREG)
    books = {r.book: r for r in records}
    assert set(books) == {"L", "P", "B", "M", "R", "A"}
    assert books["L"].inference is False and books["L"].passes_h4 is True
    assert books["P"].inference is False and books["P"].passes_h4 is True
    assert books["B"].passes_h4 is False
    assert books["M"].passes_h4 is False
    assert books["R"].passes_h4 is False
    assert books["A"].passes_h4 is False
    assert books["A"].t_years == 0.09
    path = books["M"].path
    assert books["M"].sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    again = load_preregistration(path)
    assert again.sha256 == books["M"].sha256


def test_inference_prereg_rejects_wrong_mde(tmp_path: Path) -> None:
    text = (PREREG / "h0-prereg-book-m.md").read_text(encoding="utf-8")
    text = text.replace("mde_ann: 0.0501", "mde_ann: 0.01")
    fake = tmp_path / "h0-prereg-book-m.md"
    fake.write_text(text, encoding="utf-8")
    with pytest.raises(PreRegistrationError, match="mde_ann"):
        load_preregistration(fake)
