# G0 charter — results calendar (free sources)

Written **before** the calendar hunt. This is not a residual peek. G1 is not run here.

| Lock | Choice |
|---|---|
| Universe | The existing GOLDEN 100-name equity panel. No expansion |
| Source | NSE public corporate-filings pages / JSON behind `nseindia.com` and `nsearchives.nseindia.com`. No vendor, no BSE-only feed, no paid calendar |
| Event | Financial-results filing (quarterly authority). Annual / half-year kept as a column, not mixed into G1 |
| Timestamp | Broadcast / filing datetime as published by NSE. Date-only is accepted if time is absent; G1 then uses the first session close that provably contains it |
| Window | Panel span: 2015-02 through 2026-04 |
| Coverage bar | Names with at least one dated results filing. Publish n, unique names, year span. Do not interpolate missing names |
| Alias | Map NSE symbols through the existing MCWB / membership alias table onto GOLDEN `.NS` names |
| Pass | A free calendar exists covering the panel at a scale G1 can use (hundreds of events, MDE printed in the G1 charter). No purchase |
| Defer | Endpoint blocked, history too short to be a first test, or a paid vendor is required. Book G stops. Do not buy data |
| Three-day cap | This hunt is the first-test attempt. If the free path is not working in this pass, defer rather than keep scraping |

Do not run G1 in this milestone. Do not pick a side. Language models may clean dates; they may not trade.
