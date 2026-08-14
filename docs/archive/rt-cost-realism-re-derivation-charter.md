# RT Cost Realism Re-Derivation — Nifty-100 MIS v1

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Single-variable re-derivation of round-trip friction `c`; TP/SL floors as pure `k × c`; Horizon A+B re-measure under locked v2 defaults  
**Status:** **STOP-MEMO** — peek 1 FAIL under `c*=20`; peeks 2–3 frozen; dual-judge **ACCEPT STOP WITH REVISIONS** — next charter **OPEN:** [horizon-path-density-charter.md](horizon-path-density-charter.md); see [stop-memo](rt-cost-realism-re-derivation-stop-memo.md)  
**Authority:** [cascade-cost-horizon-physics-charter.md](cascade-cost-horizon-physics-charter.md) (dual-judge ACCEPT WITH REVISIONS)  
**Judges (sign-off):** [Claude Sonnet](db57b1e3-8911-4fa9-8f60-e87583378b40), [Gemini Flash](148f6921-4a23-44a9-8b67-2fc8efc0ee10)  
**Date:** 2026-08-13  
**Stop-memo:** 2026-08-13  
**Depends on:** [cascade-cost-horizon-physics-charter.md](cascade-cost-horizon-physics-charter.md), [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md) (STOP-MEMO), [triple-barrier-verdict.md](../triple-barrier-verdict.md)  
**Does not reopen:** Horizon v2 features / labels / H; Regime; Precision WS2; cost-multiple formula (`3 / 2.5 / 1.5`); ladder 15/10

---

## Summary

| Decision | Locked choice |
|---|---|
| Why this charter | v2 fixed `c=30` bps and searched the model; `c` was never searched; 30 bps is a stress floor, not typical liquid Nifty-100 MIS |
| Single variable | Round-trip cost `c` (and floors that are identity functions of `c`) |
| Floors | **Always** Long TP = `3×c`, Short TP = `2.5×c`, SL = `1.5×c` — same multiples; never invent new `k` mid-peek |
| Primary H | **H=6 / 90m** (frozen) |
| Horizon model | Locked v2 carry-forward defaults (path-room demoted; Long chase demoted; Short `stock_r_15` keep; aux=0) |
| Peek budget | **1 / 3 spent; 2 / 3 frozen** — no peek at 15/10 |
| Working `c*` | **0.0020 (20 bps)** — signed friction identity **kept** |
| Floors @ `c*` | Long TP **60** / Short TP **50** / SL **30** bps |
| Economics clear? | **NO** — Short H5 dual FAIL; H4 neg |
| Build posture | **CHARTER STOPPED** → [stop-memo](rt-cost-realism-re-derivation-stop-memo.md) |

**One-line:** `c*=20` is a better friction identity than 30 — it does **not** clear Horizon economics; cost search stops here.

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

## Step 0 — Statutory decomposition (no peek) — **DONE** 2026-08-13

**Gate:** Required before any Fold A+B. Dual-judge sign-off on working `c` after this table exists.  
**Broker plan:** Zerodha-class discount equity intraday (MIS) — ₹20/executed order or 0.03% (whichever lower), NSE cash.  
**Reference ticket:** ₹2,00,000 notional per side (₹20 brokerage cap binds for tickets ≳ ₹66.7k).  
**Sources:** [Zerodha Charges](https://zerodha.com/charges/) (accessed 2026-08-13); NSE equity cash txn schedule as published on that page (0.00307%/side); SEBI ₹10/crore; IPFT ₹0.01/crore (equity); stamp 0.003% buy-side (Indian Stamp Act schedule as listed by broker).

### Worked RT vs position notional (₹2L/side)

| Component | Rate / rule | RT ₹ @ ₹2L | RT bps |
|---|---|---:|---:|
| Brokerage | min(0.03%, ₹20) × 2 sides | 40.00 | **2.0** |
| STT (intraday) | 0.025% sell only | 50.00 | **2.5** |
| NSE txn | 0.00307% × 2 sides | 12.28 | **0.61** |
| SEBI turnover | ₹10/crore × 2 | 0.40 | **0.02** |
| IPFT (NSE) | ₹0.01/crore × 2 | ~0.00 | **~0** |
| Stamp duty | 0.003% buy only | 6.00 | **0.30** |
| GST | 18% × (brokerage + NSE + SEBI) both sides | ~9.5 | **0.47** |
| **Statutory + brokerage subtotal** | | **~118** | **~5.9** |

At ₹5L/side the same schedule compresses toward **~4.5 bps** (brokerage dilutes under the ₹20 cap; STT stays 2.5 bps). Band vs physics charter: **~5–8 bps** — confirmed.

### Slippage / impact (assumption — not statutory)

| Sleeve | Assumed RT slippage | Implied total `c` (stat+broker + slip) |
|---|---:|---:|
| Liquid front half Nifty-100, modest size | **~8–12 bps** | **~14–18 bps** |
| Mid / mixed Nifty-100 | **~12–16 bps** | **~18–22 bps** |
| Thinner tail / worse SL fills | **~18–25 bps** | **~24–31 bps** |

### Step 0 lock table

| Component | Approx RT (bps) | Source / note |
|---|---:|---|
| Brokerage | **~0.8–2.0** | Zerodha ₹20/order; dilutes with ticket size |
| STT (intraday sell) | **2.5** | 0.025% sell only — dominant statutory line |
| NSE txn + SEBI + IPFT | **~0.6** | 0.00307%×2 + ₹10/cr + IPFT |
| GST | **~0.3–0.5** | 18% on brokerage + exchange + SEBI |
| Stamp duty | **0.3** | 0.003% buy |
| **Statutory + brokerage subtotal** | **~5–6** | ₹2L reference; ~4.5 at ₹5L |
| Slippage / impact | **~8–16** liquid/mid · **~18–25** tail | **engineering judgment, uncited** (≠ statutory evidence weight) |
| **Proposed working `c*`** | **20** | ladder default — covers liquid/mid total; not aspirational 10 |
| Archive stress `c` | **30** | historical lock / thin-tail stress companion |

**Rationale for `c* = 20`:** Statutory floor is ~5–6 bps; adding a mid-universe slippage pad (~12–14 bps) lands on the physics-charter liquid-half band (15–20) without jumping to Gemini’s 10. Keeps 30 as archive stress. Floors if signed: Long TP **60** / Short TP **50** / SL **30** bps (`3× / 2.5× / 1.5×`).

**10 bps:** Remains **report-only** sensitivity — statutory+tiny-slip only; not proposed for peek 1.

### Broker parity — Zerodha vs Groww vs Kotak Neo (2026-08-13)

Same ₹2L/side NSE MIS RT. Statutory schedule is exchange/government (identical across brokers); only the brokerage line differs.

| Line | Zerodha | Groww | Kotak Neo (Trade Free, post day-30) |
|---|---|---|---|
| Brokerage rule | min(0.03%, ₹20)/order | min(0.1%, ₹20)/order (min ₹5) | min(0.05%, ₹10)/order |
| Brokerage RT @ ₹2L | **2.0 bps** (₹40) | **2.0 bps** (₹40) | **1.0 bps** (₹20) |
| STT sell 0.025% | 2.5 | 2.5 | 2.5 |
| Stamp buy 0.003% | 0.3 | 0.3 | 0.3 |
| NSE txn (~0.003%/side ×2) | ~0.6 | ~0.6 | ~0.6 |
| SEBI ₹10/cr ×2 | ~0.02 | ~0.02 | ~0.02 |
| GST on (broker+exch+SEBI) | ~0.5 | ~0.5 | ~0.3 |
| **Stat + brokerage subtotal** | **~5.9 bps** | **~5.9 bps** | **~4.7 bps** |
| Sources | [zerodha.com/charges](https://zerodha.com/charges/) | [groww.in/pricing](https://groww.in/pricing) · [intraday help](https://groww.in/help/stocks,-f&o,-ipo-&-mtf/sx-pricing/what-are-intraday-charges) | [kotakneo Trade Free](https://www.kotakneo.com/pricing/trade-free-plan/) |

**Parity read:** At algo-relevant tickets (≥₹1–2L), discount-broker MIS land in a **~5–6 bps** statutory+brokerage band (Kotak ~1 bps cheaper on brokerage). Groww’s 0.1% vs Zerodha’s 0.03% does **not** matter once the ₹20 cap binds. Kotak’s steady-state ₹10 cap is the only material brokerage delta among the three.

**Does not change `c* = 20`:** Slippage/impact (~8–16 liquid/mid) still dominates; broker choice moves the floor by ≲1 bps. Optional note: Kotak lists **₹0 brokerage on API-routed** Trade Free orders — would pull statutory-only closer to ~4 bps; still does not justify promoting 10 into the working ladder without dual-judge action.

**Forbidden at Step 0 (still hold):** Running `eval_horizon` A+B; changing TB floors in code before dual-judge sign-off; picking `c` outside the ladder without a separate dual-judge amend.

---

## Step 1 — Liquidity tier (no peek) — **DONE: single `c`**

**Decision:** **No liquidity-tiered `c` this charter.** One working `c*` for the whole Nifty-100 MIS universe.

| Rule | Lock |
|---|---|
| Why not tier | Liquid-vs-tail gap is real in slippage, but Step 0’s **20** already sits at the liquid/mid consensus; tiering would add a second free parameter before the first cost peek |
| Split definition | **None pre-registered** — do not introduce ADV/turnover splits mid-charter |
| Stress companion | Keep evaluating narrative against archive **30** if thin-tail concern resurfaces after peek 1 |
| Post-hoc | **Forbidden** — no tier boundaries after seeing A+B |

If dual-judge insists on tiers before peek 1, they must supply a pre-registered ADV rule in the sign-off note; otherwise single-`c` stands.

---

## Dual-judge sign-off — **SIGNED** 2026-08-13

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Step 0 fidelity | 10/10 | 8/10 | **ACCEPT** — statutory hard; slippage = engineering judgment |
| Broker parity | 10/10 | 7/10 | **ACCEPT** — ~5–6 bps band across three brokers |
| `c*=20` vs ladder | 9.5/10 | 8/10 | **ACCEPT** — not aspirational 10 |
| Single-c vs tier | 9.5/10 | 7/10 | **ACCEPT** — no tier; tail risk audited via peek-1 diag |
| Unlock Step 2 | 10/10 | 7/10 | **ACCEPT WITH REVISIONS** (Claude process MUST-FIX below) |
| Overall | **ACCEPT** | **ACCEPT WITH REVISIONS** | **`c* = 20` SIGNED** |

| Item | Locked |
|---|---|
| Working `c*` | **0.0020 (20 bps)** |
| Floors | Long TP **60** / Short TP **50** / SL **30** bps |
| Tier | **None** |
| Archive stress | **30 bps** companion |
| 10 bps | Report-only (Gemini: keep off working ladder) |
| Tail honesty | `c*=20` sits **below** Step 0 tail band (24–31); peek-1 PASS ≠ tail-universe clear |

### Claude MUST-FIX (locked into peek 1 — process only)

1. **Same-invocation dual readout:** Working-20 gates + archive-30 companion H4/TB+1 from **one** Fold A+B harness run = **one peek**, not two.  
2. **Report-only ADV/liquidity tercile** breakdown of Top-K TB+1 and H4 inside peek 1 (no extra harness call; no tiered `c`).  
3. Slippage band labeled **engineering judgment, uncited** in stop-memo/verdict (done in Step 0 table).  
4. Any peek-1 PASS narrative must note 20 ≱ Step 0 tail band.

---

## Step 2 — Propagate `c` → floors — **DONE** 2026-08-13

Signed working `c* = 0.0020`:

| Identity | Formula | At `c*=20` bps |
|---|---|---|
| Long TP floor | `3 × c*` | **60 bps** |
| Short TP floor | `2.5 × c*` | **50 bps** |
| SL floor (both) | `1.5 × c*` | **30 bps** |
| Dead zone / net labels | `c*` | **20 bps** |
| Vol multiples | Frozen | unchanged |

**Code:** `src/labels/triple_barrier.py` — `ROUND_TRIP_COST = 0.0020`, `ARCHIVE_ROUND_TRIP_COST = 0.0030`, derived floors.  
**Amend:** [triple-barrier-verdict.md](../triple-barrier-verdict.md) v3 block.  
**Rebuild:** TB labels / Horizon path-EV artifacts must be rebuilt under new floors **before** peek 1 (not itself a peek).

---

## Peek plan (max 3)

| Peek | Lever (single-variable) | Purpose |
|---|---|---|
| **1** | Baseline A+B under `c*=20` + locked v2 Horizon defaults | Working-20 gates; **same invocation** archive-30 H4/TB+1 companion + ADV-tercile report-only |
| **2** | Pre-registered only: next ladder step (**15** if 20 cleared) **or** pre-registered tier split | One cost move — not features |
| **3** | Last allowed cost move or confirmatory re-measure under locked `c` | Exhaust or stop-memo |

**Harness:** `python -m src.experiments.eval_horizon` (same Fold A/B calendars as Horizon v2; multiplicity accounted on **this** ledger).  
**Gates (unchanged roles):** H5 primary lift; H1/H2/H3 secondary; absolute Top-K TB+1 and H4 **report/diagnostic** — do not soft-promote ship language.  
**Peek-1 extras (Claude MUST-FIX, not extra peeks):** archive-30 companion metrics + ADV/liquidity tercile Top-K TB+1 / H4 — same harness invocation.  
**Not a peek:** Step 0 writeup; Step 1 tier registration; TB rebuild; train-only pipeline runs that do not gate Fold A+B holdout.

### Peek ledger

| Peek | Date | `c` (bps) | Floors L/S/SL | Dual-fold outcome | Decision |
|---|---|---|---|---|---|
| **1** | 2026-08-13 | **20** | 60/50/30 | Long H5 **PASS**; Short H5 **FAIL**; H4 neg; abs TB+1 Long ~9–11% / Short ~13% | **1 / 3** → **STOP** (no peek 2/3) |

### Peek 1 results — baseline A+B under `c*=20` (2026-08-13)

**Harness:** `python -m src.experiments.eval_horizon` (locked v2 Horizon defaults; H4arch + ADVt same invocation).  
**Logs:** `logs/horizon_cost_c20_peek1_fold_a.txt` · `logs/horizon_cost_c20_peek1_fold_b.txt`  
**Regime runs:** Fold A `e9dbc994…` · Fold B `7fff95a9…`

| Gate | Long A | Long B | Short A | Short B | Dual-fold |
|---|---|---|---|---|---|
| H1 | 0.065 PASS | 0.052 PASS | 0.034 PASS | 0.039 PASS | OK |
| H2 | 0.0003 **FAIL** | 0.0006 PASS | 0.0007 PASS | 0.0004 PASS | Long FAIL · Short PASS |
| H3 | FAIL (CI inv.) | PASS soft (m12&lt;m3k) | PASS soft | PASS soft | Long soft |
| **H5** | 0.040 [0.024, 0.056] **PASS** | 0.026 [0.012, 0.042] **PASS** | 0.002 [−0.017, 0.022] **FAIL** | 0.014 [−0.002, 0.032] **FAIL** | **Long PASS · Short FAIL** |
| Top-K TB+1 | 10.9% | 8.9% | 12.8% | 13.0% | report |
| H4 (`c*=20`) | −17 bps | −14 bps | −13 bps | −16 bps | neg |
| H4arch (`c=30`) | −27 bps | −24 bps | −23 bps | −26 bps | neg (stress) |
| ADVt lo share | 36% | 30% | 33% | 33% | Top-K ~⅓ thin tercile |

**Verdict:** Lowering `c` to 20 **does not** clear dual-fold economics. Long keeps dual-fold H5 (and Fold B also clears H2); Short H5 **gate flipped** PASS→FAIL vs v2 peek-3 under 30 bps (re-labeled path-EV + new floors; CIs overlap — not a large demonstrated regression). Absolute Top-K TB+1 still ~9–13%. H4 remains negative at working 20; archive-30 companion is ~10 bps worse as expected. ADV tercile: Top-K puts **~30–36%** mass in the thin (lo) third — single-`c*=20` is not silently all-liquid.

**Peek ledger:** **1 / 3** spent → **STOP-MEMO**. Ladder forbids auto-promote to 15 after FAIL at 20. See [rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md).

**Honesty locks:** no cascade PASS language; 20 ≱ Step 0 tail band (24–31); slippage remains engineering judgment.

---

## Success / stop criteria

| Outcome | Action |
|---|---|
| Dual-fold economics clear under signed `c*` (H5 primary; report H4 / TB+1 honestly) | Stop-memo + merge slice; still **no** cascade-ready / Horizon-path PASS claim from cost alone without meeting path gates |
| Peek 1 FAIL at 20 | **STOP** — do **not** promote 15 (ladder rule wins); remaining peeks frozen |
| 3/3 exhausted without clear economics | Cost-charter STOP-MEMO; do not invent multiples or reopen Horizon features inside this budget |
| 10 bps sensitivity wanted | Report-only appendix unless dual-judge promotes into a **new** charter |

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

1. **Step 0** — Fill statutory + broker decomposition table; propose working `c` from ladder. → **DONE**  
2. **Dual-judge sign-off** on working `c*` (and tier rule if any). → **DONE** (`c*=20` SIGNED)  
3. **Step 2** — Propagate `c*` → floors in code; amend triple-barrier verdict. → **DONE**  
4. **Peek 1** — Fold A+B baseline under locked Horizon v2 defaults + `c*=20` (+ archive-30 / ADV-tercile same invocation). → **DONE** (Short H5 FAIL; H4 neg)  
5. Peeks 2–3 — **SKIPPED / FROZEN** (ladder: no 15 after FAIL at 20).  
6. **STOP-MEMO** — [archive/rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md).

---

## Related docs

| Doc | Role |
|---|---|
| [archive/rt-cost-realism-re-derivation-stop-memo.md](rt-cost-realism-re-derivation-stop-memo.md) | **STOP-MEMO** — charter closed |
| [cascade-cost-horizon-physics-charter.md](cascade-cost-horizon-physics-charter.md) | Dual-judge authority — why cost, keep H=6, keep multiples |
| [horizon-tier2-v2-verdict.md](../horizon-tier2-v2-verdict.md) | Path-EV STOP; carry-forward feature locks |
| [triple-barrier-verdict.md](../triple-barrier-verdict.md) | Amend after `c*` sign-off — floors only |
| [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) | Upstream path density context |
| [cascade-strategy-overview.md](../cascade-strategy-overview.md) | Cascade map — friction line updates after merge |
