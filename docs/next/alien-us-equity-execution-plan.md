# Alien US desk — Execution Plan

**Authority:** Implements [alien-us-equity-architecture-blueprint.md](alien-us-equity-architecture-blueprint.md) **Rev 1.0**
**Investor:** Indian **RNOR** (2–3 year working window, then **ROR**), US **NRA**, W-8BEN on file, DTAA claimed, investing already-held USD from US accounts. Not LRS-funded.
**Status:** **ACTIVE — nothing measured.** Rev 1.0, new sibling programme. All statutory rates are **working**.
**Date:** 2026-09-13
**Goal:** Establish whether any after-cost, after-**both**-tax algo book beats an after-tax accumulating Irish UCITS core hold for a $25k–$500k NRA/RNOR desk — and, before that question is even asked, execute the two wrapper actions that are worth more than any book on the menu and that **expire with the RNOR window**.
**Constraint order (fixed):** **tax wrapper (US NRA + India RNOR/ROR cliff) → estate/situs → friction → inference → capacity/eligibility → alpha.**
**Milestone IDs in this plan belong to this programme.** They are not the US-person desk's P0 / U0 / H0 / A / B / C series, and its H1–H6 do not apply here.

---

## How to read this plan

A **milestone map, not a peek charter.** No milestone authorizes a look at a strategy result unless its Exit names the statistic in advance. Each milestone has four fields:

- **Why** — the question it answers
- **Build** — the artefacts, and nothing beyond them
- **Exit** — the numeric condition to proceed
- **Stop** — the condition that closes the branch and produces a STOP memo in `docs/archive/`

Milestones run in sequence except where a $0 parallel track is named. A STOP memo is a completed milestone, not a failure.

**The ordering principle on this desk is different from the US-person desk's, and it is deliberate.** There, everything queued behind a cost model because nothing was interpretable without one. Here, **two milestones have a deadline and the rest do not.** The RNOR window closes in 2–3 years; the basis step-up inside it is worth 300–860 bps of capital, once, permanently. So **W and R run first, ahead of all alpha work**, and the alpha branch is explicitly allowed to wait.

---

## Non-negotiables (locks)

| # | Lock |
|---|---|
| 1 | Constraint order is fixed: **tax wrapper → estate/situs → friction → inference → capacity/eligibility → alpha.** Alpha work before rung 5 is complete is out of scope. |
| 2 | Every result is reported **after cost and after both tax systems**, against the **rebuilt after-tax accumulating-UCITS core hold**. **State the RNOR number and the ROR number separately. Where they differ, ROR governs.** Gross-only is not a result; RNOR-only is not a result. |
| 3 | **MDE is printed before every peek.** MDE > 0.5 × hypothesized effect closes the book without a peek. |
| 4 | `costs`, `tax`, `situs`, `receipt`, and `residency` are single, unit-tested modules. No backtest may re-implement any of them. **`tax` takes a residency calendar, not a rate.** |
| 5 | Point-in-time or it does not exist. Delisted tickers present; no survivorship. |
| 6 | Trial budget **5 pre-registered specs per book, α = 0.01**, logged including abandonments. |
| 7 | **No live capital before L0, except:** N0's tiny calibration fills, **and the W/R wrapper transactions**, which are domicile and basis actions rather than strategy deployments and are **date-bound**. Paper 60 sessions, then 10% size for 60 sessions. |
| 8 | **Aggregate US-situs market value ≤ $60,000 at all times**, enforced pre-trade. Lifts only to a W3-insured amount. |
| 9 | **Every cash leg lands in a US account during RNOR. Zero tolerance.** |
| 10 | No short stock, no naked short options, no leverage above 1.0×, **no offshore holding company, no currency hedge** in v1. |
| 11 | **No vendor data purchase unless a later milestone explicitly names the SKU.** This programme authorizes **$0** of paid data now. Discovery-data ceiling **$346.50** (Norgate Platinum, trial first, at E1 only) — **and if the US-person desk buys that panel for its B1, this programme spends $0 and reuses the dump.** Do not buy any options tape: Book V is closed on a pre-tax measurement. |
| 12 | **One non-data purchase is authorized and it comes first:** a written US-NRA + India-RNOR/ROR tax opinion, ceiling **$1,500–$3,000**, at W1, **required before R1.** This is professional services, not a data SKU. |
| 13 | No HMM, LightGBM, MLflow, or Kaggle client enters `pyproject.toml`. |
| 14 | AI produces features from text and runs ops checks. **AI does not forecast returns and does not produce a tax conclusion.** |
| 15 | **Own capital only.** No third-party money, no customers, no dealer inventory, no advertised performance — the IRC 864(b)(2) safe harbor depends on it. |
| 16 | **Do not import the US-person desk's tax arithmetic.** Book C's 35.5 bps, the §1256 wedge, ST 40% / LT 20%, IRA location, the IRC 1091 wash-sale engine, and H1's 200 bps are not on this desk. Its **pre-tax measurements** (friction table, MDE formula, A1's 1.19×, B0/B0.5's drift) are reused as measured. |
| 17 | **Do not reopen Book V (index VRP) on a tax story.** A1 failed **pre-tax** at 1.19× against a 2× hurdle. The §1256 subsidy that once ranked it is worth **0** to an NRA. Reopening requires new data. |

---

## Milestone map

| ID | Name | Status | Hard stop if… |
|---|---|---|---|
| **N0** | Posture, residency calendar, dual-tax lock | Not started · **$0 paid data** | Costs cannot be pinned within tolerance, or the RNOR expiry date cannot be established |
| **W0** | Wrapper arithmetic ($0) | Not started | Measured recurring wrapper saving < 15 bps/yr → the domicile switch is not worth the transaction |
| **W1** | Broker + product eligibility, and the written opinion | Not started · **first authorized spend** | No accessible broker will hold Irish accumulating UCITS → degraded path: US-listed core under the $60k cap plus a priced tail |
| **W2** | Synthetic vs physical gate ($0) | Not started | Measured advantage < 10 bps/yr, or counterparty exposure > 10% NAV → physical only |
| **W3** | Price the estate tail ($0 to quote) | Not started | No acceptable, enforceable cover → situs cap stays $60,000 → Book E closes on N2 |
| **R0** | Embedded-gain and cliff-date ledger ($0) | Not started | Step-up worth < 100 bps of capital → the one-time action is dropped, the 24-month discipline stays |
| **R1** | **Step-up execution — the only date-bound milestone** | Not started · gated on W1 opinion | Opinion does not support it, or the RNOR year has already closed |
| **R2** | Standing realisation schedule | Not started | — (permanent discipline, no exit) |
| **U0** | Universe and PIT panel (listed) | Inherits the US-person desk's listed artefacts | Delisted *prices* unobtainable at acceptable cost → Book E closes; W and R proceed |
| **H0** | Inference design for **this** desk's books | Not started | Every candidate book's MDE > 0.5 × its effect → programme stops at H0 with zero data-mining risk |
| **E0** | Book E — re-gate PEAD at ROR rates ($0) | Not started | Survivorship-corrected bound < **58 bps/event after ROR tax**, or the situs cap forces w below what N1 needs |
| **E1** | Book E — PEAD existence (PIT panel) | Not started · Norgate trial | Pooled net-of-cost drift < 58 bps/event after ROR tax on ≥ 6,000 clustered events, or the effect lives only below $20M ADV |
| **E2** | Book E — economics, situs sizing, AI increment | Not started | Sleeve excess < 500 bps/yr at ROR at the permitted weight, or text features add < 10 bps over numeric surprise → AI removed |
| **E3** | Book E — tradability | Not started | Realised mid-cap round-trip > 25 bps, or auction fills degrade the drift by > 15 bps |
| **L0** | Operating loop | Not started | No book passed N2 → global STOP, 100% core posture |
| **X0** | Kill and **residency** review | Not started | Standing quarterly gate, plus a hard annual residency and US-day-count review |

**Critical path:** **R0 ∥ W0 → W1 (opinion + broker) → W2 → R1 (deadline) → R2** · then, and only then, N0 completion → U0 → H0 → **W3 → E0 → E1 → E2 → E3 → L0.** X0 is standing once live.

**Read that ordering literally.** The wrapper and step-up branch does not wait for the cost model, because its value is not a function of trading cost. The alpha branch waits for everything. If the programme runs out of patience or capital after R2, it has already captured the majority of the value available to this taxpayer.

---

## Research spend ladder

Discovery purchases exist to **kill or certify**. They are not infrastructure.

| Step | Book | Spend | What it answers | Authorizes next |
|---|---|---|---|---|
| **First spend** | W / R | **$1,500–$3,000** written cross-border tax opinion (professional services, **not** a data SKU) | Does the 25% DTAA rate apply to an individual? Is passive US income outside Indian tax during RNOR when received in a US account? Is the pre-cliff step-up supportable against GAAR? Irish CAT on UCITS units? Any surviving effect of the 1953 India–US estate convention? Situs of listed derivatives? Schedule FA during RNOR? | **R1** — and nothing else. No capital moves without it |
| Now | W0, W2, R0, E0, H0, U0 | **$0** | Published TERs, treaty rates, audited fund withholding, broker statements, EDGAR, the US-person desk's existing screens re-taxed | W1 / R1 / E1 |
| Next dollar | E1 | Norgate US Stocks Platinum **3-week trial**, then **$346.50 / 6 months** dump-and-cancel if the trial panel is complete. **This is the entire data ceiling.** **If the US-person desk has already bought this panel for B1, this programme spends $0 and reuses the dump** | Delisted PIT prices + historical constituents, 2010–2026 | E2 only if E1 passes |
| Closed at discovery | — | **Any options tape** (Cboe DataShop, OPRA, CGI, Optsum) — Book V is closed on a pre-tax measurement · Polygon as a default · Sharadar before E1 · Databento · CRSP | — | **Do not buy** |

**Programme data-spend ceiling before L0: $346.50, and plausibly $0.** Spend to date: **$0**. The US-person desk's $346.50 Norgate ceiling is *that* programme's number; this ceiling is the same SKU and the two programmes must not pay for it twice.

Note what is **not** a certifying screen. W0 is arithmetic on published documents and certifies Book W's *saving*, but it cannot certify broker access — that is W1. E0 re-taxes the US-person desk's listed screens; it is a **kill screen only**, because Lock 5 still requires delisted prices.

---

## N0 — Posture, residency calendar, and the dual-tax lock

### Why

Nothing on this desk is interpretable until three things are code: what a trade costs, what a gain is taxed at **in which year**, and which holdings are US-situs. Rungs 1, 2, and 3 become modules here. **N0 does not gate the W/R branch** — the wrapper arithmetic is published-document arithmetic and the step-up's value does not depend on a 3 bps cost calibration.

### Build

1. `residency`: RNOR start, **RNOR expiry date**, projected ROR date, Indian tax-year boundaries under ITA 2025 (in force 1 Apr 2026), and a **US physical-presence day counter** with a hard alert at 150 days and a tripwire at 183.
2. `tax`, rewritten for two jurisdictions and three regimes — `us_nra`, `india_rnor`, `india_ror` — taking the residency calendar as input. Rates **working and configurable**: US FDAP 25% with W-8BEN / 30% without, US capital gains 0, India RNOR 0 on foreign passive income received abroad, India ROR 13.0% LTCG above 24 months on the **INR-measured** gain / ~31.2% slab STCG / dividends at slab with FTC. **No IRA, no §1256 December mark, no IRC 1091 engine.** Indian set-off and 8-year carry-forward instead. Unit-tested against hand-worked examples in each regime **and a transition-year case**.
3. `situs`: per-holding US-situs classifier (US corporation stock **and** US-listed ETF shares and US MMF shares are situs; Irish UCITS units, US bank deposits, and directly held T-bills are not, **working**) with a hard **$60,000** aggregate pre-trade block.
4. `receipt`: an assertion that every cash leg routes to a US account; a standing broker instruction pinning the settlement account.
5. `costs`: the US-person desk's product buckets reused as measured, **plus** an LSE/UCITS bucket (8–15 bps at small size, 4–8 bps at $100k+ clips, no UK SDRT on Irish-incorporated shares) and a **zero-FX assertion** for USD-denominated lines.
6. **The rebuilt benchmark series, 2005–2026:** an after-tax accumulating Irish UCITS core hold, 70/30 US/ex-US, 15% fund-level US withholding, 0% investor-level, blended TER. **This series is the denominator of every later claim on this desk.** Publish the RNOR line and the ROR line, including the INR-measured accrual-equivalent stress.
7. W-8BEN on file with the Indian PAN as foreign TIN; confirm in writing that no ITIN is required for publicly traded securities income.
8. 200 real fills in tiny size across the UCITS core line, one US large cap, one US mid cap, and one SPX spread, purely to calibrate `costs`. Operational, not a vendor SKU.
9. **Data decision, $0 paid:** fund KIIDs and audited annual reports, LSE/Euronext published spreads, SEC EDGAR, FRED, Yahoo, broker historical. **No Norgate, no Polygon, no Cboe, no Sharadar.**

### Exit

All cost, tax, situs, and receipt unit tests pass in **both** regimes and across a transition year; modelled cost matches the 200 fills within 3 bps (US equities/ETFs), 5 bps (LSE UCITS), 0.3% of premium (options); the rebuilt core benchmark reproduces the underlying index net total return within 5 bps/yr; the `situs` cap demonstrably blocks an order; the `receipt` assertion demonstrably blocks a non-US settlement instruction; the RNOR expiry date is documented.

### Stop

Costs cannot be pinned within tolerance → no book on this desk can be evaluated and the alpha branch stops here. **W and R proceed regardless** — their value is arithmetic, not cost-sensitive.

---

## W0 — Wrapper arithmetic ($0)

### Why

Decide the core wrapper before anything is bought, because it is the largest recurring number on the desk and because the decision is arithmetic on published documents. It costs nothing and it cannot be deferred: every dollar held in the wrong wrapper leaks while the question is open.

### Build

1. For each candidate core line — a US-listed pair (VTI + VXUS) and an Irish accumulating pair (an S&P 500 / US-total line plus an ex-US line), and a single FTSE All-World accumulating line — extract from the **audited annual report and prospectus**, not from marketing material: TER, accumulation policy, domicile, and the **actual withholding tax suffered** as a fraction of gross income.
2. Publish the recurring-cost table: blended TER, US-leg withholding, **ex-US-leg investor-level withholding**, total, and the RNOR and ROR after-tax core return. Show the ex-US double-withholding line explicitly — it is the largest single item.
3. Publish the **estate table**: US estate tax on US-situs values of $60k / $100k / $200k / $500k / $1M against the $60,000 exemption and the graduated schedule, and the resulting percentage of book at risk.
4. Publish the **ROR-cliff table**: annual Indian dividend tax and Form 67 burden under a distributing wrapper versus zero under an accumulating wrapper, and the conversion of the dividend leg into a 13.0% capital gain.
5. Publish the **LSE dealing cost** of the chosen line at the desk's actual clip size, amortised over a 20-year hold.

### Exit

Measured recurring wrapper saving **≥ 15 bps/yr** (N9) against the naive US-listed core, **and** a documented path to **zero** US-situs exposure on the core. Working expectation: **23.5 bps/yr** plus removal of a **24.5%-of-book** estate tail at $500k.

### Stop

Saving < 15 bps/yr **and** the estate path unavailable → the domicile switch is not worth the transaction; the core stays US-listed under the **$60,000 situs cap** plus a **W3-priced tail**, and the receipt rule and the 24-month discipline survive unchanged. This is a degraded pass, not a programme closure.

---

## W1 — Broker eligibility, and the written opinion

### Why

The entire rung-2 verdict is unexecutable if no accessible broker will hold Irish accumulating UCITS for an India-resident client, and the entire rung-1 model rests on statutory readings that this programme has labelled **working**. Both are answerable now, one for free and one for four figures, and **R1 is irreversible.** This is the milestone where this desk's spend discipline differs from the US-person desk's: **the first authorized purchase is an advisor, not data.**

### Build

1. **In writing from the broker:** under which entity the account is held; whether LSE/Euronext-listed Irish-domiciled UCITS ETFs are tradeable and holdable in that account for an India-resident client; whether any PRIIPs/KID restriction applies; whether the USD line can be bought with already-held USD with no FX leg; whether US Treasury bills can be held directly; and confirmation that W-8BEN is on file with the Indian PAN and the withholding rate actually applied to the last dividend (verify against the 1042-S — **if the applied rate is 30%, the form is broken**).
2. **Written cross-border tax opinion**, ceiling $1,500–$3,000, covering exactly and only: (a) the DTAA Art. 10 rate for an individual beneficial owner — 25%, not 15%; (b) that passive US portfolio income received in a US account is outside Indian tax during RNOR; (c) whether a pre-ROR sale-and-repurchase basis step-up is supportable, including GAAR; (d) Irish CAT treatment of UCITS units held by a non-Irish-resident, non-domiciled holder; (e) whether the 1953 India–US estate convention has any surviving effect on the $60,000 exemption; (f) situs of listed derivatives; (g) Schedule FA / FSI obligations during RNOR and at the transition; (h) Indian characterisation at ROR of futures P&L and of high-turnover equity P&L.
3. FEMA note in writing: that reinvestment **within** existing foreign assets held from an NRI period is permitted and is not an LRS remittance.

### Exit

Broker confirms UCITS eligibility in writing **and** the last dividend was withheld at 25%; the opinion supports items (a), (b), and (c) at least to a "more likely than not" standard.

### Stop

No broker will hold UCITS → degraded path per W0's Stop. The opinion does not support (c) → **R1 is dropped**, R2's standing 24-month discipline survives, and the programme loses its single largest number. **Do not execute R1 on an agent's reading of a statute.**

---

## W2 — Synthetic versus physical ($0)

### Why

A swap-based UCITS on a **qualified index** can recover most of the residual 15% fund-level US withholding, because the qualified-index exception keeps it outside IRC 871(m) (**working**). That is worth 10–20 bps/yr on the US leg, for free, and it is measurable from published NAV history. It also introduces counterparty risk and a regulatory dependency, so it is gated, not assumed.

### Build

Measure the **tracking difference** of a swap-based S&P 500 UCITS against the physical equivalent and against the index **gross** total return, over the longest common published history (≥ 5 years), annualised. Read the counterparty list, the collateral policy, and the per-counterparty exposure cap from the prospectus and the latest holdings disclosure. Document the reliance on the 871(m) qualified-index exception and what happens if it is withdrawn.

### Exit

Measured advantage over physical **≥ 10 bps/yr** over ≥ 5 years, **and** per-counterparty exposure ≤ 10% of NAV, **and** the 871(m) reliance is documented → the synthetic line is permitted at **≤ 50% of the US leg**, with the physical line holding the remainder.

### Stop

Advantage < 10 bps/yr, or counterparty concentration above the cap, or the 871(m) exception is materially in question → **physical only.** The core is not degraded by this; it simply keeps its 13.7 bps drag.

---

## W3 — Price the estate tail ($0 to quote)

### Why

The $60,000 situs cap is what limits the only surviving alpha candidate to a **12%** sleeve weight at $500k, and at 12% the measured PEAD bound cannot clear N2. **This is the one lever that changes that, and pricing it costs nothing.** It is published here, before E0's peek, so that using it later is a pre-registered branch and not a goalpost move.

### Build

Obtain real quotes for term life cover sized to the W0 estate table at the sleeve's target US-situs exposure (indicatively $150k–$250k of cover for a 25% sleeve on a $500k book). Establish in writing: that the policy is enforceable and payable in time to fund a Form 706-NA liability; the jurisdiction and insurer; the annualised premium as basis points of the total book. Compare against the alternative of simply forgoing the sleeve.

### Exit

Annualised premium **≤ 10 bps/yr of the book**, and enforceability documented → the situs cap lifts from $60,000 to the insured amount, the permitted sleeve weight rises to **25%**, and the premium is charged to the sleeve as a cost in E2.

### Stop

No acceptable quote — health, jurisdiction, insurable interest, or price above 10 bps → **the cap stays $60,000**, the permitted weight stays 12%, and **Book E is expected to close on N2.** Record that the killing rung for the desk's only alpha candidate was **estate situs**, not alpha.

---

## R0 — Embedded-gain and cliff-date ledger ($0)

### Why

This produces the single most important number on the desk: what the pre-cliff basis step-up is actually worth **for this portfolio**. Until it is computed, the programme cannot rank its own milestones.

### Build

From broker statements and the investor's own records, build a complete lot ledger: acquisition date, USD cost, current USD value — **and the INR cost at the RBI/prescribed rate on the acquisition date and the current INR value**. Publish: total USD unrealised gain; total **INR-measured** unrealised gain; the FX-accretion component separately; the tax that would be due at 13.0% if the book were sold after the cliff; and the same at ~31.2% for any lot that would be under 24 months at that point. Publish the documented RNOR expiry date from `residency` and therefore the **last tax year in which R1 can be executed.**

### Exit

The step-up is worth **≥ 100 bps of capital** (N9). Working illustration, to be replaced by the real number: a book bought at USD 200k, now USD 400k, with INR at ~62 then and ~92 now, carries ~₹2.44 crore of INR-measured gain — of which ~₹0.60 crore is pure FX accretion — worth **~₹31.7 lakh ≈ USD 34,500 ≈ 863 bps of capital** at 13.0%. A book with only 30% embedded gain is nearer **390 bps**.

### Stop

Below 100 bps → the one-time step-up is not worth the transaction cost and the opinion; **R2's standing discipline is retained regardless.** This is the likely case only for a freshly funded account.

---

## R1 — Step-up execution (the only date-bound milestone)

### Why

During RNOR a realised gain on a US listed security is taxed at 0% by the US (871(a)(2)) and 0% by India (not received in India, not India-source, not from an India-controlled business). Selling and repurchasing inside an RNOR tax year erases the accumulated gain — **including the FX accretion** — from both systems permanently, and restarts the Indian 24-month clock from a fresh high basis. **No wash-sale rule in either regime is violated: the US rule does not apply to a gain, and India has no IRC 1091.** The action expires with the window.

### Build

Execute the sale and repurchase **as one combined transaction with the W0 domicile migration**, so the desk crosses the spread once rather than twice: sell the existing (US-listed) holdings and buy the Irish accumulating USD line. Sequence and evidence:

1. Confirm from `residency` that the current Indian tax year is an **RNOR** year, in writing, before the first order.
2. Confirm the W1 opinion supports the step-up.
3. Route **all** proceeds to the **US** account. `receipt` blocks anything else. No Indian account touches this transaction.
4. Execute in clips sized to the LSE/US venue depth, with limits, away from the open and close; RFQ where the clip exceeds displayed size.
5. Freeze the pre-transaction lot ledger and the post-transaction lot ledger, both timestamped, both retained permanently.
6. Verify that the post-transaction `situs` reading is **$0** of US-situs equity (or ≤ $60,000 if the degraded US-listed path is in force).

### Exit

Executed inside a documented RNOR tax year; **zero** Indian receipt; the lot ledger shows fresh basis on every lot with a new 24-month clock; the post-transaction situs reading is within N5; the realised USD and INR gain figures are recorded for the R0 file. **This is a wrapper transaction, explicitly authorized before L0 under Lock 7 — a later agent must not block it as "live capital before a book passes."**

### Stop

The RNOR year has closed, or the opinion does not support the action → **R1 is not executed and is not retried on a later reading of the statute.** Post a STOP memo recording the value forgone. R2 continues.

---

## R2 — Standing realisation schedule

### Why

The step-up is once. The 24-month line is forever, and it is worth **1,820 bps of realised gain** every time a sale crosses it.

### Build

Permanent rules in `books.realise`, enforced pre-trade: no voluntary sale of a lot inside 24 months of acquisition unless the sale clears the ~31.2% slab rate on its own merits; **band rebalancing after the cliff is done with new cash flow, never with an MES overlay and never with a sale** (an overlay converts a deferred 13.0% into a realised 31.2%); Indian set-off and 8-year loss carry-forward tracked; Schedule FA and Form 67 artefacts generated from the lot ledger once ROR. **Tax-loss harvesting is deferred, not adopted** — it has zero value during RNOR because there is no capital-gains tax on either side for a loss to offset, and after the cliff a buy-and-hold desk realises no gains for the loss to work against. **Book C's 35.5 bps is not imported and no harvesting number is claimed on this desk.**

### Exit

Rules in code, unit-tested, and demonstrably blocking an in-window sale. No numeric exit — this is a permanent discipline.

### Stop

None. R2 survives every other closure in this plan.

---

## U0 — Universe and point-in-time panel (listed)

### Why

Survivorship bias is the most common cause of a fake equity backtest. This makes the listed panel honest and the leakage tests real. **This desk inherits the US-person desk's U0 artefacts** — the EDGAR identifier panel, the corporate-action fixtures, the leakage test — and adds nothing except the wrapper metadata Book W needs.

### Build

Reuse the listed PIT identifier panel for US common stock and ETFs, 2005–2026, with delisted and renamed names from EDGAR Form 25/15. Add to `universe`: **domicile, accumulation policy, replication method (physical/synthetic), and situs class** per fund. Delisted *prices* remain deferred to E1.

### Exit

The listed panel round-trips a known index-membership snapshot; the leakage test shows no future information reachable from any row's knowledge date; delisted identifiers are present even where price series are empty; every fund in the core candidate set carries a domicile, accumulation, replication, and situs flag.

### Stop

Delisted prices later unobtainable at acceptable cost → **Book E closes; W and R proceed** (neither needs single-name history).

---

## H0 — Inference design for this desk

### Why

Decide what is measurable **before** looking. On this desk that decision has a consequence the US-person desk did not face: it determines whether the tax-free RNOR window can host a strategy at all.

### Build

For each candidate book on **this** desk, publish the bet definition, n per year, estimated σ per observation, the clustering haircut, and **MDE = 2.8σ/√n**. Include the rows that close branches:

| Book / shape | n | σ | Hypothesized | MDE | Ratio | Gate |
|---|---|---|---|---|---|---|
| Book W (wrapper arithmetic) | 1 household | 0 | 15 bps/yr | 0 | 0 | **pass** (accounting, not statistical) |
| Book R (step-up arithmetic) | 1 household | 0 | 100 bps of capital | 0 | 0 | **pass** (accounting) |
| Book E (event panel, 2010–2026 history) | 30,000 → 6,000 after 5× cluster | 800 bps | 100 bps/event | **28.9 bps** | 0.29 | **pass** |
| **Any monthly sleeve measured live inside the RNOR window** | 36 | 300 bps | 300 bps | 140 bps | 0.47 | window ends before the sample completes |
| **Any 12-cycle option sleeve inside the RNOR window** | 36 | 150 bps | 116 bps | **70 bps** | **0.60** | **CLOSED without a peek** |
| **Long-horizon factor-tilt comparison** | 15 annual | 600 bps | 150 bps | **434 bps** | **2.89** | **CLOSED as a measurable book**; permitted as a ≤ 20% no-alpha-credit tilt |

Also build: purged and embargoed walk-forward splits; a trial ledger with pre-registered specs; deflated Sharpe; and a `harness` guard that raises unless n, σ, and MDE have been printed for the current spec.

### Exit

MDE published for every candidate book; at least one book clears MDE ≤ 0.5 × its effect; the harness guard demonstrably blocks an undeclared test; **the RNOR-window rows are published and their closures recorded.**

### Stop

No book clears the ratio → **the alpha branch stops at H0 with zero data-mining risk incurred.** W and R stand. This is a legitimate and inexpensive outcome.

---

## E0 — Book E: re-gate PEAD at ROR rates ($0)

### Why

PEAD is the only alpha candidate on this desk with an inference budget that supports honest discovery. The US-person desk's screens are **pre-tax**, so they transfer as measured — but the housing that made the sleeve work (an IRA) does not exist here, and the sleeve's weight is capped by estate situs rather than by contribution room. **Re-tax and re-cap before spending a dollar.** This is a kill screen, not E1: Lock 5 still requires delisted prices.

### Build

MDE printed first. Take the imported measurements — B0 listed mid-cap 20-day net **80.9 bps** (n=17,143, survivorship-biased); B0.5 Item 2.02 **82.3 bps** (n=13,907); missing-tape weight **w = 12.9%**; **zero-drift bound 71.7 bps** — and publish, for **this** taxpayer:

1. The effective kill threshold: the US-person desk's 40 bps net-of-cost becomes **40 / (1 − 0.312) = 58 bps** once ROR slab tax applies to a 5–40 day hold. Bound vs threshold: 71.7 / 58 = **1.24×** (the US person's was 1.79×).
2. The sleeve arithmetic at both tax regimes. Working: sleeve alpha ≈ 71.7 bps × 12.6 cycles/yr ≈ **903 bps/yr**; sleeve gross total ≈ 16.03%; **at RNOR, tax 0 → sleeve excess over the 6.74% core ≈ 929 bps**; **at ROR, 31.2% on all of it → sleeve net 11.03% → excess ≈ 429 bps.**
3. The situs-capped book-level excess: **51 bps at w = 12%** (below N1's 60) and **107 bps at w = 25%** (above it, and only reachable if W3 passed).
4. A note that at ROR the sleeve also pays slab tax on its **INR-measured** FX gain annually while the core defers it — which moves the comparison further against the sleeve and is not counted as a credit to it.

### Exit

Survivorship-corrected bound **≥ 58 bps/event after ROR tax** (working: 49.3 bps after tax against a 40 bps after-tax kill, i.e. the **pre-tax** bound of 71.7 against a 58 bps pre-tax threshold — 1.24×) **and** a permitted sleeve weight that can deliver N1. Given W3's outcome, one of two verdicts is recorded:

- **W3 passed (w = 25%):** book-level excess ≈ 107 bps > N1's 60 → **E1 authorized.**
- **W3 failed (w = 12%):** book-level excess ≈ 51 bps < N1's 60, and sleeve excess 429 bps < N2's 500 → **Book E closes at $0.**

### Stop

Bound below 58 bps after ROR tax, or the situs cap holds at $60,000 → **Book E closes. No Norgate, no Polygon, no Sharadar, and the programme proceeds to L0 in its 100%-core form.** This outcome is pre-registered here and is not a failure: it records that the binding constraint on this desk's only alpha candidate is **US estate-tax situs**, a rung-2 fact, and not alpha.

---

## E1 — Book E: PEAD existence (PIT panel)

### Why

The only book on the desk where discovery is statistically legitimate, and the most likely to be already arbitraged. **Cannot certify at $0:** Lock 5, and listed-only free sources do not keep delisted quotes.

### Build

**SKU, only if E0 cleared:** Norgate US Stocks Platinum, **3-week free trial first.** Subscribe **6 months at $346.50**, dump, cancel, **only if** the trial panel is complete (delisted EOD plus historical index constituents, Python-usable, 2010–2026). **Check first whether the US-person desk has already bought this panel for its B1 — if so, reuse the dump and spend $0.** Do not default to Polygon (Developer is 10 years against a 16-year window; Advanced is $199/mo with spotty delisted coverage). Event panel from EDGAR 8-K Item 2.02 filing timestamps joined to the PIT price panel, 2010–2026, $ADV > $20M, surprise proxy from the announcement-window return only (no vendor consensus). Pooled forward returns at 5/10/20/40 days, net of modelled cost, **reported at both RNOR and ROR rates**, with date and sector clustering, purged walk-forward, and controls for momentum and size. MDE printed first.

### Exit

Net-of-cost drift **≥ 58 bps/event after ROR tax**, present in the $20–100M ADV band and not only in the illiquid tail, sign-stable across walk-forward folds.

### Stop

Below 58 bps after ROR tax, or the effect is concentrated below $20M ADV, or it is fully explained by momentum and short-interest controls → **Book E closes. No vendor fundamentals are purchased.**

---

## E2 — Book E: economics, situs sizing, and the AI increment

### Why

A drift is not a book. Establish that the sleeve fits inside the estate cap at a weight that delivers N1, that it clears N2 **at ROR rates**, and that text features earn their complexity.

### Build

Only if E1 passed. Authorize a PIT fundamentals/consensus subscription. Build `ai.extract` for guidance-change and call-language features with strict pre-timestamp inputs, cached and versioned. Report the sleeve **three ways** — numeric surprise only, numeric + text, text only — and **at both tax regimes**. Model the situs cap explicitly as a position-level constraint, not a portfolio note, and charge the W3 premium to the sleeve as a cost. Blend the sleeve with the core at 8%, 12%, and 25% weights.

### Exit

Sleeve after-cost, after-**ROR**-tax excess over the rebuilt core **≥ 500 bps/yr** (N2) at the permitted weight; the resulting book-level excess ≥ **60 bps/yr** (N1) with excess Sharpe ≥ 0.5; text features add **≥ 10 bps per event** over numeric surprise on held-out folds; the sleeve's peak US-situs exposure stays inside N5; book max drawdown ≤ the core's over the same window.

### Stop

Sleeve excess below 500 bps at ROR → **Book E closes.** Text adds < 10 bps → remove the AI layer and re-test numeric-only against the same exit. Situs exposure cannot be held inside N5 at the weight N1 needs → Book E closes. **Do not re-optimise the holding window or the surprise definition outside the trial budget.**

---

## E3 — Book E: tradability

### Why

Mid-cap fills are where PEAD backtests die.

### Build

60 sessions of paper trading via the closing auction (MOC/LOC) at target size. Log intended versus achieved price per name. Measure realised round-trip cost per ADV bucket and the drift decay caused by entry timing. Feed realised slippage back into `costs` and re-run E2.

### Exit

Realised round-trip cost ≤ 25 bps in the traded bucket; auction-timed entry preserves ≥ 85% of the modelled drift; E2 still passes on recalibrated costs.

### Stop

Either fails → **Book E closes.**

---

## L0 — Operating loop

### Why

Build the operating machinery only for what has already passed. Ops before alpha is how retail desks spend two years building infrastructure for a strategy that never existed. **On this desk L0 is reached in one of two very different shapes, and both are legitimate.**

### Build

Daily instruction-list generator (dry-run first, diffed against live positions); broker order adapter with limit/MOC/LOC and an LSE RFQ path for the core, plus the kill switch; **`situs` pre-trade block and `receipt` assertion wired into the order path, not the report**; PDT counter and margin pre-check; fill audit of intended versus actual; daily P&L reconciliation against broker statements; **USD lot ledger with INR conversion at the prescribed rate**; after-both-tax attribution against the N0 benchmark series; and — once ROR — **Schedule FA and Form 67 draft artefacts generated from the ledger.** Deploy at 10% of target size for 60 sessions, then full size.

### Exit

60 consecutive sessions with zero unexplained reconciliation breaks, **zero situs-cap breaches, zero non-US receipts**, zero PDT violations, kill switch verified in a drill, and live after-cost tracking within 30 bps/yr of the E2 model.

### Stop

No book passed N2 → **global STOP, and it is the expected outcome.** Post the STOP memo. The desk holds 100% accumulating Irish UCITS core under the situs cap, the receipt rule, and R2's realisation schedule. **That posture still delivers 23.5 bps/yr of avoided wrapper leakage, the one-time R0-measured step-up (working illustration: 300–860 bps of capital), removal of a 24.5%-of-book US estate tail, and permanent elimination of annual Indian dividend tax and FTC filing — for zero research risk and $0 of vendor spend.** Reopen only with new data.

---

## X0 — Kill and residency review

Standing quarterly gate once live: any book missing its N9 minimum over four rolling quarters is retired automatically and its capital returns to the core. No new debate required.

**Plus, annually and non-negotiably:** re-run `residency`. Confirm the Indian residency status for the coming tax year, the US physical-day count for the calendar year, and whether the ROR transition has occurred. **On the first ROR year, re-run every live book's economics at ROR rates and retire anything that fails N2 at those rates.** A book that was passing at RNOR rates and fails at ROR rates is retired on the day the status changes, not at the next quarterly review.

---

## Critical path, stated plainly

**R0 and W0 run now, in parallel, at $0.** They produce the two numbers that rank everything else: what the step-up is worth, and what the wrapper is worth. **W1 buys the opinion** — the first and most important purchase on this desk, and not a data SKU. **W2 settles physical versus synthetic at $0. R1 then executes the combined domicile migration and basis step-up inside a documented RNOR tax year**, and it is the only milestone on this desk with a deadline. **R2 makes the 24-month discipline permanent.**

Only then does the alpha branch open: N0 completes the cost and situs modules, U0 inherits the listed panel, H0 publishes this desk's MDEs and closes every window-only book without a peek, **W3 prices the estate tail** — which is what decides whether an active sleeve can be large enough to matter — and **E0 re-taxes the imported PEAD screens at ROR rates against a 58 bps threshold.** E1 is the only milestone that may spend on data, at most $346.50, and plausibly $0 if the US-person desk buys the same panel first.

The single largest **scheduling** risk on this desk is not building L0 early. It is **letting the RNOR window expire while the programme debates alpha.** The step-up is worth more than any book on the menu, it is deterministic, it requires no forecast, and it cannot be recovered once the window closes. The plan is ordered accordingly.

The single largest **spend** risk is buying an options tape because a name in the US-person desk's history suggests one. **Book V is closed on a pre-tax measurement — 1.19× against a 2× hurdle — and the §1256 subsidy that once ranked it is worth exactly zero to this taxpayer.** Do not buy it, and do not reopen it on a tax story.
