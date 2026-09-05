# L0 — Runbook (manual fallback)

Date: 2026-09-05
Milestone: L0
Posture: [p0-posture.md](p0-posture.md)

No live capital. No paid broker API until this milestone exits (L7, L8). Placement is the
paper venue in `src.execute.PaperBroker`. The printed instruction list is the source of truth
(L12).

## Daily loop (IST)

| Time | Step | If it fails |
|---|---|---|
| **09:00** | Reconcile yesterday's fills to the broker ledger. Residual must be ≤ ₹1. | **Stop. Emit no instructions today.** Fix the break. |
| 09:00–09:05 | Pre-open phase 1: market or limit | — |
| 09:05–09:15 | Pre-open phase 2 (from **7 Sep 2026**): **limit only** | A market order is an exchange reject; `execute` refuses it first |
| 09:15 | Continuous; remainder of the list as limits | — |
| 15:20–15:25 | CAS-eligible names only: limit residual into the auction | Non-CAS names refused |
| **16:15** | Refresh panel (cache), `apply_realisation`, print tomorrow's list | Missed 16:15 is an L0 break |
| 16:30 | Template note on the run log (`ops.run_note`). No model in the book (L10). | — |

Auth every morning: static IP, OAuth, 2FA, **today's** session token, exchange algo ID. Any gap
refuses every order.

## Printed list

`logs/instructions-YYYY-MM-DD.txt`, one order per line:

```
# instruction list 2026-09-07
# place by hand if the API is down; one line per order
# SIDE SYMBOL QTY TYPE LIMIT ALGO PHASE
SELL N50 1 LIMIT 1000.00 NSEALGO1 continuous
```

Place each line on the broker ticket in that order. Do not type a market order in phase 2 or CAS.
Do not send a line with a blank algo ID. Cap at **8 orders in any clock second**.

Replay check: `parse_instruction_list` of the file must equal the automated list, and paper fills
must reconcil to ₹1 against the automated path.

## Three triggers for this fallback

1. **API down** — place the printed file by hand; still reconcil at 09:00 next session.
2. **Token failure** — do not send untagged or yesterday's-token orders. Renew, or fall back to hand.
3. **Reconciliation mismatch > ₹1** — no new instructions that day. Paper and live stay blocked
   until the rupee break is identified.

## H6

One machine, one broker, one ~16:15 run, ≤ 10 OPS (code cap 8), algo ID on every order. If the
loop needs a second machine, a second broker, or someone watching the screen between 09:15 and
15:15, stop and redesign — do not add infrastructure.

## What L0 has not yet done

Twenty **calendar** paper sessions with a live (or paper-account) broker ledger, a hand-placed
session at the terminal, and H1 on a real contract note. Unit tests cover the refusals, a printed
replay, and twenty in-process paper sessions. **L0 is not exited. Spend stays ₹0. Capital stays 0.**
