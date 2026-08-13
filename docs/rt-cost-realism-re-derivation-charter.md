# RT Cost Realism Re-Derivation — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Single-variable re-derivation of round-trip friction `c`; TP/SL floors as pure `k × c`; Horizon A+B re-measure under locked v2 defaults  
**Status:** **OPEN** — Step 0 required before any Fold A+B peek  
**Authority:** [cascade-cost-horizon-physics-charter.md](cascade-cost-horizon-physics-charter.md) (dual-judge ACCEPT WITH REVISIONS)  
**Date:** 2026-08-13  
**Depends on:** [cascade-cost-horizon-physics-charter.md](cascade-cost-horizon-physics-charter.md), [horizon-tier2-v2-verdict.md](horizon-tier2-v2-verdict.md) (STOP-MEMO), [triple-barrier-verdict.md](triple-barrier-verdict.md)  
**Does not reopen:** Horizon v2 features / labels / H; Regime; Precision WS2; cost-multiple formula (`3 / 2.5 / 1.5`)

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | v2 fixed `c=30` bps and searched the model; `c` was never searched; 30 bps is a stress floor, not typical liquid Nifty-100 MIS |
| Single variable | Round-trip cost `c` (and floors that are identity functions of `c`) |
| Floors | **Always** Long TP = `3×c`, Short TP = `2.5×c`, SL = `1.5×c` — same multiples; never invent new `k` mid-peek |
| Primary H | **H=6 / 90m** (frozen) |
| Horizon model | Locked v2 carry-forward defaults (path-room demoted; Long chase demoted; Short `stock_r_15` keep; aux=0) |
| Peek budget | **Max 3** Fold A+B harness invocations — new ledger; cannot borrow from Horizon v2's exhausted 5 |
| Build posture | **Step 0 → dual-judge `c` sign-off → rebuild TB → peek** |

**One-line:** Re-anchor economic identity to a cited, dual-judge-signed `c`, then re-measure the frozen Horizon path-EV stack — do not reopen Horizon features.

---

## Carry-forward locks (from Horizon v2 STOP)

| Item | Lock |
|---|---|
| H=6 primary; H=4 diagnostic only | Unchanged |
| Path-room features | **Demoted** |
| Long `stock_r_15` | **Demoted**; Long `episode_balanced=True` |
| Short `stock_r_15` | **Keep** |
| Aux excess weight | **0** |
| Separate Long/Short; K=5/3 | Unchanged |
| Regime CLOSED; Precision WS2 blocked | Unchanged |
| Horizon-path PASS | Still **NO** under 30 bps — this charter may clear economics under new `c`, not claim PASS from cost alone without gates |

---

## Process locks

| Lock | Rule |
|---|---|
| Peek budget | **Max 3** Fold A+B harness invocations (baseline under signed `c` counts as 1) |
| Step 0 (no peek) | Publish cited statutory + broker decomposition table **before** any A+B |
| Step 1 (no peek) | If tiered `c`, pre-register ADV/liquidity split rule **before** peek 1 |
| Dual-judge gate | Sign-off on chosen working `c` **before** TB floors propagate in code |
| Single-variable | No Horizon feature / label / H / K / aux changes inside this charter |
| Multiplicity | Cost peeks **cannot** borrow from Horizon v2's exhausted 5 |
| Floors | Propagate **only** as `3×c / 2.5×c / 1.5×c` of signed `c` |
| Stop | Exhaust 3 peeks **or** dual-fold economics clear under signed `c` → stop-memo / merge |

### Pre-registered `c` ladder (do not grid)

| Point | Role | When usable |
|---|---|---|
| **30 bps** | Stress / archive (historical lock) | Always retained as diagnostic companion |
| **20 bps** | Working candidate (liquid-half consensus) | Default first signed working `c` after Step 0 |
| **15 bps** | Aggressive | Only if 20 clears dual-fold diagnostics; still needs dual-judge promote |
| **10 bps** | Gemini sensitivity | **Report-only** until Step 0 + dual-judge explicitly promote |

Do **not** soft-replace 30→10. Do **not** run a cost grid on A+B.

---

## Step 0 — Statutory decomposition (no peek)

**Gate:** Required before any Fold A+B. Dual-judge sign-off on working `c` after this table exists.

Publish a cited note (inline below or linked annex) covering:

1. **Broker plan assumption** (e.g. Zerodha-class discount: ₹20/order or 0.03% cap).  
2. **Statutory RT components** vs position notional (FY25–26 style schedules; cite source / effective date):
   - Brokerage
   - STT (intraday equity — sell leg)
   - Exchange txn charges + SEBI turnover + IPFT
   - GST on brokerage/fees
   - Stamp duty (buy leg, state schedule as assumed)
3. **Subtotal** statutory + brokerage (expected ~5–8 bps band from physics charter).  
4. **Slippage / impact band** — liquid front half vs thinner Nifty-100 tail (assumption, labeled as such).  
5. **Chosen working `c`** from the pre-registered ladder + one-sentence rationale.  
6. **Stress companion** — keep 30 bps as archive/diagnostic, not deleted.

### Step 0 template (fill before peek 1)

| Component | Approx RT (bps) | Source / note |
|---|---:|---|
| Brokerage | | |
| STT (intraday sell) | | |
| NSE txn + SEBI + IPFT | | |
| GST | | |
| Stamp duty | | |
| **Statutory + brokerage subtotal** | | |
| Slippage / impact (assumption) | | liquid / tail |
| **Chosen working `c`** | | ladder point + rationale |
| Archive stress `c` | **30** | historical lock |

**Forbidden at Step 0:** Running `eval_horizon` A+B; changing TB floors in code before dual-judge sign-off; picking `c` outside the ladder without a separate dual-judge amend.

---

## Step 1 — Optional liquidity tier (no peek)

Default posture: **single working `c`** for the whole Nifty-100 MIS universe.

If (and only if) Step 0 shows a wide liquid-vs-tail gap that a single number cannot represent:

| Rule | Lock |
|---|---|
| Split definition | Pre-register ADV / turnover / membership rule **before** peek 1 |
| Per-tier `c` | Each tier still maps floors via `3× / 2.5× / 1.5×` of that tier's `c` |
| Post-hoc | **Forbidden** — no tier boundaries drawn after seeing A+B |
| Peek accounting | Tiered eval still costs the same A+B peek when both folds run |

If no tier rule is pre-registered, do not introduce one mid-charter.

---

## Step 2 — Propagate `c` → floors (no peek until rebuild done)

After dual-judge sign-off on working `c = c*` (fraction, e.g. `0.0020`):

| Identity | Formula | Example at `c*=20` bps |
|---|---|---|
| Long TP floor | `3 × c*` | 60 bps |
| Short TP floor | `2.5 × c*` | 50 bps |
| SL floor (both) | `1.5 × c*` | 30 bps |
| Dead zone / net labels | `c*` | same |
| Vol multiples | **Frozen** (`2.5/1.0` Long; `2.0/0.9` Short on TOD-rv) | unchanged |

**Code touchpoints (expected):** `src/labels/triple_barrier.py` (`ROUND_TRIP_COST` and derived floors); any eval that hard-codes 30 bps commentary must read the constant. Rebuild TB labels / Horizon path-EV artifacts under new floors before peek 1.

**Amend note:** After sign-off, add a dated amend block to [triple-barrier-verdict.md](triple-barrier-verdict.md) — vertical H stays 6; **only** `c` and absolute floors change; multiples unchanged.

---

## Peek plan (max 3)

| Peek | Lever (single-variable) | Purpose |
|---|---|---|
| **1** | Baseline A+B under signed working `c*` + locked v2 Horizon defaults | Establish dual-fold economics / H5 / report TB+1 / H4 under new identity |
| **2** | Pre-registered only: next ladder step (**15** if 20 cleared) **or** pre-registered tier split | One cost move — not features |
| **3** | Last allowed cost move or confirmatory re-measure under locked `c` | Exhaust or stop-memo |

**Harness:** `python -m src.experiments.eval_horizon` (same Fold A/B calendars as Horizon v2; multiplicity accounted on **this** ledger).  
**Gates (unchanged roles):** H5 primary lift; H1/H2/H3 secondary; absolute Top-K TB+1 and H4 **report/diagnostic** — do not soft-promote ship language.  
**Not a peek:** Step 0 writeup; Step 1 tier registration; TB rebuild; train-only pipeline runs that do not gate Fold A+B holdout.

### Peek ledger

| Peek | Date | `c` (bps) | Floors L/S/SL | Dual-fold outcome | Decision |
|---|---|---|---|---|---|
| — | — | — | — | — | **0 / 3** spent |

---

## Success / stop criteria

| Outcome | Action |
|---|---|
| Dual-fold economics clear under signed `c*` (H5 primary; report H4 / TB+1 honestly) | Stop-memo + merge slice; still **no** cascade-ready / Horizon-path PASS claim from cost alone without meeting path gates |
| Peek 1 FAIL at 20; diagnostics show cost still dominant | Dual-judge may promote **15** for peek 2 — not silent 10 |
| 3/3 exhausted without clear economics | Cost-charter STOP-MEMO; do not invent multiples or reopen Horizon features inside this budget |
| 10 bps sensitivity wanted | Report-only appendix unless dual-judge promotes into the ladder |

---

## Forbidden moves

- Silent 30→10 (or any) cost swap without Step 0 + dual-judge sign-off  
- Lowering TP/SL without a revised `c`, or inventing new multiples mid-peek  
- Reopening Horizon v2 features / labels / H / exhausted v2 peek budget  
- Reopening Regime or Precision WS2  
- Reverting primary H to 60m to “fit” afternoon bars  
- Claiming cascade-ready / Horizon-path PASS / book PnL from cost change alone  
- Post-hoc liquidity-tier boundaries after seeing A+B  
- Cost grid search on A+B; borrowing peeks from Horizon v2's 5  
- Changing vol multiples (`2.5/1.0`, `2.0/0.9`) inside this charter  

---

## Build sequence

1. **Step 0** — Fill statutory + broker decomposition table; propose working `c` from ladder.  
2. **Dual-judge sign-off** on working `c*` (and tier rule if any).  
3. **Step 2** — Propagate `c*` → floors in code; rebuild TB / path-EV labels; amend triple-barrier verdict.  
4. **Peek 1** — Fold A+B baseline under locked Horizon v2 defaults + new `c*`.  
5. At most two further pre-registered cost levers (peek 2–3).  
6. Stop-memo / merge — update this charter status; do not reopen Horizon feature search from here.

---

## Related docs

| Doc | Role |
|---|---|
| [cascade-cost-horizon-physics-charter.md](cascade-cost-horizon-physics-charter.md) | Dual-judge authority — why cost, keep H=6, keep multiples |
| [horizon-tier2-v2-verdict.md](horizon-tier2-v2-verdict.md) | Path-EV STOP; carry-forward feature locks |
| [triple-barrier-verdict.md](triple-barrier-verdict.md) | Amend after `c*` sign-off — floors only |
| [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) | Upstream path density context |
| [cascade-strategy-overview.md](cascade-strategy-overview.md) | Cascade map — friction line updates after merge |
