# Sales Forecast Report — Noor Electronics, Lahore (SAMPLE)

**Shop (SAMPLE):** Noor Electronics, Lahore · **History:** Jan 2024 – Oct 2025 · **Forecast:** Nov 2025 – Apr 2026 (6 months) · **Report:** 11 Nov 2026

> ⚠️ **What this is and is not.** The monthly sales file is a fictional shop's demo data, generated to show the method. No real shop, customer or payment is involved. What is real is the method: the same trend + seasonal index forecast, the same SQL and the same workbook run on a real client's file the same way, and every number in this report is recomputed from the data, never typed.

## Business question it answers

> "How much will we sell in the next 6 months — and how much stock and cash should we plan for?"

The forecast is a classical decomposition: a straight-line trend fitted to deseasonalised monthly sales, multiplied by a calendar-month seasonal index estimated from the shop's own 22 months. The workbook (`sales_forecast_SAMPLE.xlsx`) carries the same numbers as live formulas, and the What-If sheet lets the owner change the growth rate and the seasonal uplift and watch the forecast move.

## Headline numbers

- **22 months of history** (Jan 2024 – Oct 2025), **PKR 68,170,300** total sales, **PKR 3,098,650** a month on average.
- **Best month: Jun 2025 — PKR 3,879,400**; weakest: Jan 2024 — PKR 2,226,100.
- **Next 6 months forecast: PKR 21,306,134** (PKR 3,551,022 a month), **3.1% vs the last 6 months** (PKR 20,669,900).
- **Backtest: 4.82% MAPE** — holding out Aug–Oct 2025, the model was off by 4.82% on average. That is the honest error to plan around, not a promise.
- **Trend: +PKR 38,079 a month** on deseasonalised sales — the shop is growing, slowly and steadily.

## 3 key findings

1. **The peak is coming in March, not December.** Mar 2026 is forecast at PKR 4,133,046 — the highest of the six months — because Ramadan and Eid al-Fitr fall in March 2026 and the shop's own history peaks there (seasonal index 1.1213). *So what:* stock for March should be ordered in February, not after the rush starts.
2. **January is the planning month, not a problem month.** January is forecast at PKR 2,895,012 — the lowest of the six — because the winter dip is in the shop's own data (seasonal index 0.802). *So what:* use January to clear slow stock and negotiate supplier terms, not to judge the business.
3. **The model is honest about its error.** The backtest missed Aug–Oct 2025 by 4.82% on average (Aug 2025 6.49%, Sep 2025 1.52%, Oct 2025 6.44%). *So what:* plan cash and stock on the forecast minus 4.82%, and treat the forecast as a planning range, not a target to hit to the rupee.

## Forecast — Nov 2025 to Apr 2026

| Month | Seasonal index | Trend (PKR) | Forecast (PKR) | Share |
|---|---:|---:|---:|---:|
| Nov 2025 | 1.0804 | 3,533,722 | 3,817,695 | 17.9% |
| Dec 2025 | 0.8995 | 3,571,800 | 3,212,849 | 15.1% |
| Jan 2026 | 0.802 | 3,609,879 | 2,895,012 | 13.6% |
| Feb 2026 | 0.8751 | 3,647,958 | 3,192,505 | 15.0% |
| Mar 2026 | 1.1213 | 3,686,036 | 4,133,046 | 19.4% |
| Apr 2026 | 1.0889 | 3,724,115 | 4,055,027 | 19.0% |
| **TOTAL** | — | — | **21,306,134** | **100%** |

## Backtest — what the model would have said about Aug–Oct 2025

Fitted on Jan 2024 – Jul 2025 only, then forecast the last 3 months the model had never seen:

| Month | Actual (PKR) | Forecast (PKR) | Error (PKR) | Error % |
|---|---:|---:|---:|---:|
| Aug 2025 | 3,238,900 | 3,028,665 | -210,235 | 6.49% |
| Sep 2025 | 3,347,000 | 3,296,157 | -50,843 | 1.52% |
| Oct 2025 | 3,608,700 | 3,376,142 | -232,558 | 6.44% |
| **MAPE** | — | — | — | **4.82%** |

## How to use it on a real file

1. Put the client's monthly sales file at `data/raw/monthly_sales_SAMPLE.csv` (same columns: month, year, month_no, sales_pkr, orders, units, plus one column per category).
2. Re-run `python3 src/generate_data.py` is skipped — instead `python3 src/forecast.py`, `python3 src/build_sqlite.py`, `python3 src/analyze.py`, `python3 src/build_workbook.py`, `python3 src/checks.py` — the report, the workbook and the checks rebuild themselves from the new rows.
3. The SQL in `sql/forecast_model.sql` stays with the client: re-running it on next month's sales re-forecasts the next 6 months the same way.

## Limits — what this delivery does not do

- **Demo data, 22 months.** A real client's file has its own growth, its own seasonality and its own category mix — the numbers here describe Noor Electronics' sample, not any real shop.
- **Seasonal indices for Nov and Dec rest on one observation each** (the file has only one Nov and one Dec). They are the best estimate from this file, and they will steady as more months arrive — re-run the forecast every month.
- **The trend is a straight line.** It cannot see a new competitor, a price change or a supply shock. If the shop changes, the forecast must be re-run, not defended.
- **The backtest is 3 months.** A 3-month MAPE is an honest signal, not a guarantee — the What-If sheet exists so the owner can stress-test the plan against slower growth.

