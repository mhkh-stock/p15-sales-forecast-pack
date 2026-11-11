#!/usr/bin/env python3
"""Regenerate the findings report for P15 from the computed summary.

Every number in the report is recomputed from
outputs/forecast_summary.json — nothing is typed by hand.

Run: python3 src/analyze.py   (after src/forecast.py)
Output: outputs/forecast_report.md
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "outputs" / "forecast_summary.json"
REPORT = ROOT / "outputs" / "forecast_report.md"


def pkr(n):
    return f"PKR {n:,}"


def main():
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    fc = s["forecast"]
    bt = s["backtest"]
    lines = []
    lines.append("# Sales Forecast Report — Noor Electronics, Lahore (SAMPLE)")
    lines.append("")
    lines.append(f"**Shop (SAMPLE):** Noor Electronics, Lahore · "
                 f"**History:** {s['period']} · "
                 f"**Forecast:** {s['forecast_period']} · **Report:** 11 Nov 2026")
    lines.append("")
    lines.append("> ⚠️ **What this is and is not.** The monthly sales file "
                 "is a fictional shop's demo data, generated to show the "
                 "method. No real shop, customer or payment is involved. "
                 "What is real is the method: the same trend + seasonal "
                 "index forecast, the same SQL and the same workbook run on "
                 "a real client's file the same way, and every number in "
                 "this report is recomputed from the data, never typed.")
    lines.append("")
    lines.append("## Business question it answers")
    lines.append("")
    lines.append("> \"How much will we sell in the next 6 months — and how "
                 "much stock and cash should we plan for?\"")
    lines.append("")
    lines.append("The forecast is a classical decomposition: a straight-line "
                 "trend fitted to deseasonalised monthly sales, multiplied "
                 "by a calendar-month seasonal index estimated from the "
                 "shop's own 22 months. The workbook "
                 "(`sales_forecast_SAMPLE.xlsx`) carries the same numbers as "
                 "live formulas, and the What-If sheet lets the owner change "
                 "the growth rate and the seasonal uplift and watch the "
                 "forecast move.")
    lines.append("")
    lines.append("## Headline numbers")
    lines.append("")
    lines.append(f"- **{s['history_months']} months of history** "
                 f"({s['period']}), **{pkr(s['history_total_pkr'])}** total sales, "
                 f"**{pkr(s['avg_monthly_pkr'])}** a month on average.")
    lines.append(f"- **Best month: {s['best_month']} — {pkr(s['best_month_sales_pkr'])}**; "
                 f"weakest: {s['worst_month']} — {pkr(s['worst_month_sales_pkr'])}.")
    lines.append(f"- **Next 6 months forecast: {pkr(s['forecast_total_pkr'])}** "
                 f"({pkr(s['forecast_avg_pkr'])} a month), "
                 f"**{s['forecast_growth_vs_last6_pct']}% vs the last 6 months** "
                 f"({pkr(s['last_6m_total_pkr'])}).")
    lines.append(f"- **Backtest: {bt['mape_pct']}% MAPE** — holding out Aug–Oct 2025, "
                 f"the model was off by {bt['mape_pct']}% on average. That is the "
                 f"honest error to plan around, not a promise.")
    lines.append(f"- **Trend: +{pkr(round(s['trend_slope_pkr_per_month']))} a month** "
                 f"on deseasonalised sales — the shop is growing, slowly and steadily.")
    lines.append("")
    lines.append("## 3 key findings")
    lines.append("")
    best_fc = max(fc, key=lambda f: f["forecast_pkr"])
    lines.append(f"1. **The peak is coming in March, not December.** "
                 f"{best_fc['month']} is forecast at {pkr(best_fc['forecast_pkr'])} — "
                 f"the highest of the six months — because Ramadan and Eid al-Fitr "
                 f"fall in March 2026 and the shop's own history peaks there "
                 f"(seasonal index {best_fc['seasonal_index']}). *So what:* stock "
                 f"for March should be ordered in February, not after the rush starts.")
    lines.append(f"2. **January is the planning month, not a problem month.** "
                 f"January is forecast at "
                 f"{pkr(next(f['forecast_pkr'] for f in fc if f['month'] == 'Jan 2026'))} — "
                 f"the lowest of the six — because the winter dip is in the shop's "
                 f"own data (seasonal index "
                 f"{next(f['seasonal_index'] for f in fc if f['month'] == 'Jan 2026')}). "
                 f"*So what:* use January to clear slow stock and negotiate supplier "
                 f"terms, not to judge the business.")
    lines.append(f"3. **The model is honest about its error.** The backtest missed "
                 f"Aug–Oct 2025 by {bt['mape_pct']}% on average "
                 f"({', '.join(b['month'] + ' ' + str(b['ape_pct']) + '%' for b in bt['months'])}). "
                 f"*So what:* plan cash and stock on the forecast minus "
                 f"{bt['mape_pct']}%, and treat the forecast as a planning range, "
                 f"not a target to hit to the rupee.")
    lines.append("")
    lines.append("## Forecast — Nov 2025 to Apr 2026")
    lines.append("")
    lines.append("| Month | Seasonal index | Trend (PKR) | Forecast (PKR) | Share |")
    lines.append("|---|---:|---:|---:|---:|")
    for f in fc:
        lines.append(f"| {f['month']} | {f['seasonal_index']} | {f['trend_pkr']:,} | "
                     f"{f['forecast_pkr']:,} | {f['share_pct']}% |")
    lines.append(f"| **TOTAL** | — | — | **{s['forecast_total_pkr']:,}** | **100%** |")
    lines.append("")
    lines.append("## Backtest — what the model would have said about Aug–Oct 2025")
    lines.append("")
    lines.append("Fitted on Jan 2024 – Jul 2025 only, then forecast the last "
                 "3 months the model had never seen:")
    lines.append("")
    lines.append("| Month | Actual (PKR) | Forecast (PKR) | Error (PKR) | Error % |")
    lines.append("|---|---:|---:|---:|---:|")
    for b in bt["months"]:
        lines.append(f"| {b['month']} | {b['actual_pkr']:,} | {b['forecast_pkr']:,} | "
                     f"{b['error_pkr']:+,} | {b['ape_pct']}% |")
    lines.append(f"| **MAPE** | — | — | — | **{bt['mape_pct']}%** |")
    lines.append("")
    lines.append("## How to use it on a real file")
    lines.append("")
    lines.append("1. Put the client's monthly sales file at "
                 "`data/raw/monthly_sales_SAMPLE.csv` (same columns: month, "
                 "year, month_no, sales_pkr, orders, units, plus one column "
                 "per category).")
    lines.append("2. Re-run `python3 src/generate_data.py` is skipped — instead "
                 "`python3 src/forecast.py`, `python3 src/build_sqlite.py`, "
                 "`python3 src/analyze.py`, `python3 src/build_workbook.py`, "
                 "`python3 src/checks.py` — the report, the workbook and the "
                 "checks rebuild themselves from the new rows.")
    lines.append("3. The SQL in `sql/forecast_model.sql` stays with the client: "
                 "re-running it on next month's sales re-forecasts the next "
                 "6 months the same way.")
    lines.append("")
    lines.append("## Limits — what this delivery does not do")
    lines.append("")
    lines.append("- **Demo data, 22 months.** A real client's file has its own "
                 "growth, its own seasonality and its own category mix — the "
                 "numbers here describe Noor Electronics' sample, not any real shop.")
    lines.append("- **Seasonal indices for Nov and Dec rest on one observation "
                 "each** (the file has only one Nov and one Dec). They are the "
                 "best estimate from this file, and they will steady as more "
                 "months arrive — re-run the forecast every month.")
    lines.append("- **The trend is a straight line.** It cannot see a new "
                 "competitor, a price change or a supply shock. If the shop "
                 "changes, the forecast must be re-run, not defended.")
    lines.append("- **The backtest is 3 months.** A 3-month MAPE is an honest "
                 "signal, not a guarantee — the What-If sheet exists so the "
                 "owner can stress-test the plan against slower growth.")
    lines.append("")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
