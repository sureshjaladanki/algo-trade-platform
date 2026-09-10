# Inherited learnings — research operating system

Methods earned on closed ledgers. Reimplement them in `src/events/` when a gate needs them. **Do not import the frozen cascade tree** — it is not on this branch.

None of this is a product. It is how a peek is allowed to count.

---

## Required skill before a fit

\[
\mathrm{IC} \approx \frac{c - \delta}{\sigma \cdot \mathbb{E}[z \mid \mathrm{selected}]}
\]

Every measured drift in the prior tree sat between **0 and 8 bps** against costs of **10 to 20 bps**. No model class fixes a negative numerator. State required skill against the measured ceiling **before** fitting.

On this desk the hurdle is **45 bps delivery** and **20.8% STCG**, compared to an **after-tax** passive hold — not a pre-tax index line.

---

## Gate validity (invoke FAIL only if all hold)

1. The gate is passable by a correct model.
2. The inputs can carry the effect.
3. **MDE is printed before the peek**, beside the point estimate.
4. The pipeline is wired.
5. The statistic matches the claim.
6. The hurdle is the instrument's own (delivery 45 bps here; never sample-era futures STT).

INCONCLUSIVE (MDE ≥ effect) is not a pass. Repair is more history from the existing panel, never a re-run with a different window after seeing the result.

---

## Three-way verdict

On a session-block bootstrap CI of the claim statistic:

| Verdict | Rule |
|---|---|
| **PASS** | CI lower bound > 0 (after the hurdle in use) |
| **FAIL** | CI upper bound < the hurdle |
| **INCONCLUSIVE** | otherwise, or MDE at or above the effect |

Do not treat an inconclusive as a pass. Do not smooth, pool, or reweight to hide a downward trend.

---

## Pooled authority, not per-fold 95%

A sparse book cannot pass a per-fold 95% lower bound above zero at a honest fire rate. Authority is:

1. **Pooled** session-block CI across pre-registered folds, lower bound > 0, **and**
2. A **fold sign test** (point estimate positive on enough folds).

Session is the independent unit. Print event count, interval, MDE, and sign together.

---

## Purge

Walk-forward folds need an explicit **calendar embargo** between train end and test start (the prior tree used 5 calendar days on rolling annual folds). Dual-fold A/B (2018 / 2019) historically had **no** gap — do not silently rewrite that if a reprint is ever needed. New peeks on this desk use a real purge.

---

## Disaster clip, not drop, not a tight stop

On thin drift, a stop inside session noise is triggered by randomness and **destroys** the mean. Clip disaster losses at a wide floor (prior tree: 500 bps) and **keep the row**. Do not drop disasters; that biases EV up. Risk lives in position caps and skip masks.

Tight stops as silent risk control are **forbidden** on this desk.

---

## Range head (sizing only)

Remaining-session range was incremental to VIX, HAR, and name ATM IV (Spearman on the order of 0.61 in the prior work). **It never picks a side and never sells premium.** Rebuild it later only if Book F/G needs a skip or size mask — not as a research track of its own.

---

## What this is not

Point-in-time index membership helpers are **promoted** to Book F's event source; they are not described here because the membership data lives with the panel, not with these methods. Cascade models (HMM, rankers, Precision) are not inputs, features, or tie-breaks.
