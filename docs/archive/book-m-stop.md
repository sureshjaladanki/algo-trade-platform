# STOP — Book M (self-run momentum)

Date: 2026-09-05
Closed at: P1 / M1
Author: agent

## What was claimed

A 12-month-formation, 12-month-hold, long-only momentum sleeve on Nifty 200, rebalanced annually,
clears H2 net of delivery friction and 13.0% LTCG. Pre-registered E_net **2.0%/yr**, σ **8%**, T
**20 yr** (`docs/next/h0-prereg-book-m.md`).

## What was measured

**Nothing was measured; the book never opened.** Specs used 0 of 5.

MDE_ann = 2.80 × 8% / √20 = **5.01%/yr**. ½ E_net = **1.0%**. **Fails H4 by 5.0×.**

The gross effect required to clear H4 at σ = 6% and T = 15 is **g ≥ 12.1%/yr** (blueprint §5.2) —
not a credible claim for a publicly documented Nifty 200 anomaly.

## Why it closed

**P1 did not return outcome 2** (self-run wins by > 100 bps/yr). P1 stopped because a self-run
replication cannot be reconciled to published factor TRI within 50 bps/yr on the U0 universe
([p1-stop.md](p1-stop.md)). Default is the packaged vehicle.

Separately, **H4 already failed at H0**. Even an outcome-2 opening would have been expected to STOP
on measurability.

## What would re-open it

P1 outcome 2 on a replication that tracks published TRI within 50 bps/yr before costs, **and** an
H4 waiver that does not currently exist (σ and T such that 2.80 σ/√T ≤ 1.0%). Not a fifth
specification on the same unmeasurable sleeve.

## What was deleted

No `src/books/momentum.py`. None will be added while this memo stands.
