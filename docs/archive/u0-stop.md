# STOP — U0 universe breadth

Date: 2026-09-05
Closed at: U0
Author: agent

## What was claimed

Point-in-time membership for Nifty 50 / Next 50 / 100 / 200 / Midcap 150 / Smallcap 250 from NSE reconstitution press releases and factsheets, as of any Indian session.

## What was measured

Nifty 50 and Nifty Next 50 **current** constituent CSVs from `archives.nseindia.com` (2026-09-05). One reconstitution event encoded: STER out of Nifty 50 on 2013-08-27. No complete free bulk archive of Nifty 200 (or 500 / Midcap 150 / Smallcap 250) reconstitution history was assembled without a vendor or a third-party scrape.

## Why it closed

Not a full U0 stop — **breadth narrowing only**, as the plan requires. L8 forbids buying a PIT membership vendor at this stage.

## What would re-open it

A free NSE Indices dump of historical constituents for Nifty 200 (or a complete set of monthly “Market Capitalisation, Weightage, Beta” files loaded into `index_events.csv`) covering 2005–present.

## What was deleted

Nothing. `universe.py` still names the wider indices. `membership_as_of` for those names returns empty unless events/seeds are added. Books that need a PIT universe must use **Nifty 50 + Nifty Next 50** and re-derive capacity and σ at H0 on that breadth.
