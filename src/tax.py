"""Indian tax for listed equity and F&O. Income-tax Act, 2025; Tax Year 1 Apr–31 Mar."""

from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum

PAISE = Decimal("0.01")
CESS = Decimal("0.04")
STCG_RATE = Decimal("0.20")
LTCG_RATE = Decimal("0.125")
LTCG_EXEMPTION = Decimal(125000)
SURCHARGE_CG_CAP = Decimal("0.15")
AUDIT_ONE_CRORE = Decimal(10000000)
AUDIT_TEN_CRORE = Decimal(100000000)
SPECULATIVE_CARRY_YEARS = 4
NON_SPECULATIVE_CARRY_YEARS = 8

# s.202 new-regime default slabs, Tax Year 2026-27.
_SLABS: tuple[tuple[Decimal, Decimal], ...] = (
    (Decimal(400000), Decimal(0)),
    (Decimal(800000), Decimal("0.05")),
    (Decimal(1200000), Decimal("0.10")),
    (Decimal(1600000), Decimal("0.15")),
    (Decimal(2000000), Decimal("0.20")),
    (Decimal(2400000), Decimal("0.25")),
    (Decimal("Infinity"), Decimal("0.30")),
)


class BusinessKind(StrEnum):
    SPECULATIVE = "speculative"
    NON_SPECULATIVE = "non_speculative"


def _money(value: Decimal) -> Decimal:
    return value.quantize(PAISE, rounding=ROUND_HALF_UP)


def add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    day_num = min(day.day, monthrange(year, month)[1])
    return date(year, month, day_num)


def long_term_holding(acquired: date, as_of: date) -> bool:
    """Listed equity / equity-oriented funds: held ≥ 12 months (s.198 vs s.196)."""
    return as_of >= add_months(acquired, 12)


def tax_year(day: date) -> str:
    start = day.year if day.month >= 4 else day.year - 1
    return f"{start}-{str(start + 1)[2:]}"


def tax_year_start(day: date) -> int:
    return day.year if day.month >= 4 else day.year - 1


def _with_cess(tax: Decimal, surcharge_rate: Decimal) -> Decimal:
    surcharge_rate = min(surcharge_rate, SURCHARGE_CG_CAP)
    return _money(tax * (Decimal(1) + surcharge_rate) * (Decimal(1) + CESS))


def stcg(gain: Decimal, surcharge_rate: Decimal = Decimal(0)) -> Decimal:
    """s.196: 20% from the first rupee, plus 4% cess. Surcharge on CG capped at 15%."""
    if gain <= 0:
        return Decimal("0.00")
    return _with_cess(gain * STCG_RATE, surcharge_rate)


def ltcg(gain: Decimal, exemption_used: Decimal, surcharge_rate: Decimal = Decimal(0)) -> Decimal:
    """s.198: 12.5% on the excess over ₹1,25,000 aggregate per tax year, plus cess."""
    remaining = LTCG_EXEMPTION - exemption_used
    if remaining < 0:
        remaining = Decimal(0)
    taxable = gain - remaining
    if taxable <= 0:
        return Decimal("0.00")
    return _with_cess(taxable * LTCG_RATE, surcharge_rate)


def slab_tax(income: Decimal) -> Decimal:
    if income <= 0:
        return Decimal("0.00")
    tax = Decimal(0)
    lower = Decimal(0)
    for upper, rate in _SLABS:
        band = min(income, upper) - lower
        if band > 0:
            tax += band * rate
        if income <= upper:
            break
        lower = upper
    return _money(tax)


def business_surcharge_rate(total_income: Decimal) -> Decimal:
    if total_income > Decimal(20000000):
        return Decimal("0.25")
    if total_income > Decimal(10000000):
        return Decimal("0.15")
    if total_income > Decimal(5000000):
        return Decimal("0.10")
    return Decimal(0)


@dataclass
class CarryItem:
    origin_year_start: int
    amount: Decimal
    years_allowed: int

    def usable_in(self, year_start: int) -> bool:
        return self.origin_year_start < year_start <= self.origin_year_start + self.years_allowed


@dataclass
class CarryLedgers:
    speculative: list[CarryItem] = field(default_factory=list)
    non_speculative: list[CarryItem] = field(default_factory=list)

    def remaining(self, kind: BusinessKind, year_start: int) -> Decimal:
        items = self.speculative if kind is BusinessKind.SPECULATIVE else self.non_speculative
        return sum((i.amount for i in items if i.usable_in(year_start)), Decimal(0))


@dataclass(frozen=True)
class BusinessResult:
    tax: Decimal
    taxable_income: Decimal
    carried: Decimal
    years_allowed: int
    ledgers: CarryLedgers


def _apply_carry(ledgers: CarryLedgers, kind: BusinessKind, year_start: int, profit: Decimal) -> Decimal:
    items = ledgers.speculative if kind is BusinessKind.SPECULATIVE else ledgers.non_speculative
    remaining_profit = profit
    for item in items:
        if remaining_profit <= 0:
            break
        if not item.usable_in(year_start):
            continue
        take = min(item.amount, remaining_profit)
        item.amount -= take
        remaining_profit -= take
    return remaining_profit


def business_income(
    pnl: Decimal,
    kind: BusinessKind,
    year_start: int,
    ledgers: CarryLedgers | None = None,
    other_income: Decimal = Decimal(0),
) -> BusinessResult:
    """Slab + surcharge + 4% cess. Speculative losses offset only speculative income."""
    books = ledgers if ledgers is not None else CarryLedgers()
    years = SPECULATIVE_CARRY_YEARS if kind is BusinessKind.SPECULATIVE else NON_SPECULATIVE_CARRY_YEARS
    if pnl < 0:
        loss = -pnl
        item = CarryItem(origin_year_start=year_start, amount=loss, years_allowed=years)
        if kind is BusinessKind.SPECULATIVE:
            books.speculative.append(item)
        else:
            books.non_speculative.append(item)
        return BusinessResult(
            tax=Decimal("0.00"),
            taxable_income=Decimal("0.00"),
            carried=loss,
            years_allowed=years,
            ledgers=books,
        )
    taxable = _apply_carry(books, kind, year_start, pnl)
    total = taxable + other_income
    base = slab_tax(total) - slab_tax(other_income)
    surcharge = business_surcharge_rate(total)
    tax = _money(base * (Decimal(1) + surcharge) * (Decimal(1) + CESS))
    return BusinessResult(
        tax=tax,
        taxable_income=taxable,
        carried=Decimal("0.00"),
        years_allowed=years,
        ledgers=books,
    )


@dataclass(frozen=True)
class AuditTrade:
    pnl: Decimal
    option_premium_sold: Decimal = Decimal(0)
    premium_already_in_pnl: bool = False


@dataclass(frozen=True)
class AuditTurnover:
    turnover: Decimal
    crosses_one_crore: bool
    crosses_ten_crore: bool


def audit_turnover(trades: list[AuditTrade]) -> AuditTurnover:
    """Absolute-sum P&L; option premium sold added unless already inside the broker P&L (W10)."""
    turnover = Decimal(0)
    for trade in trades:
        turnover += abs(trade.pnl)
        if trade.option_premium_sold and not trade.premium_already_in_pnl:
            turnover += trade.option_premium_sold
    turnover = _money(turnover)
    return AuditTurnover(
        turnover=turnover,
        crosses_one_crore=turnover > AUDIT_ONE_CRORE,
        crosses_ten_crore=turnover > AUDIT_TEN_CRORE,
    )
