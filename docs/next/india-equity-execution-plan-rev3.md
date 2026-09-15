# Retail India desk — Execution Plan, Rev 3.0

| | |
|---|---|
| **Date** | 2026-09-10 |
| **Status** | BLUEPRINT Rev 3.0 / DRAFT — competing charter |
| **Charter** | [india-equity-architecture-blueprint-rev3.md](india-equity-architecture-blueprint-rev3.md) (**Claude Opus**) |
| **This plan** | Written to complete the Opus Rev 3.0 pair. Opus landed the blueprint, then `resource_exhausted` before writing the plan. Book names, gates, kills, H2-ABS, L13 and the `src/` delta are taken from that blueprint, not re-litigated. |
| **Does not replace** | [india-equity-architecture-blueprint-rev2.md](india-equity-architecture-blueprint-rev2.md) (Rev 2.0, ACTIVE) · [india-equity-execution-plan.md](india-equity-execution-plan.md) (Rev 1.0, superseded) |
| **Branch** | `in-equity` |

---

## How to read this plan

This is a **milestone map for the Opus Rev 3.0 brief**, not a peek charter and not a restart of Rev 1.0.

Every milestone has four parts: **Why / Build / Exit / Stop**. Rules:

1. **No milestone starts before its predecessors exit.**
2. **No book's returns are looked at before K0 publishes pre-registration** (n, σ, T, MDE, E_net). σ is a return-free estimator (blueprint §7).
3. **A closed book is a completed milestone.** STOP memo, no “paused”.
4. Unsourced numbers stay in the blueprint [Appendix A](india-equity-architecture-blueprint-rev3.md#appendix-a--working-numbers-register) until the named milestone resolves them. **W3-01 and W3-04 first** (blueprint Appendix A).
5. Poetry only. No HMM, LightGBM, MLflow, Kaggle, or Polars unless a named milestone imports them.
6. **A charter whose conclusion is “do not trade this” should not require a platform** (blueprint §10). Expected new code: one module, one extended function, one universe flag, three pre-registration files, zero new runtime dependencies.

Until a human **accepts Rev 3.0**, none of V0 / K0 / F1 is more than paper. The live desk is Rev 2.0. Nothing here authorises a rupee, a module, a dependency, or a data purchase.

---

## Inherited Rev 1.0 state (do not restart)

| ID | Status |
|---|---|
| P0, U0 (narrowed to Nifty 50 + Next 50), H0, L1, L2 | **DONE** |
| P1 | **STOPPED** — packaged default (`docs/archive/p1-stop.md`) |
| M1, R0 | **Closed** |
| A0 | **Deferred to 2027-08-31** |
| S0 | Gated on SEBI reformed-SLBM circular |
| L0 | **IN PROGRESS** (paper). No live capital. |
| X0 | Pending L0 + two live quarters |

New work hangs off **H0 / U0**. Critical path if Rev 3.0 is accepted: **`V0 → K0 → F1`**. Books D and Z die at K0. Book Q is expected to die at K0. F0 is skipped unless K0 leaves Q open.

---

## Non-negotiables (locks)

**L1–L9, L11, L12** stand exactly as in [india-equity-execution-plan.md](india-equity-execution-plan.md). Spread is **outside** `costs` (blueprint H1): a book that quotes 3.9 bps as its trading cost has failed H1's spirit.

**L10 — AI — UNCHANGED, by arithmetic not taste.** Blueprint §8.6: MDE = 2.80 σ / √T is a property of the sample, not of the signal. Relaxing L10 buys **zero** hurdle relief for D, Z or Q. STOP memos must **not** blame L10. `ai.extract.etf` is specified and **not in v1**; V0 hand-reads six to twelve factsheets.

**L13 — Rev 3.0.** A named ETF is tradable on date *t* only if it is on the Book V pass list **as of *t***. Backtesting the *index* and trading the *ETF* is a look-ahead fail. H4's T is the **intersection** of index history, ETF listing date, and V-pass dates (blueprint §7).

**H2-ABS** (blueprint §11) is a Rev 3.0 hurdle, not a silent rewrite of [h0-hurdles.md](h0-hurdles.md): after-tax desk return ≥ after-tax 91-day T-bill roll + 200 bps = **5.85%/yr** (W3-07). It binds any sleeve whose claim is “net PnL positive when Nifty is flat or down.”

---

## Milestone map

```
Rev 1.0 (unchanged):
P0 → U0 → H0 → L1 → L2 → P1 → L0 → X0

Rev 3.0 (gated on human accept of the Opus charter):

         U0, H0 ──> V0 ──> K0 ──┬──> STOP D, STOP Z
                                ├──> STOP Q   [expected]
                                ├──> Q1       [only if K0 passes H4 — not expected]
                                └──> F0       [only if Q still open]
         V0, P1 ──────────────> F1   Book W decision note
                                └──> L0 may emit Book W fund instructions
                                     after F1, still no live capital until L0 exits
```

| ID | Milestone | Depends on | Expected result |
|---|---|---|---|
| **V0** | Book V — ETF tradability and routing ledger | U0, human accept | Pass list; resolve W3-01, W3-03, W3-04. Most sectoral names fail. Nifty 50 class expected to pass. |
| **K0** | Pre-register Q / D / Z; MDE; STOP memos | H0, V0 | **D and Z close, no peek.** Q fails H4 **7.7×** (index T) / **12.1×** (ETF T) and closes. |
| **F0** | Sectoral index + ETF tracking panel | K0 *if Q still open* | **Skip** on the expected path. |
| **Q1** | Book Q ₹0 monthly-rotation screen | K0 `passes_h4: true` | **Likely never starts.** |
| **F1** | Book W packaged-different-beta decision | P1, V0 | **The 4/5 deliverable.** Direct-plan tilt, or Rev 1.0 / Rev 2.0. |
| **L0 / X0** | Unchanged | Rev 1.0 | Paper then live under whichever charter the human picked. |

---

## Research spend ladder (INR)

Unchanged in spirit from Rev 1.0.

| Tier | Ceiling | Unlocked by | What it buys |
|---|---|---|---|
| **0** | **₹0** | — | V0, K0, F1. AMFI AUM/TER/NAV, NSE quotes / bhavcopy, NSE Indices TRI and factsheets, fund SIDs. |
| **1** | **₹6,000/yr** | **L0 exit only** | Broker API. Not for V0. |
| **2** | **₹8,400 one-off** | Named exit that bhavcopy cannot meet | Three months of minute bars. **Book Z is closed; do not buy.** |
| **∞** | — | — | NSE Data & Analytics / CMOTS / LSEG. Do not contact. |

If a 20-day median quoted spread cannot be rebuilt from free NSE quotes, **fail the name** (blueprint §8.1 kill / L8). Do not buy a vendor spread history to rescue Book Q.

---

## V0 — Book V, ETF tradability and routing ledger

### Why

Statutory ETF round trip is **₹39.02 = 3.9 bps at ₹1 lakh** and **₹133.75 = 2.7 bps at ₹5 lakh** (`costs`, 2026-09-10). Stored sectoral quotes are **154–346 bps (W3-01, stale)** — up to 50× the statute. V0 replaces those stored quotes with a 20-day median from free NSE data **before any return is examined**. It also extends Book L's routing to a three-way choice: ETF at market vs direct index fund at NAV vs constituent basket, adding the premium/discount term (blueprint §8.1, §10).

W3-01 and W3-04 are **first**. The product board is not actionable until they are measured.

### Build

1. **`src/books/etf_screen.py`** — the only new module. Per name, per as-of date *t*:
   - AMFI AUM, TER
   - 20-day median quoted spread (bps) and ADV notional
   - 20-day median \|LTP − NAV\| / NAV
   - top-1 and top-5 weights, effective N = 1 / Σwᵢ², index family
   - pass/fail against the Book V gate (blueprint §6.1):
     - AUM ≥ **₹2,000 crore**
     - 20-day median quoted spread ≤ **25 bps**
     - ADV notional ≥ **₹25 crore**
     - 20-day median absolute premium/discount ≤ **15 bps**
2. **`src/universe.py`** — as-of-date flag `etf_liquid` from the pass list (**L13**). A sectoral ETF maps to **one sector** for the 25% cap (not to one 6% name).
3. **`src/books/ledger.py`** — extend `etf_vs_constituents` to
   `route_exposure(etf_quote, etf_premium, fund_ter, constituent_impact)` (~20 lines). All-in ETF cost = `costs` statutory + Book V half-spread. Prefer the index fund at NAV when the ETF's premium exceeds its spread advantage (blueprint §12).
4. **`docs/next/v0-etf-screen.md`** — dated pass/fail table. No return column. No ranking by past performance.
5. Resolve **W3-01, W3-03, W3-04**. Hand-read six to twelve factsheets; `ai.extract.etf` is not in v1.

`fetch` reuse: session-cookie warm-up, ≤ 1 request / 2 seconds, content-addressed cache, **no fetching 09:00–16:15 IST**.

### Exit

- Dated pass list exists. NIFTYBEES-class names expected to pass. PHARMABEES / FMCGIETF / BFSI / AXISCETF expected to **fail AUM**.
- BANKBEES and ITBEES are pass or fail on **measured** 20-day median spread, not on 154 / 258 bps stored figures.
- `route_exposure` prefers the direct Nifty 50 fund over NIFTYBEES at 4 turns/yr if the §5.4 drag comparison still holds (~16 bps/yr).
- `etf_liquid` is as-of-date; a date-shift of V0 inputs is allowed to change the flag.
- `poetry run pytest` green if code was added; no new runtime dependency.

### Stop

If **zero** sectoral/thematic names pass, record that in `v0-etf-screen.md`; Book Q's instrument set is empty and K0 closes Q for lack of universe. If NIFTYBEES-class quotes themselves cannot be reconstructed from free sources, write `docs/archive/v0-stop.md` — the screen is broken, not the names.

---

## K0 — Pre-registration and H4 for Books Q, D, Z

### Why

Same job as H0 for the three books this brief named. Publishing MDE after seeing 5-session ETF returns is decoration. K0 is where D and Z die, and where Q is expected to die. Blueprint §7 / §8.3–§8.5 already compute the failures; K0 **records** them under `harness` before any peek.

### Build

1. Three pre-registration files, committed **before** F0 or any sectoral-return peek:
   - `docs/next/k0-prereg-book-q.md` — 12-month formation, 1-month hold, long-only, 25% sleeve, V-pass universe. σ from **return-free** realised vol of (sectoral index TRI − Nifty 50 TRI). T = intersection of index history, ETF listing, V-pass dates (W3-06). Blueprint working: σ 10.4%, T 20 → MDE **6.51%**; T 8 → **10.30%**. E_net 1.70% (W3-11, reverse-engineered — if pre-registered gross is lower, failure widens). **Fails H4 7.7× / 12.1×.**
   - `docs/next/k0-prereg-book-d.md` — 5-session TSMOM. σ 14.0%, T 20 → MDE **8.77%**; T 8 → **13.86%**. E_net ≤ 2.0%. Required desk-level gross sector alpha **22.75%/yr** (blueprint §3.2). **Fails H4 ≥ 8.8×.** Permanently closed, not deferred (T required for a 2%/yr effect: **1,537 years**).
   - `docs/next/k0-prereg-book-z.md` — 1-day MIS or same-day square. σ 19.0%, T 20 → MDE **11.90%**; T 8 → **18.81%**. Plus s.66, plus H6. **Fails H4 ≥ 11.9×.**
2. STOP memos **at K0, before any data access**:
   - `docs/archive/book-d-stop.md`
   - `docs/archive/book-z-stop.md`
   - `docs/archive/book-q-stop.md` if `passes_h4` is false (expected).
3. `harness` loads the new files the same way as `h0-prereg-book-*.md`. Spec budget 5; sixth refused.
4. Pin `mde()` for **6.51%, 8.77%, 11.90%** (blueprint §10) in addition to Rev 1.0's six values.
5. Resolve **W3-06, W3-07, W3-10, W3-11** as *inputs to pre-registration*, not as measured P&L. W3-02 (daily σ) may be recomputed from U0 without opening a book.

Do **not** peek ETF or sectoral-index *strategy* returns to choose σ.

### Exit

- Three pre-registrations exist with SHA, n, σ, T (intersection), MDE, E_net, `passes_h4`.
- D and Z have STOP memos **before** any of their data is touched. Memos must state: all-in RT from `costs` + V0 half-spread; s.196 or s.66; MDE vs ½ E_net; 22.75%/yr gearing for D; H6 for Z; Joseph (2016) sign conflict for D; **what would reopen** from blueprint §9 (not “more AI”; not L10).
- Q either has a STOP memo (expected) or an explicit `passes_h4: true` that unlocks F0/Q1.
- H2-ABS base rate (W3-07) is written into the Q pre-reg even if Q closes, so a later agent cannot quietly drop it.

### Stop

If σ and T cannot be stated without looking at the strategy's own returns, **the book closes**. Same H0 rule. If V0 produced an empty sectoral pass list, Q closes for lack of universe without a peek.

---

## F0 — Sectoral index and ETF tracking panel (gated; expected skip)

### Why

Only if K0 leaves Book Q open. PIT join: sectoral TRI, ETF LTP, NAV, premium, `etf_liquid` as of *t*. Without it, an index-level Q1 would look ahead on liquidity (**L13**).

### Build

`panel` columns for V-pass tickers only. `close_method` still **L6**. No fetch 09:00–16:15 IST. No Polars unless this milestone actually imports it.

### Exit

- Look-ahead test: shift V0 inputs one session; `etf_liquid` may change.
- ≥ 1,000 sessions of *index* TRI for each sector whose ETF is on the pass list; ETF rows only from listing date.

### Stop

If NAV/LTP cannot be aligned from free sources, **do not buy a vendor** — close Q, write `docs/archive/f0-stop.md`, proceed to F1.

**If K0 already closed Q, skip F0 entirely.**

---

## Q1 — Book Q ₹0 screen (not expected to start)

### Why

Only if `passes_h4` at K0. Reconstruct monthly ranks on dates with `etf_liquid`, apply `costs` + Book V half-spread + s.196, sleeve 25% of ₹50 lakh, remainder core. Must clear **H2, H2-ABS, H3, H4, H5** simultaneously, five specs max.

Honest expectation from blueprint §8.3: a fully successful Q contributes **42 bps** of the desk against **46 bps** of desk-level friction and Book L's already-measured **95.92 bps**. Ranking, not just MDE, is why Q sits third.

### Exit / Stop

Clear all five hurdles on V-pass dates only. Expected: does not run. If it runs and fails, `docs/archive/book-q-stop.md`. Reopen for a *new* Q specification is only blueprint §13 item 1: V0 finds ≥ 3 sectoral ETFs with 20-day median quoted spread ≤ **11 bps** and AUM ≥ ₹2,000 crore — then re-run MDE at the lower friction. **Book D stays closed** even then (50 × 8.2 bps = 4.10%/yr and MDE 8.77%).

---

## F1 — Book W decision note (the actual deliverable)

### Why

Q6's honest product (blueprint §1.6, §8.2): a 4/5 investor who wants not to sit in range-bound Nifty 50 should **buy a direct-plan different beta and hold it past 12 months**, not rotate BANKBEES every five sessions. Cadence arithmetic: the same 8% gross keeps **0.32%/yr** at 50 five-session turns and **6.89%/yr** at one 13-month hold (blueprint §3.1). P1 already defaulted packaged. Book W **buys the fund**; it does not need PIT factor constituents.

Book W is a **decision**, not a measured edge. It is **not** required to clear H2's 300 bps. Every packaged alternative correlates **0.87–0.93** to Nifty 50 (W3-05): a tilt, not an escape. H2-ABS is unreachable for any long-India sleeve in a flat or down year (blueprint §3.4).

### Build

1. Extend `src/books/packaged.py` — add Next 50, Midcap 150, 100 Low Vol 30 to the existing TRI-versus-TER comparison. **No self-run replication.**
2. `docs/next/f1-packaged-different-beta.md` — one of three forms, with numbers:

   | # | Recommendation | When |
   |---|---|---|
   | **1** | **100% Nifty 50 direct fund** (Rev 1.0) | Every packaged alternative's 5-year TRI after TER trails Nifty 50 TRI by **> 300 bps annualised** and the investor still wants India equity. Book W closes. |
   | **2** | **≤ 40% named direct-plan tilt** (Next 50 / Midcap 150 / MOM30 / Low Vol 30), rest Nifty 50 core; Book L on both; any one sector ≤ **25%** | Investor wants tracking error and will hold 12 months. |
   | **3** | **Rev 2.0 carry** | Requirement is positive rupees **independent of** the Indian tape. Book W closes. |

3. Resolve **W3-05, W3-08, W3-09**. Print ρ, β, active σ, TER, 1y/3y/5y TRI vs Nifty 50 TRI, tax class (s.198 if held > 12 months).
4. Explicit: **no 5-session ETF rotator.** Point at K0 STOP memos for D, Z, and (expected) Q.

### Exit

A dated recommendation with TER, 5y TRI delta vs Nifty 50, the 25%/40% caps, and which of (1)(2)(3) was chosen. No new runtime dependency. If Book W is (2), L0's instruction list may later include **index-fund purchase/redemption**, never D/Z orders.

### Stop

If AMFI TRI/TER cannot be read, default (2) to the Motilal/UTI/Axis/Bandhan **direct** momentum/low-vol funds at ~0.30–0.50% TER cited in Rev 1.0, mark TRI **(working)**, and still refuse a 7-day rotator.

Kill (blueprint §8.2): (a) 5y trail > 300 bps → (1); (b) needs > 40% of equity or > 25% in one sector → close; (c) absolute rupees regardless of tape → (3) Rev 2.0.

---

## L0 and X0

Unchanged from Rev 1.0. Rev 3.0 does not move live capital earlier (**L7**).

If the human accepts Rev 3.0 and F1 chose (2), L0 may emit Book W rebalance instructions on the existing instruction-list path. No new order type. No intraday path (**H6 closes Book Z by construction**).

X0 additionally checks:

- V0 pass list still valid (monthly refresh).
- Every closed 7-day book's reopen condition (blueprint §9 and §13).
- H2-ABS if any trading sleeve was live (none expected).
- Realised single-sector weight: above **25%** on any measurement date is a limit breach, not a drift (blueprint H7 addition).
- Spend against the ladder.

---

## Calendar reality — additions

Rev 1.0 calendar stands (CAS, expiry, tax year, filing, Book A 2027-08-31). Add:

| Item | When | Why |
|---|---|---|
| V0 refresh | Month-end, after AMFI AUM | Spreads and AUM change; **L13** is as-of |
| Factor / sectoral index reconstitution | NSE semi-annual (Mar / Sep) | Book W holds the *fund*; no action unless a self-run book exists (it does not) |
| Human charter pick | Before V0 code | Until then this plan is paper |
| H2-ABS base (T-bill / FD) | Quarterly with W3-07 | Absolute hurdle is a rate, not a constant |

---

## Working-numbers ownership (Rev 3.0)

| # | Verify at |
|---|---|
| W3-01, W3-03, W3-04 | **V0, first** |
| W3-02 | U0 / F0 (skip F0 if Q closed) |
| W3-06, W3-07, W3-10, W3-11 | **K0, before peek** |
| W3-05, W3-08, W3-09 | **F1** |
| W3-12 | Assumption; not verified |

---

## STOP memo template

Use the Rev 1.0 template in [india-equity-execution-plan.md](india-equity-execution-plan.md). Book D / Z / Q memos must state:

- the brief's Q (1-day direction / 5-session TSMOM / monthly rotation),
- all-in RT from `costs` + V0 half-spread (never 3.9 bps alone),
- tax line (s.196 or s.66),
- MDE vs ½ E_net, with **intersected T**,
- 25% sector-cap gearing where it binds (D: 22.75%/yr gross to move the desk 300 bps),
- **what would reopen** from blueprint §9 / §13 — a spread, a rate, a lot size, a T, a charter pick. Not “more research”. Not L10.

---

*Charter (Opus): [india-equity-architecture-blueprint-rev3.md](india-equity-architecture-blueprint-rev3.md). Does not replace: [india-equity-architecture-blueprint-rev2.md](india-equity-architecture-blueprint-rev2.md) (Rev 2.0, ACTIVE).*
