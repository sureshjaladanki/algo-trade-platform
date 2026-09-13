"""Book W — domicile, withholding, accumulation, and estate arithmetic.

Deterministic. The recurring wrapper saving is the core-benchmark construction,
not excess. W0 locks published-document inputs; it does not certify broker access.
"""

from __future__ import annotations

from dataclasses import dataclass

# N9 Book W minimum (alien plan). Accounting identity, not a statistical peek.
WRAPPER_SAVING_HURDLE_BPS = 15.0
GROSS_EQUITY_RETURN = 0.07
US_WEIGHT = 0.70
EXUS_WEIGHT = 0.30
NRA_FDAP_RATE = 0.25
IRISH_US_TREATY_WHT = 0.15
INDIA_SLAB_RATE = 0.312
INDIA_LTCG_RATE = 0.13
NRA_ESTATE_UNIFIED_CREDIT_USD = 13_000.0
HOLD_YEARS = 20.0

# Published TERs / OCFs (prospectus / factsheet, not marketing copy).
VTI_TER = 0.0003  # Vanguard summary prospectus, Total Annual Fund Operating Expenses
VXUS_TER = 0.0005  # Vanguard summary prospectus dated 2026-02-27
CSPX_TER = 0.0007  # iShares Core S&P 500 UCITS ETF USD Acc
XUSE_TER = 0.0015  # iShares MSCI World ex-USA UCITS ETF USD Acc
VWRA_TER = 0.0014  # Vanguard FTSE All-World UCITS ETF USD Acc, OCF 31 Jul 2026

# Dividend yields used to convert a withholding *rate* into bps of NAV.
VTI_SEC_YIELD = 0.0102  # Vanguard, SEC yield as of 2026-06-30
VXUS_TTM_YIELD = 0.0276  # published TTM yield as of 2026-09-09
VWRA_US_WEIGHT = 0.616  # Vanguard factsheet 31 Jul 2026, United States allocation

# Blueprint §0.2 working yields (sensitivity). Not a substitute for published yields.
WORKING_US_YIELD = 0.013
WORKING_EXUS_YIELD = 0.029

# LSE/UCITS dealing (blueprint rung 3, working until N0 fills). No UK SDRT on
# Irish-incorporated shares. USD line: zero FX.
LSE_ROUND_TRIP_BPS_SMALL = 11.5  # midpoint of 8–15 at small size
LSE_ROUND_TRIP_BPS_LARGE = 6.0  # midpoint of 4–8 at $100k+ clips

# IRC 2001(c) graduated schedule. NRA credit is $13,000 (tax on $60,000).
_ESTATE_BRACKETS: tuple[tuple[float, float], ...] = (
    (10_000.0, 0.18),
    (20_000.0, 0.20),
    (40_000.0, 0.22),
    (60_000.0, 0.24),
    (80_000.0, 0.26),
    (100_000.0, 0.28),
    (150_000.0, 0.30),
    (250_000.0, 0.32),
    (500_000.0, 0.34),
    (750_000.0, 0.37),
    (1_000_000.0, 0.39),
)


def _tax_on_taxable_estate(taxable: float) -> float:
    tax = 0.0
    lower = 0.0
    for upper, rate in _ESTATE_BRACKETS:
        if taxable <= lower:
            break
        band = min(taxable, upper) - lower
        tax += band * rate
        lower = upper
    if taxable > 1_000_000.0:
        tax += (taxable - 1_000_000.0) * 0.40
    return tax


def us_nra_estate_tax(situs_market_value: float) -> float:
    """US estate tax on US-situs property for an NRA, working 2026 schedule."""
    tentative = _tax_on_taxable_estate(situs_market_value)
    return max(tentative - NRA_ESTATE_UNIFIED_CREDIT_USD, 0.0)


def bps(fraction: float) -> float:
    return fraction * 10_000.0


@dataclass(frozen=True)
class LineFacts:
    name: str
    ticker: str
    isin: str
    domicile: str
    accumulation: bool
    replication: str
    ter: float
    situs_us: bool
    investor_wht_rate: float
    fund_us_wht_rate: float
    withheld_of_gross_income: float


VTI = LineFacts(
    name="Vanguard Total Stock Market ETF",
    ticker="VTI",
    isin="US9229087690",
    domicile="US",
    accumulation=False,
    replication="physical",
    ter=VTI_TER,
    situs_us=True,
    investor_wht_rate=NRA_FDAP_RATE,
    fund_us_wht_rate=0.0,
    withheld_of_gross_income=NRA_FDAP_RATE,
)
VXUS = LineFacts(
    name="Vanguard Total International Stock ETF",
    ticker="VXUS",
    isin="US9219097683",
    domicile="US",
    accumulation=False,
    replication="physical",
    ter=VXUS_TER,
    situs_us=True,
    investor_wht_rate=NRA_FDAP_RATE,
    fund_us_wht_rate=0.0,
    withheld_of_gross_income=NRA_FDAP_RATE,
)
CSPX = LineFacts(
    name="iShares Core S&P 500 UCITS ETF USD Acc",
    ticker="CSPX",
    isin="IE00B5BMR087",
    domicile="IE",
    accumulation=True,
    replication="physical",
    ter=CSPX_TER,
    situs_us=False,
    investor_wht_rate=0.0,
    fund_us_wht_rate=IRISH_US_TREATY_WHT,
    withheld_of_gross_income=IRISH_US_TREATY_WHT,
)
XUSE = LineFacts(
    name="iShares MSCI World ex-USA UCITS ETF USD Acc",
    ticker="XUSE",
    isin="IE000R4ZNTN3",
    domicile="IE",
    accumulation=True,
    replication="physical",
    ter=XUSE_TER,
    situs_us=False,
    investor_wht_rate=0.0,
    fund_us_wht_rate=0.0,
    withheld_of_gross_income=0.0,
)
VWRA = LineFacts(
    name="Vanguard FTSE All-World UCITS ETF USD Acc",
    ticker="VWRA",
    isin="IE00BK5BQT80",
    domicile="IE",
    accumulation=True,
    replication="physical",
    ter=VWRA_TER,
    situs_us=False,
    investor_wht_rate=0.0,
    fund_us_wht_rate=IRISH_US_TREATY_WHT,
    withheld_of_gross_income=IRISH_US_TREATY_WHT * VWRA_US_WEIGHT,
)


@dataclass(frozen=True)
class WrapperCosts:
    label: str
    blended_ter_bps: float
    us_leg_wht_bps: float
    exus_investor_wht_bps: float
    total_bps: float
    rnor_after_tax: float
    ror_after_tax: float
    situs_on_core: bool

    @property
    def ror_governs_after_tax(self) -> float:
        return self.ror_after_tax


@dataclass(frozen=True)
class EstateRow:
    situs_usd: float
    tax_usd: float
    pct_of_situs: float


@dataclass(frozen=True)
class RorCliffRow:
    wrapper: str
    annual_india_dividend_tax_bps: float
    form_67: bool
    dividend_as_ltcg_bps: float


def _blended_ter(us_ter: float, exus_ter: float) -> float:
    return US_WEIGHT * us_ter + EXUS_WEIGHT * exus_ter


def _extra_india_dividend_tax(*, us_yield: float, exus_yield: float) -> float:
    gross_div = US_WEIGHT * us_yield + EXUS_WEIGHT * exus_yield
    return (INDIA_SLAB_RATE - NRA_FDAP_RATE) * gross_div


def us_listed_costs(*, us_yield: float, exus_yield: float) -> WrapperCosts:
    ter = _blended_ter(VTI.ter, VXUS.ter)
    us_wht = NRA_FDAP_RATE * us_yield * US_WEIGHT
    exus_wht = NRA_FDAP_RATE * exus_yield * EXUS_WEIGHT
    total = ter + us_wht + exus_wht
    rnor = GROSS_EQUITY_RETURN - total
    ror = rnor - _extra_india_dividend_tax(us_yield=us_yield, exus_yield=exus_yield)
    return WrapperCosts(
        label="US-listed VTI+VXUS",
        blended_ter_bps=bps(ter),
        us_leg_wht_bps=bps(us_wht),
        exus_investor_wht_bps=bps(exus_wht),
        total_bps=bps(total),
        rnor_after_tax=rnor,
        ror_after_tax=ror,
        situs_on_core=True,
    )


def irish_pair_costs(*, us_yield: float) -> WrapperCosts:
    ter = _blended_ter(CSPX.ter, XUSE.ter)
    us_wht = IRISH_US_TREATY_WHT * us_yield * US_WEIGHT
    total = ter + us_wht
    after_tax = GROSS_EQUITY_RETURN - total
    return WrapperCosts(
        label="Irish physical acc CSPX+XUSE",
        blended_ter_bps=bps(ter),
        us_leg_wht_bps=bps(us_wht),
        exus_investor_wht_bps=0.0,
        total_bps=bps(total),
        rnor_after_tax=after_tax,
        ror_after_tax=after_tax,
        situs_on_core=False,
    )


def vwra_costs(*, us_yield: float) -> WrapperCosts:
    us_wht = IRISH_US_TREATY_WHT * us_yield * VWRA_US_WEIGHT
    total = VWRA.ter + us_wht
    after_tax = GROSS_EQUITY_RETURN - total
    return WrapperCosts(
        label="Irish physical acc VWRA",
        blended_ter_bps=bps(VWRA.ter),
        us_leg_wht_bps=bps(us_wht),
        exus_investor_wht_bps=0.0,
        total_bps=bps(total),
        rnor_after_tax=after_tax,
        ror_after_tax=after_tax,
        situs_on_core=False,
    )


def recurring_saving_bps(naive: WrapperCosts, candidate: WrapperCosts) -> float:
    return naive.total_bps - candidate.total_bps


def ror_annual_india_dividend_tax_bps(
    *,
    us_yield: float,
    exus_yield: float,
    accumulating: bool,
) -> float:
    if accumulating:
        return 0.0
    return bps(_extra_india_dividend_tax(us_yield=us_yield, exus_yield=exus_yield))


def dividend_as_ltcg_bps(*, us_yield: float, exus_yield: float) -> float:
    """Accrual-equivalent Indian tax if the dividend leg is realised as 13.0% CG."""
    gross_div = US_WEIGHT * us_yield + EXUS_WEIGHT * exus_yield
    return bps(INDIA_LTCG_RATE * gross_div)


def lse_dealing_amortised_bps(*, clip_usd: float) -> float:
    round_trip = LSE_ROUND_TRIP_BPS_LARGE if clip_usd >= 100_000.0 else LSE_ROUND_TRIP_BPS_SMALL
    return round_trip / HOLD_YEARS


def estate_table() -> tuple[EstateRow, ...]:
    values = (60_000.0, 100_000.0, 200_000.0, 500_000.0, 1_000_000.0)
    rows = []
    for situs in values:
        tax = us_nra_estate_tax(situs)
        rows.append(EstateRow(situs_usd=situs, tax_usd=tax, pct_of_situs=tax / situs))
    return tuple(rows)


def ror_cliff_table(*, us_yield: float, exus_yield: float) -> tuple[RorCliffRow, ...]:
    ltcg = dividend_as_ltcg_bps(us_yield=us_yield, exus_yield=exus_yield)
    distributing = ror_annual_india_dividend_tax_bps(
        us_yield=us_yield, exus_yield=exus_yield, accumulating=False
    )
    accumulating = ror_annual_india_dividend_tax_bps(
        us_yield=us_yield, exus_yield=exus_yield, accumulating=True
    )
    return (
        RorCliffRow(
            wrapper="US-listed distributing (VTI+VXUS)",
            annual_india_dividend_tax_bps=distributing,
            form_67=True,
            dividend_as_ltcg_bps=0.0,
        ),
        RorCliffRow(
            wrapper="Irish accumulating (CSPX+XUSE or VWRA)",
            annual_india_dividend_tax_bps=accumulating,
            form_67=False,
            dividend_as_ltcg_bps=ltcg,
        ),
    )


def measured_pair() -> tuple[WrapperCosts, WrapperCosts, float]:
    naive = us_listed_costs(us_yield=VTI_SEC_YIELD, exus_yield=VXUS_TTM_YIELD)
    irish = irish_pair_costs(us_yield=VTI_SEC_YIELD)
    return naive, irish, recurring_saving_bps(naive, irish)


def zero_situs_path_documented() -> bool:
    return not CSPX.situs_us and not XUSE.situs_us and not VWRA.situs_us


def w0_passes() -> bool:
    _naive, irish, saving = measured_pair()
    return saving >= WRAPPER_SAVING_HURDLE_BPS and not irish.situs_on_core and zero_situs_path_documented()
