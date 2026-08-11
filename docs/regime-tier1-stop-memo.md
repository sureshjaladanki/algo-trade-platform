# Tier 1 Regime — Stop Memo (A0 terminal)

**Market:** NSE India, Nifty 100 universe, intraday MIS cash  
**Status:** **TERMINAL — Tier 1 Regime architecture search CLOSED**  
**Date:** 2026-08-11  
**Friction lock:** **0.30% (30 bps)** round-trip — do not re-derive  
**Depends on:** [regime-tier1-verdict.md](regime-tier1-verdict.md) (locked v1 + A0 demotion), [regime-tier1-eval-verdict.md](regime-tier1-eval-verdict.md), [regime-tier1-v11-revision.md](regime-tier1-v11-revision.md), [regime-tier1-v12-revision.md](regime-tier1-v12-revision.md)  
**Trigger:** A1 H1 quad-fail (reject-early; H2 not run)

---

## One-line

Pre-registered Intraday architecture shot **A1 failed** on holdout H1 (2021); **A0 is locked** — demote Regime to frozen soft overlay (triad HMM restored), do not reopen Regime search, **escalate Horizon / Precision**.

---

## What failed (terminal evidence)

| Item | Result |
|---|---|
| Candidate | **A1** — frozen triad rules (`rv` p80 / `\|r\|` p50 + `vwap_dist` sign); hysteresis + cascade gates unchanged |
| **H1** | Train 2018–2020 → test **2021** — `logs/eval_a1_h1.txt` |
| OCC | **PASS** — UP 11.9% / DOWN 8.4% / CHOP 50.9% / HV 28.9% (n=4951) |
| 2020 S/A disclosure | 184/252 (**73.0%**) — not a gate |
| I7 | Report-only (A1 by construction) |
| **I1** long | **FAIL** — Edge −0.027, CI [−0.094, +0.024] |
| **I1** short | **FAIL** — Edge −0.088, CI entirely &lt; 0 |
| **I5** long / short | **FAIL** both (CI LB ≤ 0; long `p_adm`≈0) |
| I4 | Flip 0.23%; ASD TREND ≈ 1.2 (diagnostic) |
| **H2** | **Skipped** — H1 quad-fail reject-early (accept path always needs both; reject does not) |

Prior cycle (v1.1): emission-add search **CLOSED** (O5 / `adr_15` / HL/CO all FAIL+REVERTED); Daily frozen soft overlay; D2′ FAIL diagnostic; A2 **REJECT**. A1 was the single remaining architecture try.

---

## Locked A0 outcomes

| Lock | Decision |
|---|---|
| Regime posture | **Demoted to soft overlay** — Daily v1 veto/admission + triad GaussianHMM sleeve labels remain available to the cascade, but Regime is **not** a cleared edge / admission engine |
| Intraday model | **Restore locked-v1 triad HMM** (`r_15`, `rv_15`, `vwap_dist`) as the frozen soft overlay; A1 rules are **REJECTED** (do not ship, do not re-tune quantiles) |
| A1 | **REJECT** after H1 FAIL — no quantile change, no H2 peek, no merge into ship gates |
| A2 / more emissions / 3rd holdout | **REJECT** — terminal; no second architecture candidate |
| Daily / D2′ / O6 / O7 / IndexTB floors | Stay **CLOSED / REJECT** as in v1.1 |
| Eval years 2021 / 2022 | Quarantine further **Regime** architecture peeks; free for Horizon / Precision work |
| Ship gates | **Do not** treat I1 / I5 Regime PASS as a merge requirement going forward under this memo — those gates failed under both HMM (A+B) and A1 (H1) |

---

## Escalate (active work)

1. **Horizon (Tier 2)** — path quality / selection under the soft Regime overlay; do not wait on further Regime redesign.  
2. **Precision (Tier 3)** — timing / monetization only after Horizon path quality improves (see also [cascade-tier3-ws01-verdict.md](cascade-tier3-ws01-verdict.md)).  
3. Regime code stays runnable for cascade admission labels; **do not** open a new Regime revision cycle without an explicit new dual-judge charter.

Pointers: [horizon-tier2-verdict.md](horizon-tier2-verdict.md), [precision-tier3-verdict.md](precision-tier3-verdict.md).

---

## Explicit do-not (post-stop)

- Reopen A1 quantiles / drop `vwap_dist` / add magnitude floors / A2  
- Another emission-add try on the 4-state HMM  
- Merge A1 on any single-fold or diagnostic re-read of H1  
- Treat OCC PASS or I7 report-only as evidence of a healthy A1 map  
- Edit this memo into a “REVISE” — it is **terminal** for Tier 1 Regime search

---

## Code restore note

A1 implementation was **removed** from the codebase after A0 (module, CLI flag, OCC pre-check, eval wiring). Soft overlay path is triad HMM only. H1 evidence remains in `logs/eval_a1_h1.txt` and this memo.
