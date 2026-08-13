# Cascade Cost & Horizon Physics — Dual-Judge Charter (v3)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Scope:** Fresh dual-judge lock on friction realism, 60m vs 90m, TP ceilings, and cascade structural soundness — **after** Horizon Tier-2 v2 path-EV STOP  
**Status:** **ACCEPT WITH REVISIONS** (dual-judge locked) — open **narrow cost charter only**; Horizon feature/label search stays closed  
**Judges:** [Claude Sonnet](cfae50bb-0c8e-4623-8160-952667de4d52), [Gemini Flash](a2d95c56-e066-4694-8b57-b676b08c9601)  
**Date:** 2026-08-13  
**Depends on:** [horizon-tier2-v2-verdict.md](horizon-tier2-v2-verdict.md) (v2 STOP), [triple-barrier-verdict.md](triple-barrier-verdict.md), [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md)  
**Does not reopen:** Regime search, Precision WS2, Horizon v2 feature/label peeks (5/5 spent)

---

## Summary

| Decision | Locked choice |
|---|---|
| New charter? | **YES** — narrow: **RT cost re-derivation** (+ floors as pure function of `c`) |
| Q1 Cost | **30 bps is overly conservative** for liquid Nifty-100 MIS; do **not** silently jump to 10 bps |
| Q2 Horizon | **Keep H=6 / 90m** — better R:R physics and more promising for this cascade |
| Q3 Ceilings | Failure is **partly** cost-driven; 3×/2.5× multiples stay; **input `c`** was never searched |
| Q4 Foundation | Cascade **structurally sound enough to continue**; stop model tweaking; test the untested input |
| Next title | **RT Cost Realism Re-Derivation — Nifty-100 MIS v1** → [charter](rt-cost-realism-re-derivation-charter.md) |

**One-line:** Keep building the cascade — but the next falsifiable experiment is **cost calibration**, not another Horizon feature peek.

---

## Dual-judge scores

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Cost realism of current 30 bps | 2/10 | 5/10 | **REVISE** — 30 bps is a conservative floor, not a typical liquid Nifty-100 MIS cost |
| 60m vs 90m fidelity | 9.5/10 | 8/10 | **ACCEPT** — lock H=6 / 90m |
| Ceiling diagnosis | 9.5/10 | 7/10 | **ACCEPT WITH REVISION** — `c` is the confound; TP **multiples** stay frozen |
| Cascade structural soundness | 9/10 | 5/10 | **ACCEPT WITH REVISION** — not dead; not proven; cost test before foundation verdict |
| Charter readiness | 9/10 | 7/10 | **ACCEPT WITH REVISIONS** — open cost charter; refuse Gemini's immediate 10 bps + new multiples |

**Judge one-liners**

- Gemini: 30 bps is unphysical (~2.5–3× real MIS friction); re-anchor to ~10 bps and recalibrate TP at H=6.  
- Claude: 30 bps is a defensible conservative floor but likely inflated for the liquid half; reopen **only** `c` (decompose + liquidity-tier), keep 3×/2.5×/1.5× formula, max 3 peeks.

---

## Critical questions — locked answers

### 1. Can RT costs be more realistic? Is 30 bps overly conservative?

**Yes — 30 bps is overly conservative as a *typical* Nifty-100 MIS cost. It remains a defensible single-number *stress floor* for the thinner tail — not evidence that the cascade should keep using it as the only economic identity.**

Public statutory + discount-broker schedule (FY25–26 style; Zerodha-class):

| Component | Approx RT (vs position notional) |
|---|---|
| Brokerage (₹20/order or 0.03% cap) | ~0–2 bps on meaningful tickets |
| STT (intraday, sell only 0.025%) | ~2.5 bps |
| NSE txn + SEBI + IPFT + GST + stamp | ~1–2 bps |
| **Statutory + brokerage subtotal** | **~5–8 bps** |

| Slippage / impact (assumption) | Band |
|---|---|
| Liquid front half Nifty-100, modest size | ~5–12 bps RT |
| Thinner Nifty-100 tail / worse SL fills | ~15–25 bps RT |

**Realistic total band (consensus):**

| Sleeve of universe | Realistic RT `c` |
|---|---|
| Liquid front half | **~15–20 bps** |
| Thinner tail | **~25–35 bps** |
| Gemini preferred point estimate | 8–12 bps (baseline 10) — **aspirational; not dual-judge locked** |
| Historical lock | **30 bps** = stress/conservative, not typical liquid |

**Lock:** Step 0 of the new charter must publish a cited statutory decomposition + broker plan assumption **before** any Fold A+B peek. Do **not** soft-replace 30→10 without that note and dual-judge sign-off on the chosen `c`.

---

### 2. Better off with 90m vs 60m?

**Keep 90m (H=6) as primary.** Do not revert to H=4.

#### 2.a Risk-to-reward (Indian equity dynamics)

**90m wins.** Nominal TP:SL multiples are unchanged by vertical H; what changes is **reward-leg reachability**.

| Window | Typical P50 | Typical P75 | Long 90 bps @ old `c` |
|---|---:|---:|---|
| 60m | ~0.28–0.50% | ~0.55–1.03% | At/above P75 for most sectors → structural rarity |
| 90m | ~0.36–0.65% | ~0.68–1.28% | Closer to reachable upper-quartile |

Same economic TP identity + more time → better realized R:R under Indian open-drive / midday continuation dynamics, with MIS cutoffs pulled earlier (Long ~13:45 / Short ~13:30) — already sample-loss **PASS** in v2.

#### 2.b Cascade metrics / what you've been building

**90m is more promising for this cascade — partial lift, not proof.**

Evidence under H=6 path-EV (v2 stop):

- Dual-fold **H5 PASS** on both sleeves under peek-3 locks (path-room demoted; Long chase demoted)
- Top-K TB+1: Long ~9–10%, Short ~15% (up from ~7–11% H4-era band; still not ship)
- H4 stayed **negative** (−20 to −32 bps) under 30 bps friction
- Horizon-path PASS **denied** (Long H2 dual FAIL; Short H2 B FAIL; soft-H3)

Read: H=6 enabled the first dual-fold path-density lift; it did **not** close economics under 30 bps. Reverting to 60m would re-impose worse physics without fixing cost.

---

### 3. Are evals failing because ceilings are too high? Are 3× / 2.5× typical?

**Partly yes on the *input* `c`; no on abandoning cost-multiple design.**

| Claim | Lock |
|---|---|
| 30 bps inflated vs liquid MIS reality | **Yes** — see Q1 |
| Long TP = 3×c / Short = 2.5×c / SL = 1.5×c as *formula* | **Keep** — standard barrier economics; not the anomaly |
| Absolute 90 / 75 bps targets at 30 bps | Sit in a harsh tail of 60–90m move distributions → TB+1 rarity is partly physics |
| Typical Indian intraday momentum | Often runs on **much lower effective friction** and **smaller absolute TPs**; Gemini's “35–50 bps TP at ~10 bps friction” is directionally right as market practice, but **not** locked here without a `c` decision |

**Revision vs Gemini:** do **not** jump to Long TP 40 / Short 35 / SL 20 in the same breath as picking `c=10`. New floors must be **`k × c_new`** with the same `k` (3 / 2.5 / 1.5) unless a **separate** dual-judge note amends multiples.

**Key process point (Claude):** v2 fixed `c` and searched the model. It never searched `c`. That untested confound is the new charter's single variable.

---

### 4. Is the cascade structurally sound for Indian equities?

**Continue — do not declare the foundation dead; do not keep tweaking Horizon features under the exhausted v2 budget.**

| Evidence for soundness | Evidence against “ship-ready” |
|---|---|
| Modular Regime → Horizon → Precision separation | Regime never cleared as economic gate (correctly CLOSED) |
| Horizon H1 non-null across peeks (real XS skill) | Horizon-path PASS never achieved |
| H=6 + path-EV produced dual-fold H5 under demotions | H4 always negative under 30 bps; abs TB+1 still thin on Long |
| Precision correctly blocked from monetizing non-+1 paths | Cost identity never stress-tested downward |

**Verdict:** Fundamentally sound *architecture* for Indian MIS large-cap intraday; **parameter economy** (friction) is the next falsifiable layer. Keep tweaking what is sound — stop tweaking what is exhausted (Horizon feature peeks).

---

## Freeze vs reopen

| Freeze | Reopen (cost charter only) |
|---|---|
| Horizon v2 STOP-MEMO; peek ledger 5/5 closed | RT cost `c` — statutory vs slippage decomposition |
| Regime CLOSED; Precision WS2 blocked | Liquidity-tiered `c` **if** tier rule pre-registered before peek 1 |
| H=6 primary; H=4 diagnostic only | TP/SL floors **only as** `3×c / 2.5×c / 1.5×c` of revised `c` |
| Path-room demoted; Long `stock_r_15` demoted; Short `stock_r_15` kept; aux=0 | Horizon A+B **re-measure** under new `c` (counts against **new** peek budget) |
| Separate Long/Short; K=5/3 | — |
| Cost-multiple **formula** | Multiples themselves stay frozen this charter |

---

## Next charter — process locks

**Title:** RT Cost Realism Re-Derivation — Nifty-100 MIS v1

| Lock | Rule |
|---|---|
| Peek budget | **Max 3** Fold A+B harness invocations (single-variable; tighter than Horizon v2's 5) |
| Step 0 (no peek) | Publish cited statutory + broker decomposition table |
| Step 1 (no peek) | If tiered `c`, pre-register ADV/liquidity split rule |
| Dual-judge gate | Sign-off on chosen `c` **before** TB floors propagate |
| Single-variable | No Horizon feature/label/H changes inside this charter |
| Multiplicity | Cost-charter peeks **cannot** borrow from Horizon v2's exhausted 5 |
| Stop | Exhaust 3 peeks or dual-fold economics clear under new `c` → stop-memo / merge |

**Suggested candidate `c` ladder (pre-register, do not grid):** stress **30** (archive) → working **20** (liquid-half) → aggressive **15** (only if 20 clears diagnostics). Gemini's **10** stays a sensitivity report-only point until Step 0 + dual-judge promote it.

---

## Forbidden moves

- Silent 30→10 (or any) cost swap without Step 0 + dual-judge sign-off  
- Lowering TP/SL without a revised `c` (or inventing new multiples mid-peek)  
- Reopening Horizon v2 features / labels / exhausted peek budget  
- Reopening Regime or Precision WS2  
- Reverting primary H to 60m to “fit” afternoon bars  
- Claiming cascade-ready / Horizon-path PASS / book PnL from cost change alone  
- Post-hoc liquidity-tier boundaries after seeing A+B  

---

## Related docs

| Doc | Role |
|---|---|
| [rt-cost-realism-re-derivation-charter.md](rt-cost-realism-re-derivation-charter.md) | **Operational next charter** — Step 0 / peeks / floors |
| [horizon-tier2-v2-verdict.md](horizon-tier2-v2-verdict.md) | Path-EV charter STOP — why cost is next |
| [triple-barrier-verdict.md](triple-barrier-verdict.md) | TB geometry; amend only after `c` lock |
| [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md) | Why upstream path density matters |
| [regime-tier1-stop-memo.md](archive/regime-tier1-stop-memo.md) | Regime CLOSED |
