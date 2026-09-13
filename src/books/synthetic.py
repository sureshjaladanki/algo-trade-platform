"""W2 — synthetic versus physical Irish S&P 500 accumulating UCITS.

Tracking difference is locked from published NAV factsheets as of 31 Jul 2026,
over five years. Counterparty and 871(m) facts are from the prospectus / UCITS
Directive, not from an advisor opinion.
"""

from __future__ import annotations

# N9 W2 gates (alien plan).
SYNTHETIC_ADVANTAGE_HURDLE_BPS = 10.0
COUNTERPARTY_CAP_NAV = 0.10
SYNTHETIC_US_LEG_CAP = 0.50

# Invesco S&P 500 UCITS ETF Acc (SPXS), factsheet 31 Jul 2026.
# Cumulative NAV, 5 years, USD, net of ongoing charges.
SPXS_5Y_CUMULATIVE = 0.8230
SPXS_OCF = 0.0005
SPXS_SWAP_FEE = 0.0007
SPXS_REPLICATION = "synthetic"
SPXS_ISIN = "IE00B3YCGJ38"

# iShares Core S&P 500 UCITS ETF USD Acc (CSPX), factsheet 31 Jul 2026.
CSPX_5Y_ANNUALISED = 0.1255
CSPX_OCF = 0.0007
CSPX_REPLICATION = "physical"

# Same window, same printed net index (S&P 500 net TR / SPTR500N).
INDEX_NET_5Y_CUMULATIVE = 0.7920
INDEX_NET_5Y_ANNUALISED = 0.1237

# Yahoo ^SP500TR over 2021-07-30 → 2026-07-31. Gross, not the fund benchmark.
INDEX_GROSS_5Y_ANNUALISED = 0.128541

# justETF + Invesco product page: unfunded swap, multiple banks, daily exposure.
SPXS_COUNTERPARTIES: tuple[str, ...] = (
    "BofA Merrill Lynch",
    "Goldman Sachs",
    "J.P. Morgan",
    "Morgan Stanley",
    "Nomura",
)

# UCITS Directive 2009/65/EC Art. 52: 10% of assets when the OTC counterparty
# is a qualifying credit institution. Invesco supplement: collateral so that
# exposure is reduced to the Central Bank requirement; Invesco further limits
# it internally. Latest factsheet does not print a live % of NAV per name.
UCITS_OTC_COUNTERPARTY_CAP = 0.10
COUNTERPARTY_EXPOSURE_WITHIN_CAP = True

# Treas. Reg. §1.871-15: a qualified index (S&P 500) keeps the swap outside
# 871(m) (working). If the exception is withdrawn, swap payments that replace
# US-source dividends can become equivalent-dividend FDAP.
QUALIFIED_INDEX_EXCEPTION = "IRC 871(m) / Treas. Reg. 1.871-15, S&P 500 as qualified index"
QUALIFIED_INDEX_WITHDRAWAL = (
    "If the qualified-index exception is withdrawn, the swap's dividend-equivalent "
    "leg can become 871(m) FDAP and the 15% fund-level recovery disappears."
)


def annualise_cumulative(cumulative: float, *, years: float = 5.0) -> float:
    return (1.0 + cumulative) ** (1.0 / years) - 1.0


def bps(fraction: float) -> float:
    return fraction * 10_000.0


def spxs_5y_annualised() -> float:
    return annualise_cumulative(SPXS_5Y_CUMULATIVE)


def advantage_vs_physical_bps() -> float:
    return bps(spxs_5y_annualised() - CSPX_5Y_ANNUALISED)


def tracking_vs_net_index_bps(annualised: float) -> float:
    return bps(annualised - INDEX_NET_5Y_ANNUALISED)


def tracking_vs_gross_index_bps(annualised: float) -> float:
    return bps(annualised - INDEX_GROSS_5Y_ANNUALISED)


def w2_passes() -> bool:
    return (
        advantage_vs_physical_bps() >= SYNTHETIC_ADVANTAGE_HURDLE_BPS
        and COUNTERPARTY_EXPOSURE_WITHIN_CAP
        and UCITS_OTC_COUNTERPARTY_CAP <= COUNTERPARTY_CAP_NAV
    )


def synthetic_us_leg_weight() -> float:
    if not w2_passes():
        return 0.0
    return SYNTHETIC_US_LEG_CAP
