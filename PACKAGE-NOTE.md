# PACKAGE NOTE — P15: Sales Forecast Pack

**Fiverr-ready gig title:** "I will forecast your next 6 months of sales with trend and seasonality, and show you the honest error"

## What the buyer gets

A full 6-month sales forecast, not a one-off spreadsheet: a trend +
seasonal-index model fitted to the shop's own monthly sales, a
month-by-month forecast with the money on every line, an honest
backtest (the model forecast 3 months it had never seen), and a
What-If sheet where the owner changes the growth rate and the
seasonal uplift and watches the forecast move. Delivered on this
sample: 22 months of history (PKR 68,170,300), a 6-month forecast of
PKR 21,306,134, a backtest MAPE of 4.82%, 100+ data-quality checks
passing, and the SQL that re-forecasts next month the same way.

## Tiers

| Tier | Price | Delivery | Includes |
|---|---|---|---|
| **Basic — $20** | $20 | 2 days | 6-month sales forecast from one monthly sales file (12–36 months of history) → forecast report (PDF-ready markdown) with the 3 key findings + forecast table (CSV). |
| **Standard — $65** | $65 | 4 days | Everything in Basic + Excel forecast workbook with live-formula KPIs (Dashboard + History + Forecast + Backtest + What-If + Method sheets) + backtest with MAPE + the SQL that re-runs the forecast. |
| **Premium — $140** | $140 | 7 days | Everything in Standard + a second file in the same run (e.g. a category-level forecast: the same model per product category) + a monthly re-forecast setup (same model, dated snapshots, forecast-vs-actual tracking report) + a 30-min walkthrough call on the findings and the stock/cash plan for the peak month. |

## What the buyer must provide

- The monthly sales file (CSV or Excel, 12–36 months of history;
  Basic up to 36 months, Standard up to 60, Premium up to 120) with
  at least: month and total sales. Orders, units and a per-category
  split are optional — the forecast works without them, but the
  workbook is richer with them.
- The forecast horizon they want (default 6 months) and any known
  one-off months to flag (e.g. a shop closure, a one-time bulk order)
  — otherwise every month is modelled like the rest.
- Any known upcoming change (a new branch, a price rise, a supplier
  change) — the What-If sheet can model it, but only if the buyer
  says so up front.

## Notes for the seller (Hashir)

- Sample built on a fictional shop's generated file (Noor
  Electronics, 22 months) — the forecast is the proof to show a
  buyer. Never present the demo Noor Electronics file as a real
  client forecast; the deliverable is the method, the sample proves it.
- The backtest MAPE is the trust line: quote it to the buyer up
  front ("the model was off by 4.82% on the 3 months it never saw")
  instead of promising accuracy. A buyer who hears the error first
  trusts the forecast more, not less.
- Seasonal indices for Nov and Dec rest on one observation each in
  this sample — say this to the buyer: with fewer than 2 full years
  of history, the newest months' indices are the least certain, and
  the forecast should be re-run every month as new actuals arrive.
- The trend is a straight line: if a buyer's sales are clearly
  curved (fast growth that is slowing, or a step change), say so
  before taking the order — the model will still run, but the
  forecast will be honest about its limits, not silently wrong.
- Monthly re-forecasting (Premium) reuses the P4 snapshot-diff
  pattern: same model, dated snapshots, forecast-vs-actual report
  (what was forecast, what actually sold, how the error moved).
