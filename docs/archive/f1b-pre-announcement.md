# F1b — Pre-announcement ranking

**Gate:** F1b / execution-plan F3 ranking skill. **Date:** 2026-08-19.
Charter: `docs/next/f1b-charter.md`. Not a residual peek.

## Authority (top-k hit rate)

- n=24 (universe misses=5)
- hit rate=66.7% CI=[47.8%, 85.5%]
- naive=4.1% MDE=11.3%
- mean Next 50 rank=2.67
- verdict=**PASS**
- universe misses: IBULHSGFIN.NS (2017-01-31), IOC.NS (2017-01-31), GRASIM.NS (2018-01-31), NESTLEIND.NS (2019-07-31), MAXHEALTH.NS (2025-07-31)

IOC and IBULHSGFIN sit in the Nifty 50 MCWB file at the Jan-2017
cut-off, not Next 50. GRASIM, NESTLEIND, and MAXHEALTH are absent
from both files at their cut-offs (not a ticker-alias miss).

## 1.5× companion (not the gate)

- recall=100.0%
- precision=15.5%

## Hold-out print (same rule, not a re-fit)

- 2015–2019 n=13 hit=76.9% naive=4.8% verdict=PASS
- 2020–2025 n=11 hit=54.5% naive=3.3% verdict=PASS

## Book F

Out-of-sample top-k rank beats naive. That is F3-SKILL, not F2-NET.

**Superseded (Rev 3):** the previous sentence blocking a pre-announcement residual until F1a/F2 is withdrawn. See [f3-residual-charter.md](../next/f3-residual-charter.md).
