"""Pre-registration, MDE, spec budget, look-ahead test, and the H2/H3/H7 benchmark."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

import polars as pl

SPEC_BUDGET = 5
MDE_Z = 2.80  # z_{1-α/2} + z_{1-β} at α = 0.05 two-sided, 80% power
BENCHMARK_TER = Decimal("0.0004")
BENCHMARK_TAX = Decimal("0.13")
PREREG_DIR = Path(__file__).resolve().parents[1] / "docs" / "next"


class SpecBudgetError(Exception):
    """Sixth specification on a book — the book closes regardless of result."""


class PreRegistrationError(Exception):
    """Front matter missing, unreadable, or inconsistent with MDE / H4."""


@dataclass(frozen=True)
class PreRegistration:
    book: str
    hypothesis: str
    instrument: str
    horizon: str
    universe: str
    n: float | None
    sigma_ann: float | None
    t_years: float | None
    mde_ann: float | None
    e_net_hypothesised: float | None
    half_e_net: float | None
    passes_h4: bool
    spec_budget: int
    specs_used: int
    sha256: str
    inference: bool
    path: Path


def mde(sigma_ann: float, years: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """MDE_ann = 2.80 × σ_ann / √T. α and power document the 2.80 z-sum; they are not free parameters."""
    if alpha != 0.05 or power != 0.80:
        raise ValueError("mde is defined at α = 0.05 two-sided and 80% power")
    if years <= 0:
        raise ValueError("years must be positive")
    return MDE_Z * sigma_ann / math.sqrt(years)


def spec_budget_guard(specs_used: int, spec_budget: int = SPEC_BUDGET) -> None:
    """Refuse to run a specification once the five-spec budget is exhausted."""
    if specs_used >= spec_budget:
        raise SpecBudgetError(
            f"specification {specs_used + 1} refused; budget is {spec_budget}"
        )


def date_shift_test(panel: pl.DataFrame, feature_fn: Callable[[pl.DataFrame], pl.Series]) -> None:
    """Shift unadj_close by one session. A non-constant feature must move; leftover equals is lookahead."""
    shifted = panel.with_columns(pl.col("unadj_close").shift(1).over("symbol"))
    base = feature_fn(panel)
    moved = feature_fn(shifted)
    if base.drop_nulls().n_unique() <= 1:
        return
    if (base == moved).fill_null(True).all():
        raise AssertionError("feature unchanged after input shift")


def benchmark(capital: Decimal, dates: Sequence[date], tri: Sequence[Decimal]) -> Decimal:
    """Nifty 50 TRI net of 0.04% TER, taxed at 13.0% on realisation at the last date.

    Same capital and the same first-to-last cash-flow schedule as the sleeve under test.
    """
    if len(dates) != len(tri) or len(dates) < 2:
        raise ValueError("dates and tri must be aligned and length ≥ 2")
    t_years = Decimal((dates[-1] - dates[0]).days) / Decimal(365)
    gross = tri[-1] / tri[0]
    net = gross * (Decimal(1) - BENCHMARK_TER) ** t_years
    gain = capital * (net - Decimal(1))
    tax = max(gain, Decimal(0)) * BENCHMARK_TAX
    return capital + gain - tax


def _optional_float(raw: str) -> float | None:
    if raw in ("", "n/a", "none"):
        return None
    return float(raw)


def _parse_bool(raw: str) -> bool:
    if raw == "true":
        return True
    if raw == "false":
        return False
    raise PreRegistrationError(f"boolean field is not true/false: {raw}")


def parse_front_matter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise PreRegistrationError("missing YAML front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise PreRegistrationError("unclosed YAML front matter")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        key, sep, value = line.partition(":")
        if not sep:
            raise PreRegistrationError(f"front-matter line has no key: {line}")
        fields[key.strip()] = value.strip()
    return fields


def load_preregistration(path: Path) -> PreRegistration:
    text = path.read_text(encoding="utf-8")
    fields = parse_front_matter(text)
    inference = _parse_bool(fields["inference"])
    mde_ann = _optional_float(fields["mde_ann"])
    e_net = _optional_float(fields["e_net_hypothesised"])
    half = _optional_float(fields["half_e_net"])
    record = PreRegistration(
        book=fields["book"],
        hypothesis=fields["hypothesis"],
        instrument=fields["instrument"],
        horizon=fields["horizon"],
        universe=fields["universe"],
        n=_optional_float(fields["n"]),
        sigma_ann=_optional_float(fields["sigma_ann"]),
        t_years=_optional_float(fields["t_years"]),
        mde_ann=mde_ann,
        e_net_hypothesised=e_net,
        half_e_net=half,
        passes_h4=_parse_bool(fields["passes_h4"]),
        spec_budget=int(fields["spec_budget"]),
        specs_used=int(fields["specs_used"]),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        inference=inference,
        path=path,
    )
    validate_preregistration(record)
    return record


def validate_preregistration(record: PreRegistration) -> None:
    if record.spec_budget != SPEC_BUDGET:
        raise PreRegistrationError(f"{record.book}: spec_budget must be {SPEC_BUDGET}")
    if record.specs_used > record.spec_budget:
        raise PreRegistrationError(f"{record.book}: specs_used exceeds budget")
    if not record.inference:
        if record.mde_ann is not None:
            raise PreRegistrationError(f"{record.book}: non-inference book must not publish MDE")
        return
    if record.sigma_ann is None or record.t_years is None or record.mde_ann is None:
        raise PreRegistrationError(f"{record.book}: inference book needs sigma_ann, t_years, mde_ann")
    expected = mde(record.sigma_ann, record.t_years)
    if not math.isclose(record.mde_ann, expected, rel_tol=0.01, abs_tol=5e-5):
        raise PreRegistrationError(
            f"{record.book}: mde_ann {record.mde_ann} ≠ {expected}"
        )
    if record.e_net_hypothesised is None or record.half_e_net is None:
        raise PreRegistrationError(f"{record.book}: inference book needs E_net and ½ E_net")
    expected_half = 0.5 * record.e_net_hypothesised
    if not math.isclose(record.half_e_net, expected_half, rel_tol=1e-9, abs_tol=1e-12):
        raise PreRegistrationError(f"{record.book}: half_e_net ≠ ½ × E_net")
    expected_h4 = record.mde_ann <= record.half_e_net
    if record.passes_h4 != expected_h4:
        raise PreRegistrationError(
            f"{record.book}: passes_h4 {record.passes_h4} ≠ gate {expected_h4}"
        )


def load_all_preregistrations(directory: Path = PREREG_DIR) -> list[PreRegistration]:
    paths = sorted(directory.glob("h0-prereg-book-*.md"))
    if not paths:
        raise PreRegistrationError(f"no pre-registration files in {directory}")
    return [load_preregistration(path) for path in paths]
