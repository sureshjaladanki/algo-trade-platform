"""Book F / G cost and tax constants. Locked before any peek (execution plan P0)."""

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
