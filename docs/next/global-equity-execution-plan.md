# Global programme — Execution Plan

| | |
|---|---|
| **Date** | 2026-09-14 |
| **Status** | **BLUEPRINT Rev 1.0 / DRAFT** |
| **Review** | Claude Opus |
| **Authority** | Implements [global-equity-architecture-blueprint.md](global-equity-architecture-blueprint.md) **Rev 1.0**. Where this plan and the blueprint differ, the blueprint governs |
| **Product authority** | [global-financial-market-analysis.md](../archive/global-financial-market-analysis.md) (2026-09-14). Verdicts consumed, not reopened |
| **Taxpayer** | [investor-profile.md](../investor-profile.md) · calendar [residency-calendar.md](../residency-calendar.md) |
| **Goal** | Protect the alien desk's measured **240 bps** step-up across a settlement cliff, make one Indian return computable from two currencies, and keep the disclosure surface and venue count from growing — at **$0** of new spend and **$0** of new strategy capital |
| **Milestone IDs** | **GL0–GL5.** They are not M0–M7 (India Rev 2.0), not N0/W/R/E (alien US), and not `g0-charter.md`…`g3-charter.md` (unrelated) |

---

## How to read this plan

A **milestone map, not a peek charter.** Four fields per milestone:

- **Why** — the question it answers. If you cannot state the question, do not start.
- **Build** — the artefacts, and nothing beyond them.
- **Exit** — a numeric or documentary condition. Not "looks reasonable".
- **Stop** — the condition that closes the branch, plus the STOP memo path in `docs/archive/`.

Three rules specific to this programme:

1. **This programme emits no orders and holds no capital.** It writes rules and numbers into the two existing desks. Where an action results, the owning desk executes it.
2. **Nothing here is statistical.** No milestone authorizes a peek at a strategy result, because no global book has an n. `harness` is untouched.
3. **A STOP memo is a completed milestone.** The expected end state of this programme is four small facilities and a registry, and that is a success.

**The ordering principle: the calendar comes first, because it is the only thing that expires.** GL0 protects 240 bps on a date. Everything else can wait, and most of it should.

---

## Non-negotiable locks

| # | Lock |
|---|---|
| **1** | **No new adapter.** No third broker, no fourth venue, no third run loop, no fourth OMS. India demat, US/LSE brokerage and listed derivatives are different adapters; LSE is already on the alien adapter |
| **2** | **No capital transfer between the two books.** No cross-margining, no LRS bridge, no repatriation-as-strategy, no netting. `household` has no transfer primitive and `portfolio` refuses one |
| **3** | **GL-L1 — no new INR funding.** Every global instrument is buyable from already-held USD under FEMA s.6(4) |
| **4** | **GL-L2 — no new venue** unless it clears **≥ 25 bps/yr net of market-data and FX cost at the $25,000 floor** |
| **5** | **GL-L3 — no new tax jurisdiction** and no third-country filing obligation |
| **6** | **GL-L4 — fewest Schedule FA lines.** Additions need GL-H7 (≥ 10 bps/yr of the USD book, or a named non-return reason) **and** a dated allocation instruction. The core configuration choice is exempt: it is composition |
| **7** | **`costs`, `tax`, `situs`, `receipt`, `residency`, `household` and `settlement` are single, unit-tested modules.** No book re-implements any of them. `tax` takes a residency calendar, not a rate |
| **8** | **N5, N6, N8, N3, N7, N9 and India R0–R7 plus inherited H1 / H4 / H5 / H6 are unchanged.** The GL series intersects them and never relaxes them. If a GL statement ever differs from an N, R or H statement, the desk statement wins |
| **9** | **$0 of new spend.** No paid data SKU, no market-data subscription, no vendor. The only nearby purchase is the alien desk's already-authorized **W1** written opinion ($1,500–$3,000), whose scope this programme widens without adding money |
| **10** | **No live strategy capital is authorized by this programme — $0 and ₹0.** The wrapper transactions (domicile migration, basis step-up) remain **alien-owned** under that plan's Lock 7 |
| **11** | **No predictive global book and no global pre-registration.** Every global premium fails MDE by 4.8×–15.8×; listing-basis is measured **negative**. Reopening needs a named trigger from the blueprint §13, not a new specification |
| **12** | **AI does not forecast a return and does not produce a tax conclusion.** Rule 115, s.75 CATCA 2003, FEMA Reg 7 and the s.198 set-off question are **W1 written-opinion items only** |
| **13** | **Optional sleeves default to weight 0.** Duration UCITS and gold ETC are registry entries, not books. The platform never allocates |
| **14** | **Report every result at RNOR and at ROR. ROR governs.** An RNOR-only number is not a result |
| **15** | **Poetry only.** No HMM, LightGBM, MLflow, Kaggle or Polars enters `pyproject.toml` for this programme |
| **16** | **Do not implement India Rev 1.0.** It is superseded. India Rev 2.0 is **ACTIVE**. From the US-person desk, import **pre-tax friction only** |
| **17** | **Do not reopen a closed product.** The registry is the analyst's verdict list. A closed row reopens only on its own named trigger |

---

## Milestone map

| ID | Name | Status | Hard stop if… |
|---|---|---|---|
| **GL0** | Cliff, settlement and session calendar · **$0** | Not started | The receipt date for a March-2028 trade cannot be derived with certainty → R1 is not armed and the alien desk is told so in writing |
| **GL1** | Household join ledger + Book J value · **$0** | Not started | `household` cannot reproduce both desks' ledgers to ₹1 / $0.01 → no join claim is made; the ledger is fixed before anything reads it |
| **GL2** | Book Q — core composition disclosure · **$0** | Not started | The chosen configuration is not recorded before the wrapper migration → the migration proceeds on an undocumented composition, which is the failure this milestone exists to prevent |
| **GL3** | Book K — post-cliff cash sleeve · **$0** | Not started | Sleeve < $50,000 or saving < 30 bps/yr → hold T-bills |
| **GL4** | Book S — synthetic on non-US legs · **$0** | Not started | < 10 bps/yr over ≥ 5 years, or any counterparty > 10% NAV → physical |
| **GL5** | Join operating hooks and standing review · **$0** | Not started | Standing. Retires an item rather than stopping |

```
GL0 ──────────────► feeds alien R1 (date) and execute (windows)
 │
 ├─ GL2 ──────────► must close BEFORE the wrapper migration (alien W1/R1)
 │
 ├─ GL4 ──────────► rides alien W2's existing gate
 │
 ├─ GL1 ──────────► live before 1 Apr 2028; may wait until near the cliff
 │                   │
 │                   └─ GL3 ──► on/after 1 Apr 2028 (ROR instrument)
 │
 └─ GL5 ──────────► standing, once L0 / R2 exist
```

**Critical path, stated plainly.**

1. **GL0 runs now.** It is the only date-bound work, it costs nothing, and **Book T must exist before alien R1** or R1 runs blind into a settlement question worth 240 bps.
2. **W1's scope is widened now, before it is bought** — the custodian question, FEMA s.6(4) + Circular 90 + Reg 7, s.75 CATCA 2003, Rule 115 / TT rate, and the s.198 set-off question. This programme adds scope, not money. **If the custodian cannot deal LSE, an account transfer precedes R1 and becomes the critical path.**
3. **GL2 closes before the wrapper migration.** It is two KIIDs and a spreadsheet, and the composition it records is irreversible once the migration runs.
4. **GL4 rides W2.** The gate already exists; this only widens the input set.
5. **GL1 can wait until near the cliff**, but must be live before **1 Apr 2028**, because Book J has no content until both desks are taxable in the same return.
6. **GL3 is a ROR instrument.** It is worth exactly **0 during RNOR** and must not be built early to look busy.

---

## Research spend ladder

| Step | Spend | What it buys |
|---|---|---|
| GL0, GL1, GL2, GL3, GL4, GL5 | **$0** | Exchange holiday calendars, settlement-cycle notices, fund KIIDs and audited annual reports, LSE published spreads, RBI circulars, FEMA rules, Irish and Luxembourg statutory texts, broker fee schedules, both desks' own lot ledgers |
| Nearby, **already authorized elsewhere** | $1,500–$3,000 | The alien desk's **W1** written cross-border opinion. This programme **widens its scope and adds no money** |
| Closed | — | Any market-data subscription for a new venue · any global panel or premia dataset · any vendor fundamentals · any options tape |

**Programme spend ceiling: $0. Spend to date: $0.** A new venue subscription is not a data purchase decision, it is a **GL-L2 breach** — $30/month is **144 bps/yr at the $25,000 floor**, more than the entire wrapper saving the desks are being rebuilt to capture.

---

## GL0 — Cliff, settlement and session calendar ($0)

### Why

One item on this board has a deadline and 240 bps riding on it. The alien desk's step-up is **trade-dated**; the receipt is **settlement-dated**, and N6 governs the receipt. A trade in the last days of March 2028 settles in FY 2028-29, when the taxpayer is ROR — which would hand India a taxable receipt on a transaction whose entire purpose was to avoid one. Nobody currently owns the cycle arithmetic that decides this. It is free, it takes days, and it cannot be recovered later.

### Build

1. **`src/settlement.py`** — one job per function, no I/O in the arithmetic:
   - `receipt_date(trade_date, venue) -> date` for India **T+1**, US **T+1**, LSE **T+2** with a switch to **T+1 targeted 11 Oct 2027 (working, G20)**.
   - `latest_safe_trade_date(cliff, margin_days=14) -> date` — working answer **17 Mar 2028 (GS1)** against the working cliff **31 Mar 2028 (Friday)**, consumed from `residency`, **not redefined here**.
   - `straddles_cliff(trade_date, venue, cliff) -> bool` — the assertion R1 must pass before it arms.
   - `session_window(exposure_class, date) -> (open, close)` — **14:30–16:20 London** for US-exposure lines, **14:30–15:30** for ex-US developed lines, **13:30** start in DST-gap weeks (GS9), with the UK BST switch on **26 Mar 2028** and the US EDT switch on the 2nd Sunday of March.
   - Exchange holiday tables for LSE and NSE covering the final week of March 2028 (G20).
2. **`src/execute.py` extension** — the windows enforced per exposure class as a **refusal with a logged, reasoned override**, plus the precedence order: **N6 receipt → N5 situs → GL-H3 cliff margin → session window.** The cliff calendar outranks the window; the receipt and situs blocks outrank everything and have no override.
3. **`src/situs.py` extension** — UK-situs and Irish-CAT classes beside the existing US-situs classifier. `uk_register = true` (UK-incorporated shares) is a refusal. **The $60,000 US cap is untouched and remains N5.**
4. **`src/costs.py` assertion** — a test that fails if a new venue bucket is added without a recorded GL-H4 pass. The USD-line zero-FX assertion already exists and stays.
5. **`src/ops.py` extension** — the idle-offshore-cash day counter (alert **120**, limit **180**, GS7) and GL calendar items.
6. **`docs/archive/gl0-cliff-calendar.md`** — the dated artefact: the cliff, the latest safe trade date, the settlement cycle in force, the March-2028 holiday and BST facts, the sell-to-repurchase gap rule (**≤ 5 business days**, GS2), the session windows, and the venue-fee arithmetic (**$360/yr = 144 bps at the floor, 10.2 bps at the marked book, 7.2 bps at $500k**, GS6). Resolves register items **G8, G9, G10, G11, G18, G19, G20, G21, G23, G25, G26** and the GL0 rows of **G14**.

### Exit

- `receipt_date` unit-tested against every venue cycle and both sides of the 11 Oct 2027 switch; `straddles_cliff` demonstrably returns `true` for a 30 Mar 2028 LSE trade at T+2 and `false` at the published latest safe trade date.
- The latest safe trade date is published, with **≥ 14 calendar days** of margin, and confirmed against the March-2028 holiday calendars.
- `execute` demonstrably **refuses** a US-exposure order at 11:00 London and demonstrably **allows** it under a logged cliff-margin override.
- `situs` demonstrably refuses a UK-register instrument; `costs` demonstrably fails on an unauthorized venue bucket.
- The idle-cash counter runs and alerts at 120 days on a synthetic balance.
- **The artefact is handed to the alien desk in writing** as an input to R1.

### Stop

If the receipt date for a March-2028 trade cannot be derived with certainty — an unresolved cycle, an unpublished holiday calendar, a settlement-switch date still moving — **do not guess.** Publish the uncertainty, widen the margin, and tell the alien desk that **R1 is not armed**. `docs/archive/gl0-stop.md`. Losing 240 bps to an assumed settlement date is the single most expensive avoidable error available to this household.

---

## GL1 — Household join ledger and Book J ($0)

### Why

From FY 2028-29 one Indian return carries both books. Indian set-off does not care which currency produced a loss, so a loss on one desk can shelter a gain on the other — and **no single-desk document can see it**, because each desk sees one currency. Separately, and regardless of whether Book J passes, **Schedule FA and Form 67 need an INR-native ledger spanning both books**, and a ledger cannot be reconstructed retrospectively.

### Build

1. **`src/household.py`** — the shared join ledger, a single source in the sense `costs` and `tax` are:
   - Derived by **reading** each desk's lot ledger. Reproduces the India ledger to **₹1** and the alien USD ledger to **$0.01** (GS8). The desks' ledgers stay authoritative; the broker statement and the 1042-S remain authoritative for filings.
   - INR-native, with the **12-month Indian line** and the **24-month foreign line** as separate clocks that never contaminate each other.
   - **Per-lot conversion-rate source and date**, so the Rule 115 / TT-rate basis (G4) is swappable and a change in W1's answer is a re-run, not a rebuild.
   - The **Schedule FA line register** (count in force, GS10) and the **total-India-exposure line** across both currencies.
2. **`src/tax.py` extension**, single source, unchanged elsewhere: INR-measured foreign gain from the household ledger; the named rate basis; cross-book set-off at ROR with the **8-year** carry; no third jurisdiction. Unit-tested against hand-worked examples at **RNOR and at ROR** and across the FY 2027-28 → FY 2028-29 transition.
3. **`src/books/set_off.py`** — Book J: the measured set-off value at ROR, and the realisation-**ordering** rule. Per unit of gain, realising in the USD book costs more than realising in the INR book, because the 13.0% applies to the INR-measured gain and INR depreciation is itself a taxable gain. That is a **sequencing** fact, **not** an argument to hedge and **not** an argument to reallocate.
4. **`src/ops.py` extension** — dual RNOR/ROR reporting on every join number; the FA line count in the daily artefact.
5. **`docs/archive/gl1-join-ledger.md`** — the measured Book J value against its kill line, both regimes reported. Resolves **G27**; records the open W1 dependency **G5**.

### Exit

- `household` reproduces both desks' ledgers to **₹1 / $0.01**, and a planted cross-clock error is caught by a test (**GL-H1**).
- `tax` reproduces the hand-worked transition-year case to **₹1** at both RNOR and ROR rates.
- Book J's measured value is published against **25 bps of combined capital** (≈ **₹97,000** at the marked books, GS3), with the G5 dependency stated.
- The Schedule FA line register and the total-India-exposure line exist and are populated.

### Stop

Book J below 25 bps → **fold the set-off rule into India Book S (Rev 2.0 tranche ledger; not global Book S) and alien Book R and close the book**, `docs/archive/gl1-book-j-stop.md`. **The ledger survives the closure** — Schedule FA and Form 67 need it either way. This closure is pre-registered here: at the marked books, the estimated ₹65,000–₹1.56 lakh straddles the ₹97,000 kill line, so Book J may well close, and its closure costs the household nothing it was counting on.

If `household` cannot reproduce both ledgers, **stop and fix the ledger** before anything reads it. A join ledger that is 90% right is worse than none: it will be believed.

---

## GL2 — Book Q, core composition disclosure ($0)

### Why

W0 records CSPX + XUSE as the chosen pair and VWRA as the permitted single-line substitute. **They are not the same portfolio.** XUSE tracks MSCI World ex USA — developed only, **no EM at all**. VWRA tracks FTSE All-World, EM at **~10% (working)**. The choice decides whether the USD book holds emerging markets, and downstream whether it holds India at ~1.1% of book. While the INR desk's Nifty sleeve stays at default **0**, that line may be **the household's only India equity**. The migration is irreversible; the disclosure costs nothing and must precede it.

### Build

Two KIIDs, a spreadsheet, and one line in `household`. **No module.** `docs/archive/gl2-core-composition.md` carrying:

1. The index each candidate line tracks, **confirmed from the KIID** (G12), and the EM weight.
2. The India weight: **~11.01% of MSCI EM** (justETF, Aug 2026) × EM ~10% of a global index → **~1.1% of the USD book ≈ $3,900 ≈ ₹3.7 lakh** at the marked $354,097 (G13). While INR β ≤ 0.10 this may be the household's only India equity; it is still **not worth a book** — worth one ledger line.
3. **The trade-off, handed back with both numbers on it and no recommendation:** the pair's measured **3.31 bps/yr** fee advantage (**$117/yr ≈ ₹11,000/yr**) against **one extra Schedule FA line** under a **₹10 lakh/yr** s.43 penalty regime (working), and against **holding versus not holding ~10% of world market capitalisation**. The fee axis favours the pair; the disclosure axis favours the single line; the composition axis is not a cost question. **GL-H7 does not apply to this choice** — the core configuration is exempt because it is composition, and composition belongs to the investor and the alien desk.
4. The chosen configuration, once the investor states it, **written into `household` and dated**.

### Exit

Both indices confirmed from their KIIDs; the India weight computed and written into `household`; the trade-off table published with both numbers; **and the investor's choice recorded and dated before the wrapper migration runs.**

### Stop

Book Q closes the moment the two KIIDs are read and the India weight is in the ledger — it is a disclosure, not a trade, and closing is the exit. `docs/archive/gl2-composition-note.md`. **The failure mode this milestone exists to prevent is a migration that runs before the composition is recorded.** If that happens, record it as a process failure in the memo and reconstruct the composition from the executed fills.

---

## GL3 — Book K, post-cliff cash sleeve ($0)

### Why

At ROR, USD cash held as deposits or directly held T-bills pays slab **~31.2% on interest every year**. The same economics inside an Irish accumulating USD ultra-short / T-bill UCITS distributes nothing and is taxed once, at 13.0% on the INR-measured gain, after 24 months. It is also unambiguously *invested* rather than idle, which is the cheap answer to the FEMA Reg 7 question. **It is worth exactly 0 during RNOR**, so building it early is busywork.

### Build

An extension of the existing **`src/books/wrapper.py`** — a cash-sleeve line beside the equity-core lines. **No new module.** Plus a registry entry in `universe` at **default weight 0**.

1. From published fund documents: the Irish accumulating USD ultra-short line's availability, TER (**0.07–0.10% working**), and minimum economic clip (**~$10,000**). Institutional MMF share classes at $100k–$5m minimums are **out of reach** and are not candidates (G15).
2. The arithmetic against the **actual** cash balance and yield: slab drag **125–170 bps/yr** versus a **~98 bps** accrual-equivalent further reduced by deferral → saving **30–70 bps/yr on the sleeve (working)** (G16). Reported at RNOR (**0**) and at ROR. ROR governs.
3. The FEMA half of the case, stated separately and not netted into the saving: an instrument satisfies the 180-day "reinvested, not idle" reading in a way a deposit may not.
4. **Confirm the alien desk's cash rule is extended, not contradicted:** never a **US** money-market fund (RIC shares are US-situs, N5). An Irish accumulating line is neither a US MMF nor US-situs.

### Exit

Sleeve **≥ $50,000** — note this is **14.1% of the marked book** (GS4) — **and** measured saving **≥ 30 bps/yr on the sleeve** at ROR → the registry entry is unlocked, still at weight 0 until a dated allocation instruction (GL-H11). Adding the line also requires **GL-H7**.

### Stop

Sleeve below $50,000 or saving below 30 bps/yr → **hold T-bills**, `docs/archive/gl3-book-k-stop.md`. **Pre-registered:** at a ~5% cash allocation on the marked book the sleeve is roughly **$17,700**, worth about **$100/yr**, and Book K fails its own floor. Record that outcome without apology — at that scale the FEMA argument is the larger half of the case, and directly held T-bills already answer it.

---

## GL4 — Book S, synthetic on the non-US legs ($0)

### Why

W2 passed synthetic over physical at **20.6 bps/yr** on the S&P 500 leg, where the mechanism is recovering residual 15% US withholding through a swap on a qualified index outside IRC 871(m). **That mechanism does not exist for World ex-USA, EM or bond legs** — any advantage there comes from the counterparty's own local withholding position and is smaller. The question is cheap and the gate already exists.

### Build

An extension of the existing **`src/books/synthetic.py`** to take a non-US underlying. **No new module and no new gate.**

Measure the tracking difference of a swap-based non-US line against its physical equivalent and against the index gross total return, over the **longest common published history (≥ 5 years)**, annualised. Read the counterparty list, collateral policy and per-counterparty exposure cap from the prospectus and the latest holdings disclosure. Working expectation: **5–15 bps/yr (G24)**, i.e. **below** the gate as often as not.

### Exit

Measured advantage **≥ 10 bps/yr over ≥ 5 years** **and** every counterparty **≤ 10% of NAV** → the synthetic non-US line is permitted on **W2's terms**, and **W2 owns the verdict**, not this programme.

### Stop

Below 10 bps/yr, or counterparty concentration above the cap → **physical only**, `docs/archive/gl4-book-s-stop.md`. The core is not degraded by this; it simply keeps its drag.

---

## GL5 — Join operating hooks and standing review ($0)

### Why

Two things must not decay: the enforcement surface, and the working-numbers register. Both are cheap to keep and expensive to rebuild.

### Build

1. **`src/portfolio.py` extension** — refuse an instrument absent from the registry; refuse a non-zero weight on an optional sleeve without a dated allocation instruction; **refuse any inter-book capital transfer.** These are refusals in the order path, not warnings in a report.
2. **`src/ops.py`** — the Schedule FA line register in the daily artefact; the idle-cash counter; the GL calendar items; dual RNOR/ROR reporting on join numbers; Schedule FA and Form 67 draft artefacts generated **from `household`**, with every number traceable to a ledger row and a human or CA signing.
3. **Standing review**, co-scheduled with the alien desk's **X0** and the India desk's **X0** rather than as a third meeting:
   - Re-verify the settlement cycle in force and the March-2028 calendar (until the cliff passes).
   - Re-verify the FA line count against the register, and the venue count against GL-L2.
   - Re-run Book J's value once realisation volume is real; retire it if it has fallen below 25 bps.
   - Walk the blueprint §13 trigger list as a **list**, not from memory.
   - Check every unresolved register item against its owner; an item past its milestone is either resolved or the dependent claim is **withdrawn**.
   - Measure the LSE USD-line spread inside versus outside the overlap window against own fills (**G22**), which complements alien N4 and needs live fills to exist.

### Exit

Standing. Every refusal has a test that fails when the rule is breached; the FA register and the venue count reconcile to the actual holdings and subscriptions; one full trigger-list walk is recorded per review in `docs/archive/gl5-review-YYYY-MM.md`.

### Stop

None. GL5 retires individual items; it does not stop. If it ever becomes a meeting whose only content is that nothing changed, fold it entirely into the two desks' X0 reviews and say so.

---

## Relationship to the existing desks

**This programme feeds. It does not replace, fork or duplicate.**

| This programme | Feeds | Explicitly does not |
|---|---|---|
| **GL0** (`settlement`, windows) | Alien **R1** — latest safe trade date, receipt-date proof, cliff-straddle assertion. Alien `execute` — session windows | Place the step-up. R1 owns execution and remains **alien-owned** under that plan's Lock 7 |
| **GL2** (Book Q) | Alien **W0 / W1** — the composition recorded before migration | Choose the composition. That is the investor's and the alien desk's |
| **GL4** (Book S) | Alien **W2** — widens the input set to non-US legs | Change W2's gate, which stays 10 bps / 10% NAV |
| **GL3** (Book K) | The alien desk's cash-sleeve rule — extends "never a US MMF" into "an Irish accumulating USD ultra-short line at ROR" | Reopen the US-MMF closure or the N5 situs cap |
| **GL1** (`household`, Book J) | Alien **R2** and India **Book S** — realisation ordering across both books; Schedule FA and Form 67 artefacts | Amend either desk's hurdles, re-derive either desk's lots, or become authoritative over either ledger |
| **GL5** | Both desks' **X0** reviews | Become a third review or a third loop |
| Import from **India** | Rev 2.0 shape: one machine, two windows (09:00 recon, 23:15 treasury), 15:00 MF cut-off, AMC/RTA for the carry core, recon to ₹1, ≤8 OPS, algo ID, no F&O order type, no intraday loop | Implement Rev 1.0 (superseded Nifty-beta charter) |
| Import from **US-person** Rev 1.2 | **Pre-tax measurements and friction only** | Import IRA, 40–20, §1256, Book C's 35.5 bps, or H1's 200 bps |

---

## Paper and live rules

1. **This programme authorizes no live strategy capital. $0 and ₹0.** There is no strategy.
2. **The wrapper transactions remain alien-owned.** The domicile migration and the basis step-up are wrapper actions, authorized before L0 on the alien plan, and date-bound. This programme supplies the date and refuses to duplicate the execution path. **A later agent must not block R1 as "live capital before a book passes", and must not let this programme place it either.**
3. **No paper sessions are required or authorized here**, because nothing in this programme generates an order. Where a rule this programme wrote changes an order — a session window, a registry refusal — it is exercised in the owning desk's existing paper regime and its refusal has a test.
4. **The join ledger is read-only over both desks' ledgers.** It never writes a lot, never adjusts a basis, and never becomes the filing source of record without a human signature.
5. **Every result is published at RNOR and at ROR. ROR governs.**

---

## Calendar — the dates this programme lives on

| Date | Why it matters | Owner |
|---|---|---|
| **11 Oct 2027 (working)** | UK/EU/CH move to T+1. If it slips, GL0's margin needs an extra day | GL0 / GL5 |
| **26 Mar 2028** | UK switches to BST; the 29–31 March overlap is the normal 14:30–16:30 London | GL0 |
| **On or before 17 Mar 2028 (GS1)** | Working latest safe trade date for the step-up — **≥ 14 calendar days** before the cliff | GL0 → alien R1 |
| **31 Mar 2028 (Friday)** | Working cliff. Last day of FY 2027-28 and of the RNOR window | `residency` |
| **1 Apr 2028** | ROR begins. Book J acquires content; Book K acquires value; both books enter one return | GL1 / GL3 |
| **31 Aug / 31 Oct** | ITR filing. Missing it permanently forfeits loss carry-forward — which is Book J's entire mechanism | GL1 / `ops` |
| ≈3 weeks in March, ≈1 week late Oct–early Nov | DST-gap weeks; session windows start at **13:30 London (working)** | GL0 / `execute` |
| Each desk's **X0** | The standing GL5 review rides along; no third meeting | GL5 |

---

## STOP memos

This programme uses the India desk's memo shape (historical template in superseded [india-equity-execution-plan.md](../archive/india-equity-execution-plan.md); live India map is [Rev 2.0 §13](india-equity-architecture-blueprint-rev2.md#13-twelve-month-staged-build)), with one addition: **every global STOP memo states whether the closure removes code, and if so which modules and registry entries were deleted.** A closed global book that leaves a module behind is how a join layer becomes a third desk.

Expected memos, pre-named so their existence is not a surprise: `docs/archive/gl1-book-j-stop.md` · `docs/archive/gl2-composition-note.md` · `docs/archive/gl3-book-k-stop.md` · `docs/archive/gl4-book-s-stop.md`. **GL0 has no expected STOP memo — it either exists before R1 or R1 runs blind.**

Preserve one wording exactly, because it is unusually valuable evidence: **listing-basis and session-overlap arbitrage is closed as measured and negative** — a 2–6 bps gap against an 8–15 bps round trip, with a comfortable MDE. That is a measured negative, not an unmeasurable maybe, and a later agent must not reopen it as one.

---

*Authority: [global-equity-architecture-blueprint.md](global-equity-architecture-blueprint.md) · Product authority: [global-financial-market-analysis.md](../archive/global-financial-market-analysis.md) · Siblings: [alien-us-equity-execution-plan.md](alien-us-equity-execution-plan.md) · India live map: [india-equity-architecture-blueprint-rev2.md](india-equity-architecture-blueprint-rev2.md) §13 · Historical STOP template: [india-equity-execution-plan.md](../archive/india-equity-execution-plan.md) (superseded)*
