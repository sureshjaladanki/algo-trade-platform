"""W2 — synthetic versus physical Irish S&P 500 accumulating UCITS.

Tracking difference is locked from published NAV factsheets as of 31 Jul 2026,
over five years. Counterparty and 871(m) facts are from the prospectus / UCITS
Directive, not from an advisor opinion.

GL4 extends this module to non-US underlyings under W2's unchanged gate.
IRC 871(m) is a US-leg (S&P 500) fact; it is not claimed for World ex-USA or EM.
"""

from __future__ import annotations

from datetime import date

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


# GL4 — Book S, non-US legs. Same window (31 Jul 2026), same W2 gates.
# IRC 871(m) qualified-index recovery does not exist for these underlyings.

FACTSHEET_ASOF = date(2026, 7, 31)

# Physical World ex-USA lock (W0 / wrapper): iShares XUSE. Launch 24 Jan 2025
# (BlackRock product page). Common history to 31 Jul 2026 is < 5 years.
XUSE_ISIN = "IE000R4ZNTN3"
XUSE_LAUNCH = date(2025, 1, 24)
XUSE_REPLICATION = "physical"
XUSE_OCF = 0.0015

# justETF MSCI World ex USA list as of 13 Sep 2026: eight UCITS, all physical
# (full replication or sampling). No swap-based line is listed.
EXUS_SYNTHETIC_LISTED = False
BOND_SYNTHETIC_USD_ACC_5Y_PAIR = False

# Invesco MSCI Emerging Markets UCITS ETF Acc (MXFS), factsheet 31 Jul 2026.
# Cumulative NAV, 5 years, USD, net of ongoing charges. Unfunded swap.
MXFS_5Y_CUMULATIVE = 0.4508
MXFS_OCF = 0.0009
MXFS_SWAP_FEE = 0.0
MXFS_REPLICATION = "synthetic"
MXFS_ISIN = "IE00B3DWVS88"

# iShares MSCI EM UCITS ETF USD Acc (IEMA), factsheet 31 Jul 2026.
IEMA_5Y_ANNUALISED = 0.0804
IEMA_OCF = 0.0018
IEMA_REPLICATION = "physical"
IEMA_ISIN = "IE00B4L5YC18"

# Same window. Invesco prints the net index cumulative; iShares prints 8.03%/yr.
EM_INDEX_NET_5Y_CUMULATIVE = 0.4711
EM_INDEX_NET_5Y_ANNUALISED = 0.0803

# MSCI EM Gross USD, 5y annualised to 31 Jul 2026. Yahoo has no usable 5y
# series (^652800-USD-GRTR is a stub). Free MSCI gross factsheet, same as-of.
EM_INDEX_GROSS_5Y_ANNUALISED = 0.0852

# justETF + Invesco product page: unfunded swap, multiple banks.
MXFS_COUNTERPARTIES: tuple[str, ...] = (
    "BofA Merrill Lynch",
    "Goldman Sachs",
    "J.P. Morgan",
    "Morgan Stanley",
    "Nomura",
)

# Invesco Markets plc annual report, 30 Nov 2025, Schedule of Investments for
# this sub-fund. Swap MTM as % of NAV (Art. 52 metric, not swap notional).
# Factsheet 31 Jul 2026 does not print a live % of NAV per name.
MXFS_HOLDINGS_ASOF = date(2025, 11, 30)
MXFS_MAX_COUNTERPARTY_MTM_NAV = 0.036  # J.P. Morgan Securities plc, 3.60%
MXFS_COUNTERPARTY_EXPOSURE_WITHIN_CAP = True


def exus_history_years(*, as_of: date = FACTSHEET_ASOF) -> float:
    return (as_of - XUSE_LAUNCH).days / 365.25


def mxfs_5y_annualised() -> float:
    return annualise_cumulative(MXFS_5Y_CUMULATIVE)


def em_advantage_vs_physical_bps() -> float:
    return bps(mxfs_5y_annualised() - IEMA_5Y_ANNUALISED)


def em_tracking_vs_net_index_bps(annualised: float) -> float:
    return bps(annualised - EM_INDEX_NET_5Y_ANNUALISED)


def em_tracking_vs_gross_index_bps(annualised: float) -> float:
    return bps(annualised - EM_INDEX_GROSS_5Y_ANNUALISED)


def gl4_exus_passes() -> bool:
    # No listed synthetic, and XUSE history is < 5 years, so there is no
    # advantage series that can meet SYNTHETIC_ADVANTAGE_HURDLE_BPS.
    return False


def gl4_em_passes() -> bool:
    return (
        em_advantage_vs_physical_bps() >= SYNTHETIC_ADVANTAGE_HURDLE_BPS
        and MXFS_COUNTERPARTY_EXPOSURE_WITHIN_CAP
        and MXFS_MAX_COUNTERPARTY_MTM_NAV <= COUNTERPARTY_CAP_NAV
        and UCITS_OTC_COUNTERPARTY_CAP <= COUNTERPARTY_CAP_NAV
    )


def gl4_bond_passes() -> bool:
    return BOND_SYNTHETIC_USD_ACC_5Y_PAIR


def gl4_passes() -> bool:
    return gl4_exus_passes() or gl4_em_passes() or gl4_bond_passes()


def synthetic_non_us_leg_weight() -> float:
    if not gl4_passes():
        return 0.0
    return SYNTHETIC_US_LEG_CAP

