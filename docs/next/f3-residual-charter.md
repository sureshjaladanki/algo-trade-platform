# F3-RESIDUAL charter — predicted Next 50 basket (cost-free)

Written **before** the residual peek. This is blueprint construction **C2**, not a re-window of F1 / F1a / T−40 on actual additions.

F1 public windows are closed. F1b ranking (F3-SKILL) already PASS. This peek asks whether an *ex-ante* top-3 Next 50 basket earns the pre-announcement run-up.

It differs from the locked T−40 companion in three ways: that companion used **actual** additions (look-ahead), traded **one name**, and started at a date you could not have acted on. This charter uses the **ex-ante top-3 rank**, trades a **basket including names that never get added**, and starts at a PIT-safe entry.

| Lock | Choice |
|---|---|
| Universe | Next 50 members at the cut-off, from NSE MCWB monthlies |
| Rank | 6-month average free-float mcap to 31 Jan / 31 Jul. Prefer roll-forward (prior month shares/float × panel closes through cut-off) so the rank exists on 1 Feb / 1 Aug; if roll-forward fields are missing, use the cut-off month MCWB file and record the lag |
| k | **Fixed k = 3**, equal weight. Ranking-gate k = actual additions is look-ahead and is not tradable. Mean actual rank 2.67 justifies 3 |
| Entry | Close of the **first NSE session of February / August** |
| Exit | Close of the **first session strictly after** the announcement date. Evening PRs; this captures the gap |
| Cycles | All semi-annual cycles 2015–2025, including cycles with zero additions. n ≈ 22 |
| Authority benchmark | Equal-weight control basket of Next 50 **ranks 21–50** at the same cut-off |
| Companion benchmark | vs Nifty, for comparability with F1 |
| Missing coverage | A slot with no bars contributes **0 bps (cash)**; publish coverage. Sensitivity: drop cycles with coverage < 2/3 |
| Clip | −500 bps on the **basket** return, keep the row |
| Statistic | Session-block bootstrap 95% CI, fold sign by cycle-year |
| Prior σ | **750 bps** (pre-registered: companion sample σ 982 × √(0.4 + 0.6/3), ρ = 0.4) |
| MDE | **448 bps** (2.8 × 750 / √22) |
| Economic hurdle | **300 bps gross** per cycle-basket |
| F&O screen | Not applied (conservative dilution) |
| Decay | Era split 2015–19 vs 2020–25 is a **column in this print**, not a standalone F4 |
| Friction | None on this peek. F2-NET only on a GO |

MDE (448) exceeds the hurdle (300). This peek is decision-grade, not publication-grade.

## Terminal decision (capital)

- **GO** — point ≥ 450 bps **and** CI lower bound > 0 **and** both era halves positive. Opens F5 tradability and a domestic replication. Does **not** release live capital.
- **STOP** — point < 300 bps.
- **INCONCLUSIVE** — anything between. **Resolves to STOP for capital.** The standard repair (more Nifty 50 events) does not exist.

Do not fit a model. Do not re-open C1. Do not promote locked companions. Do not probability-weight until this peek has a verdict.
