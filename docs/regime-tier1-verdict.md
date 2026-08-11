# Tier 1 Regime Strategy — Feature Verdict

**Market:** NSE India, Nifty 100 universe, intraday equities  
**Scope:** Tier 1 regime gate only (Tier 2 / 3 out of scope)  
**Judges:** Gemini Flash, Claude Sonnet  
**Date:** 2026-07-30  
**A0 demotion:** 2026-08-11 — [regime-tier1-stop-memo.md](regime-tier1-stop-memo.md)

---

## Summary

| Decision | Locked choice |
|---|---|
| Daily method | **Deterministic rules** (not LLM as primary gate) |
| Daily states | `SUPPORTIVE` \| `AMBIGUOUS` \| `HOSTILE` \| `NO_TRADE` |
| Intraday model | HMM on **Nifty 15-minute** candles (triad emissions) |
| HMM states | `TREND_UP` \| `TREND_DOWN` \| `CHOP` \| `HIGH_VOL` |
| Build posture | **A0 (2026-08-11): soft overlay only** — not a cleared edge engine |
| Active escalation | **Horizon / Precision** — Regime architecture search CLOSED |

Daily owns the pre-open risk gate. Intraday HMM owns sleeve routing labels (long momentum vs short momentum vs mean-reversion vs pause). After A0, both are **frozen soft overlays** for the cascade — Tier 2/3 must carry path quality.

### A0 demotion (merged 2026-08-11)

| Lock | Decision |
|---|---|
| Trigger | A1 H1 quad-fail (I1+I5 Long+Short); H2 skipped reject-early |
| Intraday ship path | **Restore triad GaussianHMM** (`r_15`, `rv_15`, `vwap_dist`); A1 rules **REJECTED** |
| Regime role | Soft admission / sleeve labels only — **do not** treat I1/I5 Regime PASS as a cleared ship gate |
| Closed searches | Emissions (O5 / `adr_15` / HL/CO), A1, A2, Daily reopen, D2′ formula search |
| Next | Escalate [Horizon](horizon-tier2-verdict.md) / [Precision](precision-tier3-verdict.md) |

Full terminal memo: [regime-tier1-stop-memo.md](regime-tier1-stop-memo.md). Revision archives: [v1.1](regime-tier1-v11-revision.md), [v1.2](regime-tier1-v12-revision.md).

---

## Judge scores (minimal proposal)

| Axis | Gemini Flash | Claude Sonnet | Consensus |
|---|---|---|---|
| Daily features | 8/10 | 7/10 | 3 primary + breadth overlay |
| Intraday HMM features | 6/10 | 8/10 | TOD-normalized triad: `r_15`, `rv_15`, TWAP-`vwap_dist` (no fake volz) |
| Daily method | RULES | HYBRID (rules-first) | **RULES** for the gate |
| HMM states | 3 | 3 → 4 in ideal | **User lock: 4 with UP/DOWN** |
| Overall | REVISE | ACCEPT + minor | ACCEPT with revisions |

---

## Locked feature set (v1)

### Daily Regime (pre-open, rules)

#### Primary features (3)

Pre-open aligned for session date **T** (available by ~9:08–9:15; no same-day close leakage):

| Feature | Definition |
|---|---|
| `nifty_trend` (`market_trend`) | % distance of **prior** Nifty close (T−1) to EMA20 as of T−1 |
| `vol_regime` | India VIX vs 60d median **+ 1d ΔVIX**, both as of **T−1** (Nifty ATR%/Close fallback if VIX unavailable) |
| `shock` | Overnight gap `(open_T − close_{T−1}) / prev_ATR14` |

#### Confirmatory: Daily breadth

**`breadth_div`** — not a co-equal primary axis in v1.

Use one of (as of **T−1** for the pre-open gate on T):

- **% of Nifty 100 stocks above their 20DMA** (or 5DMA for a faster signal), or
- **Nifty 100 Advance/Decline ratio**

**Role:** divergence / veto strengthener only.

Example: index trend up (`nifty_trend` positive) but breadth weak → bias toward `AMBIGUOUS` / `HOSTILE`, not full `SUPPORTIVE` (hollow heavyweight-driven rally).

In the ideal set, both judges would promote breadth to a primary Daily feature.

#### Daily states

| State | Meaning | Typical posture |
|---|---|---|
| `SUPPORTIVE` | Trend supportive, vol calm, no shock; breadth not contradicting | Allow Tier 2/3; direction left to intraday HMM |
| `AMBIGUOUS` | Mixed signals (e.g. trend ok but breadth soft, or vol mildly elevated) | Trade allowed but cautious — HMM picks sleeve |
| `HOSTILE` | Weak trend / elevated vol / breadth collapse without full crisis | Defensive: reduced size or selective sleeves only |
| `NO_TRADE` | Hard veto — large gap shock; VIX spike (high ratio + large +ΔVIX); VIX collapse / event crush (elevated ratio + large −ΔVIX) | Flat — block lower tiers |

Interpretation:

- `NO_TRADE` = capital preservation kill switch  
- `HOSTILE` = hostile market, not necessarily halt  
- `AMBIGUOUS` = ambiguous; do not force strong Daily directional bias  
- `SUPPORTIVE` = green light for the cascade; HMM chooses direction / style  

---

### Intraday Regime (HMM on Nifty 15m)

#### Emissions (TOD-normalized)

| Feature | Definition | Notes |
|---|---|---|
| `r_15` | **Signed** 15m log return / TOD baseline σ | **Required** for `TREND_UP` vs `TREND_DOWN` |
| `rv_15` | (H−L)/Close vs same TOD bucket historical mean | Volatility intensity |
| `vwap_dist` | % distance to session **TWAP** (ATR-scaled); equal-weight typical `(H+L+C)/3` | **Required** in v1 (name kept; semantics are TWAP) |

**Zero-volume cash Nifty (`^NSEI`) — locked 2026-08-01:** cash-index feeds ship volume ≡ 0. Judges (Gemini Flash, Claude Sonnet) **reject** faking participation with `(H−L)×Close` (collinear with `rv_15`). For v1: **drop `volz_15`**; redefine `vwap_dist` as session-cumulative TWAP distance; revisit participation only with rollover-clean **Nifty futures volume** (not constituent sum volumes at Tier 1).

Without signed `r_15` (or signed `vwap_dist`), UP vs DOWN collapses.

#### HMM states (locked)

| State | Role for cascading |
|---|---|
| `TREND_UP` | Long momentum sleeves on; short momentum off |
| `TREND_DOWN` | Short momentum sleeves on; long momentum off |
| `CHOP` | Mean-reversion sleeves on |
| `HIGH_VOL` | Tighten stops / pause mean-reversion; reduce or flat |

Post-fit: map unlabeled HMM states by emission means (sign of mean `r_15` / `vwap_dist`) so UP vs DOWN labels stay stable across retrains.

Add min dwell / hysteresis — especially on `TREND_UP` ↔ `TREND_DOWN` — so Tier 2 is not flipped every bar.

---

## Daily method: LLM vs rules

| Option | Verdict |
|---|---|
| **Rules** | Winner for Tier 1 gate — deterministic, backtestable, audit-friendly, fits 9:08–9:15 pre-open |
| **LLM** | Rejected as primary gate — latency, cost, non-reproducible history |
| **Hybrid (optional later)** | Rules own `NO_TRADE` / `HOSTILE`; LLM may annotate `AMBIGUOUS` only; timeout → fall back to rules |

---

## Gate mapping (Tier 1 → sleeves)

| Daily | Intraday | Tier 2/3 posture |
|---|---|---|
| `NO_TRADE` | any | Flat — hard block |
| `HOSTILE` | `HIGH_VOL` | Flat or micro size only |
| `HOSTILE` | `CHOP` / `TREND_*` | Defensive / reduced size |
| `AMBIGUOUS` / `SUPPORTIVE` | `TREND_UP` | Long momentum on; short momentum off |
| `AMBIGUOUS` / `SUPPORTIVE` | `TREND_DOWN` | Short momentum on; long momentum off |
| `AMBIGUOUS` / `SUPPORTIVE` | `CHOP` | Mean-reversion sleeves on |
| `AMBIGUOUS` / `SUPPORTIVE` | `HIGH_VOL` | Tighten stops / pause MR |

---

## Where judges disagreed

| Topic | Gemini Flash | Claude Sonnet | Locked choice |
|---|---|---|---|
| `vwap_dist` in HMM v1 | Must add | Exclude → un-defer in ideal | **Required** as TWAP-distance (zero cash volume) |
| Zero-volume / `volz_15` | Drop volz; TWAP; futures later | Drop volz; TWAP; reject range proxy | **Drop `volz_15` in v1** |
| Signed `r_15` | Prefer \|r\| earlier | Keep signed | **Required** — direction needs sign |
| Daily breadth | Shorten horizon / A/D | Demote to divergence | **Confirmatory** in v1 |
| Daily method | RULES only | HYBRID rules-first | RULES now; hybrid later |
| ΔVIX | Implied via relative VIX | Add explicitly | **Include 1d ΔVIX** |

---

## Ideal feature set (not v1 — staged later)

Judges scored ideal vs minimal lift as **~6/10 (Claude)** to **~8/10 (Gemini)**. Both say: expand later, do not jump to full ideal on day one (HMM dimensionality).

### Ideal Daily (~10)

| Theme | Gemini | Claude | Consensus |
|---|---|---|---|
| Short trend | EMA20 dist / ATR14 | EMA20 %dist | Keep; ATR-scale preferred |
| Trend strength / long | EMA200 distance | ADX14 / EMA slope R² | Add strength or multi-horizon |
| Vol level + Δ | VIX vs median + ΔVIX | Same (split as 2 feats) | Keep both |
| Shock | Gap / ATR14 | Gap / ATR14 | Keep |
| Breadth | A/D 5d EMA + % > EMA20 | Promote % > 20DMA / A/D | **Promote to primary** |
| Dispersion | Cross-sector SD | Pairwise corr / XS disp. | Add |
| RV vs IV | 10d RV / VIX | 5–10d RV vs VIX | Add |
| Flows | 5d FII / mkt cap | 20d FII z-score | Add (NSE-specific) |
| Vol-of-vol | 10d SD of VIX | — | Gemini-only; second order |
| Expiry | Handle outside | Weekly/monthly ±1d flag | Cheap override (Claude) |

**Ideal Daily taxonomies (judge suggestions, not locked):**

- Gemini: `STR_BULL` \| `STR_BEAR` \| `MR_RANGE` \| `SYS_SHOCK`
- Claude: `BULL_TREND` \| `BEAR_TREND` \| `CHOP_RANGE` \| `DISPERSION_ROTATION` + flags `SHOCK_VETO`, `VOL_ELEVATED`, `EXPIRY_DAY`

### Ideal Intraday HMM emissions (~8)

| Feature | Gemini | Claude | TOD? | Consensus |
|---|---|---|---|---|
| `r_15` | Keep | Keep | Yes (σ) | Keep |
| `rv` / range | Keep | Keep + `range_15` | Yes | Keep; Claude adds range |
| `volz_15` | Keep if true volume | Keep if true volume | Yes | **Deferred:** cash Nifty volume ≡ 0; futures volume later |
| `vwap_dist` | TWAP in v1 | TWAP in v1 | Scale | Locked as TWAP-distance on cash index |
| Body vs wick | HL/CO ratio | — | Yes | Gemini candle-quality |
| Autocorr | — | lag-1/2 of r (~1h) | No | Claude TREND/CHOP edge |
| Intraday breadth | `adr_15` | adv/decl or NH/NL | Clip open | Both add |
| Cross-index corr | Nifty↔BankNifty | — | No | Gemini-only |
| Order book | Futures B/A imb. | **EXCLUDE** | — | Disagree → exclude |
| Vol acceleration | — | `rv_delta` | Inherit | Claude early-warning |

**Ideal HMM taxonomies (judge suggestions):**

- Gemini: `QUIET_MR` \| `DIR_MOM` \| `VOL_EXP` \| `NOISY_CHOP`
- Claude: `TREND_UP` \| `TREND_DOWN` \| `CHOP` \| `HIGH_VOL` ← **aligned with user lock**

### Still exclude (both judges)

- Raw price / raw volume  
- Stock-level features at Tier 1  
- US/global returns as separate features (use overnight gap)  
- Intraday absolute India VIX  
- Stacked multi-EMAs  
- PCR / OI clutter  
- News / NLP in the gate  
- Lagged HMM state fed back as an emission  

### 80% lift priority additions

| Gemini Flash | Claude Sonnet |
|---|---|
| 1. Rigorous TOD normalization | 1. Breadth primary + ADX `trend_strength` |
| 2. Daily `market_breadth_ad` | 2. Un-defer `vwap_dist` |
| 3. Intraday `vwap_dist_tod` | 3. `expiry_flag` |

**Staging:** v1 = locked minimal + confirmatory breadth + 3 HMM emissions (`r_15`, `rv_15`, TWAP-`vwap_dist`). Full ~10 daily / ~8 HMM emissions (incl. real participation) only after stable live/paper data.

---

## NSE production constraints

1. **TOD-normalize** all HMM vol/range inputs — otherwise the model learns the U-shaped clock (open/close = fake `HIGH_VOL`).
2. Down-weight / low-confidence the auction-bleed bar (wall **09:15–09:30**, bar-end stamp **09:30**): exclude from HMM fit/score/decode; null regime + `intraday_low_confidence`. Watch wall **14:30–15:15** (bar-end stamps **14:45–15:15**) via `session_watch` flag.
3. Prefer **relative VIX** (vs median + ΔVIX), not absolute levels — event crush (budget/elections) fools level thresholds.
4. **Hysteresis** on HMM flips, especially `TREND_UP` ↔ `TREND_DOWN`.
5. **Relabel** HMM states after each fit by emission means so UP/DOWN remain stable.
6. **Do not fake index volume** with `(H−L)×Close` / `|r|` proxies; use TWAP for location; add futures volume only after rollover stitching.

---

## Next build step

**Regime v1 feature build (historical — done):** Daily rules + triad HMM emissions as above.

**Post-A0 (2026-08-11):** do **not** open further Regime architecture / emission search. Active work = **Horizon / Precision** under the soft Regime overlay. See [regime-tier1-stop-memo.md](regime-tier1-stop-memo.md).
