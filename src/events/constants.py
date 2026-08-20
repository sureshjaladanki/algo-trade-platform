"""Book F / G cost and tax constants. Locked before any peek (execution plan P0)."""

import datetime as dt

BPS = 10_000.0

# Cash delivery, working round trip (blueprint §0.2).
DELIVERY_ROUND_TRIP_BPS = 45
DELIVERY_ROUND_TRIP = DELIVERY_ROUND_TRIP_BPS / BPS

# Realized-gain tax on a book that exits inside twelve months.
STCG_RATE = 0.208  # 20.8%  (§111A + cess)

# Passive core: equity held > 12 months. Applied on exit, not annually.
LTCG_RATE = 0.125  # 12.5%

# Index futures — recorded for reference. Not a live instrument on this desk.
INDEX_FUTURES_ROUND_TRIP_LOW_BPS = 10
INDEX_FUTURES_ROUND_TRIP_HIGH_BPS = 12
INDEX_FUTURES_ROUND_TRIP_LOW = INDEX_FUTURES_ROUND_TRIP_LOW_BPS / BPS
INDEX_FUTURES_ROUND_TRIP_HIGH = INDEX_FUTURES_ROUND_TRIP_HIGH_BPS / BPS

# Research OS (inherited-learnings). Locked before F1.
DISASTER_CLIP_BPS = 500
N_BOOT = 500
BOOT_SEED = 7
PURGE_CALENDAR_DAYS = 5
MIN_FOLD_EVENTS = 2

# F1 windows, session close to session close. T = first session the PIT
# difference appears. Announcement dates are not in the membership ledger.
F1_AUTHORITY_SESSIONS = 20  # T-20 close → T close
F1_REVERSAL_SESSIONS = 20  # T close → T+20 close (F1c)
F1_COMPANION_PRE_SESSIONS = 20  # T-40 close → T-20 close

# Blueprint Appendix A sketch. Charter MDE uses this; peek also prints sample σ.
PRIOR_EVENT_SIGMA_BPS = 600.0

# F3-RESIDUAL / C2 (charter locks). Not used by F1.
F3R_K = 3
F3R_CONTROL_RANK_LO = 21
F3R_CONTROL_RANK_HI = 50
F3R_PRIOR_SIGMA_BPS = 750.0
F3R_GO_BPS = 450.0
F3R_STOP_BPS = 300.0
F3R_MIN_COVERAGE = 2.0 / 3.0
F3R_START_YEAR = 2015
F3R_END_YEAR = 2025
F3R_ERA_SPLIT_YEAR = 2020

# G1–G3 earnings drift. Locks written into the G charters before the peek.
G1_AUTHORITY_SESSIONS = 3
G1_NEAR_SESSIONS = 1
G1_FAR_SESSIONS = 5
G1_ERA_SPLIT_YEAR = 2020
# Official NSE equity close. Filings at or after this stamp are not in that close.
NSE_EQUITY_CLOSE = dt.time(15, 30)
G2_ACTIVE_WEIGHT = 0.25
G3_GAP_PERCENTILE = 50.0

FAMILY_NIFTY_50 = "nifty_50"

# NSE Indices Nifty-50 inclusion: 6-month avg FF mcap vs smallest incumbent.
INCLUSION_FF_BUFFER = 1.5
IMPACT_COST_MAX_PCT = 0.50
MCWB_MIN_MONTHS = 5
