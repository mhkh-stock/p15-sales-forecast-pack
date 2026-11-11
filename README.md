# P15 — Sales Forecast Pack: how much will we sell in the next 6 months?

**Client (SAMPLE):** Noor Electronics, Lahore — electronics retailer,
Jan 2024–Oct 2025 · **Forecast:** Nov 2025–Apr 2026 · **Status: SAMPLE delivery on DEMO data**
**Tools:** Python (stdlib forecast) · SQL (trend + seasonal index recompute) · SQLite · Excel (live formulas)
**Deliverable:** `outputs/sales_forecast_SAMPLE.xlsx`
(Dashboard + History + Forecast + Backtest + What-If + Method, 22 months of history)

> ⚠️ **What this is and is not.** The monthly sales file is a
> fictional shop's demo data, generated to show the method. No real
> shop, customer or payment is involved. What is real is the method:
> the same trend + seasonal-index forecast, the same SQL and the
> same workbook run on a real client's file the same way, and every
> number in the report is recomputed from the data, never typed.

## Business question it answers

> "How much will we sell in the next 6 months — and how much stock and cash should we plan for?"

A shop that orders on gut feel either runs out in the peak month or
sits on dead stock in the dip. This delivery fits a trend + seasonal
model to 22 months of the shop's own sales, forecasts the next
6 months month by month, backtests the model honestly on the last
3 months it never saw, and gives the owner a What-If sheet to
stress-test the plan.

## What is inside

| File | What it does |
|---|---|
| `outputs/sales_forecast_SAMPLE.xlsx` | The deliverable: Dashboard (13 live-formula KPIs + forecast at a glance) + History (22 months, live seasonal index / trend / fitted) + Forecast (6 months, all live formulas) + Backtest (hold-out, MAPE) + What-If (growth + seasonality inputs, live recompute) + Method (parameters + index table) |
| `outputs/forecast_report.md` | Findings report: headline numbers, 3 key findings with "so what", forecast table, backtest table |
| `outputs/forecast_summary.json` | Machine-readable summary (KPIs + trend + indices + forecast + backtest) |
| `data/raw/monthly_sales_SAMPLE.csv` | The sales file: 22 months, 5 categories, PKR 68,170,300 |
| `data/processed/forecast.csv` | The 6 forecast months (trend, index, forecast, share) |
| `data/processed/backtest.csv` | The 3 hold-out months (actual, forecast, error, APE) |
| `data/processed/seasonal_indices.csv` | The 12 calendar-month indices, full fit vs backtest fit |
| `data/processed/sales.db` | SQLite: dim_month + dim_category + fact_monthly_sales + fact_monthly_totals + fact_forecast (NOT uploaded — rebuildable) |
| `data/README.md` | Data dictionary + known quirks |
| `sql/schema.sql` | Star-lite schema for the five tables |
| `sql/forecast_model.sql` | The forecast logic in SQL (seasonal index + OLS trend + 6-month forecast) — recomputes the Python model |
| `src/generate_data.py` | Makes the demo file (seeded; NOT run on a real client file) |
| `src/forecast.py` | Computes seasonal indices, trend, forecast and backtest (stdlib only) |
| `src/build_sqlite.py` | Loads sales + forecast into SQLite |
| `src/analyze.py` | Regenerates the report — every number recomputed, never typed |
| `src/build_workbook.py` | Builds the workbook: 6 sheets, live formulas |
| `src/checks.py` | Data-quality + reconciliation checks as code — 132 checks, all passing |
| `requirements.txt` | Pinned: `openpyxl==3.1.2` (Python 3.12; the forecast itself is stdlib-only) |

## How it fits together

```
client's monthly sales file ──▶ src/forecast.py ──▶ data/processed/forecast.csv + backtest.csv
        (22 rows)                    │                     │
                                     ▼                     ▼
                             src/build_sqlite.py ──▶ data/processed/sales.db
                                     │              (NOT uploaded: rebuildable)
                                     ▼
                             src/analyze.py ──▶ outputs/forecast_report.md
                                     │
                                     ▼
                             src/build_workbook.py ──▶ outputs/sales_forecast_SAMPLE.xlsx
                                     ▲ src/checks.py verifies all of it (132 checks)
```

## How the forecast works

- **Seasonal index** per calendar month: mean sales in that month
  divided by the grand monthly mean, normalised so the 12 indices
  average exactly 1.0. Mar (Ramadan/Eid) is the peak (1.1213);
  Jan (winter dip) is the lowest (0.8020).
- **Trend:** ordinary least squares of deseasonalised sales
  (sales / index) on time t = 0..21. Intercept PKR 2,695,990,
  slope +PKR 38,079 a month — the shop grows slowly and steadily.
- **Forecast:** trend(t) × index(month) for t = 22..27
  (Nov 2025–Apr 2026).
- **Backtest (honest, no leakage):** the model was re-fitted on
  Jan 2024–Jul 2025 only and forecast Aug–Oct 2025, which it had
  never seen. MAPE 4.82%.

## 3 key findings (from this file)

1. **The peak is coming in March, not December.** Mar 2026 is
   forecast at PKR 4,133,046 — the highest of the six months —
   because Ramadan and Eid al-Fitr fall in March 2026 and the shop's
   own history peaks there (seasonal index 1.1213). *So what:*
   stock for March should be ordered in February, not after the
   rush starts.
2. **January is the planning month, not a problem month.** Jan 2026
   is forecast at PKR 2,895,012 — the lowest of the six — because
   the winter dip is in the shop's own data (seasonal index 0.8020).
   *So what:* use January to clear slow stock and negotiate supplier
   terms, not to judge the business.
3. **The model is honest about its error.** The backtest missed
   Aug–Oct 2025 by 4.82% on average (Aug 2025 6.49%, Sep 2025 1.52%,
   Oct 2025 6.44%). *So what:* plan cash and stock on the forecast
   minus 4.82%, and treat the forecast as a planning range, not a
   target to hit to the rupee.

## Verified numbers

| KPI | Value |
|---|---|
| History (Jan 2024–Oct 2025) | 22 months, PKR 68,170,300 total |
| Avg monthly sales / best month | PKR 3,098,650 / Jun 2025, PKR 3,879,400 |
| Forecast total Nov 2025–Apr 2026 | PKR 21,306,134 (avg PKR 3,551,022 / month) |
| Forecast vs last 6 months | +3.1% vs May–Oct 2025 (PKR 20,669,900) |
| Best forecast month | Mar 2026, PKR 4,133,046 |
| Backtest MAPE (Aug–Oct 2025) | 4.82% |
| Trend slope | +PKR 38,079 / month |
| SQL recompute vs Python | 6/6 forecast months within 1% |
| Checks | 100+ passing (`python3 src/checks.py`) |

Verification: `python3 src/checks.py` (132 checks pass — file shape,
money reconciliation to the rupee, seasonal indices, trend and
forecast recomputed independently, backtest MAPE recomputed, SQL
forecast agreeing with Python, SQLite integrity, workbook structure
and formulas, and every headline number in the report) **and** the
workbook was opened in LibreOffice, which calculated every formula:
Dashboard shows 22 months, PKR 68,170,300 history total,
PKR 21,306,134 forecast total, 4.82% backtest MAPE, and the Forecast
sheet totals PKR 21,306,134 with shares summing to 100% — identical
to the Python recompute.

## Limits — what this delivery does not do

- **Demo data, 22 months.** A real client's file has its own growth,
  its own seasonality and its own category mix — the numbers here
  describe Noor Electronics' sample, not any real shop.
- **Seasonal indices for Nov and Dec rest on one observation each**
  (the file has only one Nov and one Dec). They are the best estimate
  from this file, and they will steady as more months arrive — re-run
  the forecast every month.
- **The trend is a straight line.** It cannot see a new competitor,
  a price change or a supply shock. If the shop changes, the forecast
  must be re-run, not defended.
- **The backtest is 3 months.** A 3-month MAPE is an honest signal,
  not a guarantee — the What-If sheet exists so the owner can
  stress-test the plan against slower growth.
- **Open it in Excel or Google Sheets to see the numbers.** The
  workbook carries live formulas (openpyxl writes formulas, not cached
  values), so they calculate when the file is opened — a raw file
  reader that does not calculate formulas will show blanks instead of
  KPI values.

## How to run it (under 5 steps)

First time only: `pip install -r requirements.txt` (only openpyxl;
the forecast itself is Python stdlib).

1. `python3 src/generate_data.py` — makes the demo file (skip this on
   a real client file; put theirs at `data/raw/monthly_sales_SAMPLE.csv`).
2. `python3 src/forecast.py` — computes indices, trend, forecast and backtest.
3. `python3 src/build_sqlite.py` — loads everything into SQLite.
4. `python3 src/analyze.py` — regenerates the report.
5. `python3 src/build_workbook.py` — rebuilds the workbook.
6. `python3 src/checks.py` — 132 checks, all must pass.
7. Open `outputs/sales_forecast_SAMPLE.xlsx` — that is the deliverable.
8. To reuse it for a real client: put their file in place of the demo
   one and re-run steps 2–6 — the report, the workbook and the checks
   rebuild themselves from the new rows, and the SQL in
   `sql/forecast_model.sql` stays with the client for next month's
   re-forecast.

## Tools

- Python 3.12 (stdlib forecast; openpyxl 3.1.2 for the workbook)
- SQLite (star-lite schema) · Excel / Google Sheets (the client's tool)

## Data source note

**SAMPLE data, generated 11 Nov 2026 for this forecast** (seeded
Python generator, fictional shop "Noor Electronics"). No real shop,
customer or payment is involved. The forecast, the SQL, the workbook
and the report are the product; the numbers exist to prove them.

## Repo standard note

This paid project follows the portfolio repo standard (Master Plan
§3.2): README + data dictionary (`data/README.md`) + the deliverable
workbook + reproducible scripts + a Fiverr-ready package note
(`PACKAGE-NOTE.md`). The workbook is the deliverable a buyer opens;
the scripts are the proof it was built, not typed.
