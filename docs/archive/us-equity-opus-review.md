# Opus review — US retail desk, post-A1 measurement

**Reviewer:** Claude Opus · **Date:** 2026-09-12 · **Inputs:** status pack (measured through 2026-08-22), blueprint Rev 1.1, execution plan
**Verdict:** **UPDATE.** Both authority docs bumped to **Rev 1.2 (post-A1 measurement, 2026-09-12).**

Two things forced the edit. The execution plan's A1 milestone-map row asserted **1.39×, n=139, sign 5/5** — the measured spliced result is **1.19×, n=173, sign 4/5**, so the plan's own summary row was false against the tape. And both docs still read as *authorizing* the Cboe DataShop dump ("A1, only if A0.5 green" — A0.5 *is* green), which is exactly the sentence a later agent would use to buy a closed SKU with the book already shut. Nothing else in the docs was touched, no hurdle moved, no closed product reopened, and spend remains **$0**.

---

## Answers to the seven questions

**1 — Re-rank: Book A moves to explicitly closed; Book B becomes rank 2.**
A STOP is a result, not a pause, and leaving Book A at "rank 2" invites a later agent to treat it as the live second book. The blueprint ranking preamble now reads C rank 1, **B rank 2**, **A closed at A1**. I retitled the Book A section `CLOSED at A1 (2026-08-22)` and put the measured 1.19× and the fired kill criterion (c) at the top of it, but left the section body in place and in position: it is the record of *why* the book closed, and deleting it would lose the reasoning that protects against reopening. Reopening rule is the existing one — new data, not new specifications.

**2 — H1 stays at 200 bps and stays the L0 programme gate; the docs now say Book B is the only remaining route to it.**
H1 is not an A2-style sleeve identity, so the A1 STOP does not make it wrong — it makes it *narrow*. With A contributing 0 and C1's measured 35.5 bps, the identity `w × (sleeve − VTI) + (1−w) × C` gives, at B2's pre-registered 800 bps sleeve and w = 25%: `0.25 × 800 + 0.75 × 35.5 ≈ 227 bps`. H1 is therefore still reachable, but only through Book B, and only if B2 clears as written. I added that arithmetic to the H1 row. **200 bps is not lowered and B2's 800 bps is not lowered** — note the C term means B2's bar is now slightly more than sufficient (≈694 bps would suffice), and I deliberately did not relax it to match; a gate that clears with margin is the correct posture, and trimming it after seeing C's number would be a goalpost move. If Book B closes, the existing STOP row fires: 100% passive plus Book C location and bands.

**3 — B1 is the next action. Nothing still sequences it.**
The A1 month is over and closed inside itself, so "B1 after the A1 month" has no referent. The "do not buy A-tape and B-panel in the same month" lock is satisfied trivially — there is no A-tape left to buy — and I kept the lock rather than deleting it. P0's 200 outstanding fills do **not** gate B1: B0.5's listed zero-drift bound is 71.7 bps against a 40 bps kill, and H4's tolerance is 3 bps, so no plausible cost recalibration flips the B1 decision. Those fills stay a hard gate on **B3 and L0**, and I recorded that B1's net-of-cost figure remains labelled *working* until they land. Trial first; the Norgate subscription is authorized only if the trial panel is complete and Python-usable.

**4 — Yes, the ceiling drops to $346.50, Norgate-only.**
$700 was priced as one Cboe dump plus one Norgate 6-month. The Cboe half is dead and I explicitly forbade reallocating it, which is the failure mode a stale ceiling creates: an agent finding $353 of "unused budget" and shopping with it. Any fallback (EODHD, or Polygon only if the Norgate trial cannot deliver) must fit *inside* $346.50, not on top of it. This tightens the spend cap; it does not touch the Norgate free trial, which is unchanged and still comes first.

**5 — Goalposts confirmed, all unchanged.**
A1's **2×** hurdle stays where it was pre-registered; 1.19× fails it and 1.39× (OptionsDX-only) would have failed it too, so there is no version of the tape that rescues the book. **A2 and A3 stay not-run and unauthorized.** No delta-bucket search beyond the pre-registered five — that is spec mining. No extension to 2005–2011; 2012–present already delivered n=173, MDE 31.9, ratio 0.28, and contains the named 2018/2020/2024 stress years, so a longer sample would be a rescue attempt, not a better test. H1–H6, MDE-before-peek, the 5-spec α=0.01 trial budget, and the Norgate trial budget are all untouched. H1's 200 bps is untouched.

**6 — Stale SKU language patched in both docs.**
The Cboe row in blueprint §3.1 now reads **CLOSED — do not buy**, with the $580-vs-$100-stop history and the fact that there is no A2 to buy it for. The A1 Build block in the plan is prefixed **SKU CLOSED — never purchased, and not purchasable now**, with the original spec retained beneath it as record rather than deleted. Book B's "do not buy until A0.5 resolves" is replaced with the resolved state. Norgate is marked authorized-now, trial first. Polygon stays non-default, Sharadar stays closed until B1 passes, OPRA/CGI/Optsum/Databento/CRSP stay closed. Satellite memos (`c1-tax-location-proof`, `b0-public-pead-screen`, `zero-spend-feasibility`) are still stale by the status pack's own inventory but are **out of scope** — none is an authority doc, and the two authority docs now contradict them clearly enough that the authority wins.

**7 — Rev 1.2**, dated 2026-09-12, on both docs. Rev 1.1's substance is preserved; the revision note says Rev 1.2 records the A1 STOP in the ranking and the SKU table, moves no hurdle, and reopens nothing.

---

## Files changed

- `docs/next/us-equity-architecture-blueprint.md` — Rev 1.2 header and date; ranking preamble (B to rank 2, A closed); Book A section retitled CLOSED with the measured STOP banner; Book B A0.5-gating sentence replaced; §3.1 ceiling $700 → $346.50; Cboe row closed; Optsum row updated to the real A1 n/MDE; ThetaData row marked spent; Norgate row marked authorized-now; H1 row given the post-A1 reachability arithmetic. **§0 untouched.**
- `docs/next/us-equity-execution-plan.md` — Rev 1.2 header, date, revision note; Lock 9 ceiling $346.50; A1 milestone row corrected to 1.19× / n=173 / 4-of-5; A0.5 row's dump authorization marked spent and void; B1 row marked next certified step; both critical-path paragraphs de-staled; spend ladder retitled Rev 1.2 with the Cboe dump listed as closed; A1 Build SKU block marked closed; B1 Build given the P0-fills sequencing note.
- `docs/archive/us-equity-opus-review.md` — this memo.

No other files. No `src/`, no tests, no satellite memos.

---

## Residual risks

1. **H1 now rests on a single book.** Book B must deliver essentially the whole 200 bps. A B1 miss is a programme STOP, not a detour — the plan already says so, and that outcome should be treated as the expected one, not a surprise.
2. **B1's decision runs on working costs.** The 25 bps mid-cap round trip is uncalibrated until P0's 200 fills land. The margin (71.7 bps bound vs 40 bps kill) makes this safe for a go/no-go, but it is not safe for sizing, and B3 must not be waived on the strength of a B1 pass.
3. **Survivorship is still unresolved.** w = 12.9% is a *free-stitch* estimate with known dirty identities (AHL, SIVB, CHK) parked in N_missing. Lock 5 is satisfied only by the Norgate panel, and the trial must be checked for delisted-price completeness before the $346.50 is spent, not after.
4. **The last A1 fold was negative** (2021-09–2026-12, −0.55, n=58). That strengthens the STOP rather than weakening it, but it also means any future "vol is expensive again" argument must arrive as new data under a fresh pre-registration, not as a re-read of this tape.
5. **Retained-record risk.** Book A's pre-STOP prose and the A1 CBOE build spec are still in the docs, now under CLOSED banners. That is deliberate, but a careless reader could still quote the body. The banners are the defence; if an agent ever proposes an A-tape purchase, that is the tell that the banners failed.
6. **Satellite memos remain stale** and will keep pointing at CBOE and Polygon until someone sweeps them. Low risk while the authority docs govern, but it is real drift.
