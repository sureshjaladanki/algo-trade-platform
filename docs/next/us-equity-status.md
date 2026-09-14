# Retail US desk — measured status pack (Opus briefing)

**Branch:** `us-equity`  
**Authority:** [us-equity-architecture-blueprint.md](us-equity-architecture-blueprint.md) **Rev 1.2** · [us-equity-execution-plan.md](us-equity-execution-plan.md)  
**Measured through:** 2026-08-22 · **Spend to date:** $0  
**Opus review:** 2026-09-12 — **UPDATE** → Rev 1.2. Memo: [us-equity-opus-review.md](../archive/us-equity-opus-review.md).  
**This file:** compact results. Review questions below are answered in the memo; they are retained as the briefing that was sent.

---

## Programme one-liner

Ask whether any after-cost, after-tax algo book beats an after-tax VTI hold for a $25k–$500k US retail desk. Constraint order: tax wrapper → friction → inference → capacity → alpha.

**Now (Rev 1.2):** Book A **closed** at A1; Cboe SKU closed with it. Book C accounting **passed**. Book B is rank 2; $0 screens **did not kill**. **B1 is the next action** (Norgate trial, not started). Discovery ceiling **$346.50** (Norgate only; Cboe half not reallocated). P0 software green; 200 broker fills outstanding (gate B3/L0, not B1). C2 not started. H1 200 bps and A1 2× **unchanged**.

---

## Milestone board

| ID | Status | Headline number | Certified? |
|---|---|---|---|
| P0 | Software green; **200 fills outstanding**; $0 paid data | `costs`/`tax` unit-tested, working rates | Partial |
| U0 | Listed fixtures + leakage tests green | Delisted *prices* deferred to B1 | Listed only |
| H0 | Complete | All three books MDE ≤ 0.5 × hypothesized | Yes |
| C1 | Complete | **35.5 bps/yr** vs static VTI, 0 washes | Yes (accounting) |
| C2 | Not started | Live year / 1099-B | — |
| A0 | Complete | VIX–RV net **2.91** vol pts, sign 5/5 | Screen only |
| A0.5 | Complete | Spread retains **62.2%** of credit (n=37/54) | Kill screen only |
| A1 | **STOP** | IV−RV **4.91** vs spread cost **4.14** = **1.19×** (hurdle 2×) | Yes — book closed |
| A2 / A3 | Not run | A1 closed the book | — |
| B0 | Complete | Listed PEAD **80.9 bps** (n=17,143; survivorship) | Screen only |
| B0.5 | Complete | Item 2.02 **82.3 bps**; w=**12.9%**; bound **71.7 bps** | Kill screen only |
| B1 | **Not started** | Norgate trial, then $346.50 / 6-mo if complete | Next certified test |
| B2 / B3 / L0 / X0 | Not started | — | — |

Critical path as written: B0.5 → **B1** → B2 → B3 → L0. Do not buy A-tape. L0 only after a book passes. Plan still says “B1 after the A1 month.”

---

## Book results (authoritative numbers)

### Book C — tax / location / harvest

| | |
|---|---|
| Window | 2018-01-02 – 2023-12-29 (5.99y) |
| After-tax excess vs static VTI | **35.5 bps/yr** (hurdle 25) |
| Washes | 0 · 46 harvest events · representative $100k + $500/mo DCA |
| Gate | Pass — keep harvest, location, bands |
| C2 | Not started (calendar, not a vendor) |
| Detail | [c1-tax-location-proof.md](../archive/c1-tax-location-proof.md) |

### Book A — index VRP (closed)

| Milestone | Number | vs hurdle |
|---|---|---|
| A0 VIX–RV expensive-end | 2.91 vol pts, n=259, sign 5/5 | Screen; 2020 raw −0.23 |
| A0 PUT vs VTI 2016–2026 | after-tax PUT **5.08%** vs VTI **15.19%** | 1256 wedge **98 bps/yr** full sleeve ≈ **20 bps** at 20% weight (< C1 35.5) |
| A0.5 credit retained | **62.2%** vs 25% kill; all-in 37.8% of credit | Did not kill; H3 still closed FREE-window *certification* (n=38, MDE 68.1, ratio 0.59) |
| A1 MDE | n=173, MDE=31.9 bps, ratio=0.28 | Inside H3 |
| A1 IV−RV / spread cost | **4.91 / 4.14 = 1.19×** | Hurdle **2×** → STOP |
| OptionsDX-only (to 2023) | 5.27 / 3.79 = **1.39×** | Same fail; splice added 2024 |
| A1 sign net of cost | 4/5 sub-periods; last window 2021-09–2026-12 **−0.55** (n=58) | Exit asked ≥4/5; last fold is the problem |
| Stress raw IV−RV | 2018 +1.54, 2020 +2.06, 2024 +1.44 | Named years present |
| Spend | $0. Cboe cart **$580** tripped $100 stop. OptionsDX + ThetaData FREE splice | Do not buy Cboe. Do not search other deltas. Do not extend to 2005–2011 |
| Detail | [a1-vrp-existence.md](../archive/a1-vrp-existence.md) · STOP [book-a-stop.md](../archive/book-a-stop.md) |

H1 identity (pre-registered 2026-08-21, before tape): book excess = `w × (sleeve − VTI) + (1−w) × C`. At w=20%, “200 bps book vs VTI” demands +1,000 bps sleeve vs VTI. A0 already showed that is unreachable. H1 remains an **L0 programme gate**, not an A2 sleeve identity.

### Book B — PEAD (alive, uncertified)

| Milestone | Number | vs hurdle |
|---|---|---|
| B0 listed mid-cap net 20d | **80.9 bps**, n=17,143, n_eff=3,428.6, MDE=38.3, ratio=0.38 | Kill 40; current S&P 400; all 8-Ks; survivorship-biased |
| B0.5 Item 2.02 mid-cap net | **82.3 bps**, n=13,907, n_eff=2,781.4, MDE=42.5, ratio=0.42 | Kill 40 |
| Missing-tape weight w | **12.9%** (N_listed=399, N_missing=59 after Tiingo+successor stitch) | w that zeros B0 to 40 at 0 delisted drift = **50.6%** |
| Zero-drift bound | (1−0.129)×82.3 = **71.7 bps** | ≥ 40 → B0 still *informs* B1 |
| Membership missing mass | 62.1% left the index (promoted/demoted/delisted) | Lock 5 still requires delisted *prices* |
| Gate | B1 Norgate trial authorized **only if you proceed** | Not Lock 5. Not certified |
| Detail | [b05-item-202-bound.md](../archive/b05-item-202-bound.md) · [b075-tiingo-coverage.md](../archive/b075-tiingo-coverage.md) |

B1 exit (unchanged): net-of-cost drift ≥ **40 bps**/event on PIT panel, present in $20–100M ADV, sign-stable walk-forward. SKU: Norgate Platinum **3-week trial**, then **$346.50 / 6 months** dump-and-cancel. Not Polygon.

---

## Hurdles vs remaining path

| ID | Rule | After A1 STOP |
|---|---|---|
| H1 | Total book after-tax vs VTI ≥ **200 bps/yr**, excess Sharpe ≥ 0.5 | C contributes **35.5**. A contributes **0**. H1 now sits almost entirely on Book B (B2 already asks 800 bps/yr sleeve at 25% weight = 200 bps book-level) |
| H2 | Book DD ≤ passive DD | Untouched |
| H3 | MDE before peek; MDE > 0.5 × effect → no peek | Held on every run |
| H4 | Modelled cost vs fills | **P0 fills still outstanding** |
| H5 | C ≥ 25 (met). A ≥ 75 vs ETF + Sharpe ≥ 0.4 (A closed before A2). B ≥ 40 bps/event | B uncertified |
| H6 | 5 specs/book, α=0.01 | Untouched |
| STOP | All books below H5 → 100% passive + C location/bands | Not yet: B still open |

Do **not** weaken H1–H6, MDE-before-peek, or the trial budget to rescue a path. Do **not** move the A1 **2×** hurdle after seeing 1.19×.

---

## Spend ladder (Rev 1.1 → now)

| Step | Authorized | Actual |
|---|---|---|
| Done | C1, H0, A0, A0.5, A1, B0, B0.5 | **$0** |
| A1 first dollar | Cboe $25–35, stop if cart > $100 | Cart $580 → **not bought**. Splice $0. Book closed |
| Next dollar | B1 Norgate trial then $346.50 / 6 mo | **Not started** |
| Closed | Full OPRA, CGI, Polygon default, Sharadar before B1, 2005–2011 Optsum, Databento, CRSP | — |
| Ceiling before L0 | **$700** (was CBOE + Norgate) | CBOE unused. Residual vendor is Norgate only |

---

## Stale language (inventory, not a mandate)

Opus may fix these if it updates; do not expand scope to satellite memos unless a sentence in the two authority docs is false.

| Location | Stale bit |
|---|---|
| Execution plan A1 **milestone-map** row | Says **1.39×**; status/STOP use spliced **1.19×** |
| Execution plan critical path | “B1 after the A1 month” — A1 month is over |
| Blueprint §2 Book A | Still **rank 2** after STOP |
| Blueprint §2 Book B | “Do not buy until A0.5 resolves” — A0.5 and A1 are done |
| Blueprint §3.1 | Cboe still listed as A1 SKU; A1 already ran at $0 and closed |
| Blueprint header date | 2026-08-21; A1/B0.5 are 2026-08-22 |
| `docs/archive/c1-tax-location-proof.md` | “A1 still needs CBOE / B1 still needs Polygon” |
| `docs/archive/b0-public-pead-screen.md` | Gate “buy Polygon PIT panel” |
| `docs/archive/zero-spend-feasibility.md` | “Do not skip CBOE / Polygon”; A1/B1 SKUs outdated |

Out of scope for this review unless they appear inside the two authority docs: `src/`, tests, other-branch India/forced-flow docs, P0 fill collection.

---

## Review questions (answer each; then choose update / no-update)

1. **Re-rank.** With A closed, should Book A move to “explicitly closed” and Book B become rank 2, or stay as a recorded STOP with rank unchanged?
2. **H1 reachability.** With C=35.5 and A=0, is H1 still the right L0 programme gate, or must the plan state that **only B2’s 800 bps sleeve** can deliver it? Do not lower 200 bps.
3. **B1 authorization.** Is B1 now the next action (A1 month over), or does anything still sequence it (P0 fills, “do not buy A-tape and B-panel in the same month”)?
4. **Ceiling.** Should the $700 discovery cap drop to Norgate-only (~$346.50) now that Cboe will not be bought?
5. **Goalposts.** Confirm A1 2× and A2/A3-not-run stay. Confirm no delta-bucket search, no 2005–2011 extension.
6. **Stale SKUs.** Update Cboe/Polygon/A0.5-gating language in the two authority docs so a later agent cannot buy a closed SKU.
7. **Rev bump.** If you edit, call it **Rev 1.2** (post-A1 measurement). If you do not edit, say why Rev 1.1 still governs.

---

## Opus operating rules (token budget)

- Read **only** this file, the blueprint, and the execution plan.
- No glob, no grep of `src/` or other docs, no tests, no git, no poetry, no new long documents.
- Review memo ≤ 120 lines at `docs/archive/us-equity-opus-review.md`.
- Edit the two authority docs **only if** a measured result makes a sentence false or a later agent could buy a closed SKU. Surgical patches, not rewrites of §0.
- Do not weaken hurdles. Do not reopen closed products. Do not authorize A-tape.
