#!/usr/bin/env python3
"""Data-quality + reconciliation checks as code for P15.

Verifies: file shape, money reconciliation, seasonal indices,
the OLS trend recomputed independently, the forecast and the
backtest recomputed independently, SQL-vs-Python agreement,
SQLite integrity, the workbook structure and formulas, the
report's headline numbers, and — when outputs/.recalc/
sales_forecast_SAMPLE.xlsx exists (built by the LibreOffice recalc
step) — that every live-formula KPI in the workbook calculates to
exactly the Python number.

Run: python3 src/checks.py        (after the full pipeline + recalc)
All checks must pass. A failure prints FAILED and exits non-zero.
"""
import csv
import json
import sqlite3
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "monthly_sales_SAMPLE.csv"
INDICES = ROOT / "data" / "processed" / "seasonal_indices.csv"
FORECAST_CSV = ROOT / "data" / "processed" / "forecast.csv"
BACKTEST_CSV = ROOT / "data" / "processed" / "backtest.csv"
DB = ROOT / "data" / "processed" / "sales.db"
SUMMARY = ROOT / "outputs" / "forecast_summary.json"
REPORT = ROOT / "outputs" / "forecast_report.md"
WORKBOOK = ROOT / "outputs" / "sales_forecast_SAMPLE.xlsx"
RECALC = ROOT / "outputs" / ".recalc" / "sales_forecast_SAMPLE.xlsx"
SQL = ROOT / "sql" / "forecast_model.sql"
README = ROOT / "README.md"

CAT_COLS = ["mobiles_pkr", "tvs_audio_pkr", "home_appliances_pkr",
            "fans_cooling_pkr", "accessories_pkr"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

passed = failed = 0
failures = []


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
    else:
        failed += 1
        failures.append(f"{name}: {detail}")
        print(f"  FAILED: {name} — {detail}")


def ols(xs, ys):
    """Independent OLS recompute (same closed form, separate code)."""
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    return (sy - slope * sx) / n, slope


def indices_for(rows):
    grand = sum(r["sales"] for r in rows) / len(rows)
    raw = {}
    for m in range(1, 13):
        vals = [r["sales"] for r in rows if r["month_no"] == m]
        raw[m] = (sum(vals) / len(vals)) / grand if vals else 1.0
    mean_raw = sum(raw.values()) / 12
    return {m: raw[m] / mean_raw for m in range(1, 13)}


def main():
    raw = list(csv.DictReader(open(RAW, encoding="utf-8")))
    rows = [{"month": r["month"], "month_no": int(r["month_no"]),
             "sales": int(r["sales_pkr"]), "orders": int(r["orders"]),
             "units": int(r["units"])}
            for r in raw]
    idx_csv = {int(r["month_no"]): float(r["index_full_fit"])
               for r in csv.DictReader(open(INDICES, encoding="utf-8"))}
    fc_csv = list(csv.DictReader(open(FORECAST_CSV, encoding="utf-8")))
    bt_csv = list(csv.DictReader(open(BACKTEST_CSV, encoding="utf-8")))
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    report = REPORT.read_text(encoding="utf-8")
    total = sum(r["sales"] for r in rows)

    # --- file shape ---
    check("raw rows = 22", len(rows) == 22, f"got {len(rows)}")
    check("raw columns exact",
          list(raw[0].keys()) == ["month", "year", "month_no", "sales_pkr",
              "orders", "units", "mobiles_pkr", "tvs_audio_pkr",
              "home_appliances_pkr", "fans_cooling_pkr",
              "accessories_pkr", "notes"])
    check("months Jan 2024..Oct 2025 in order",
          [r["month"] for r in rows] ==
          [f"{MONTH_NAMES[m - 1]} {y}" for y in (2024, 2025)
           for m in range(1, 13) if not (y == 2025 and m > 10)])
    check("all sales > 0", all(r["sales"] > 0 for r in rows))
    check("all orders > 0 and units > 0",
          all(r["orders"] > 0 and r["units"] > 0 for r in rows))
    check("sales rounded to nearest 100",
          all(r["sales"] % 100 == 0 for r in rows))

    # --- money reconciliation ---
    check("categories sum to monthly total on every row",
          all(sum(int(r[c]) for c in CAT_COLS) == int(r["sales_pkr"])
              for r in raw))
    check("history total = summary total",
          total == s["history_total_pkr"], f"{total} vs {s['history_total_pkr']}")
    check("avg monthly = total / 22",
          s["avg_monthly_pkr"] == round(total / 22))
    check("last 6m total = May–Oct 2025",
          s["last_6m_total_pkr"] == sum(r["sales"] for r in rows[-6:]))
    check("last 3m avg = Aug–Oct 2025 avg",
          s["last_3m_avg_pkr"] == round(sum(r["sales"] for r in rows[-3:]) / 3))
    check("total orders/units match summary",
          sum(r["orders"] for r in rows) == s["total_orders"]
          and sum(r["units"] for r in rows) == s["total_units"])
    check("best month matches summary",
          s["best_month"] == max(rows, key=lambda r: r["sales"])["month"]
          and s["best_month_sales_pkr"] == max(r["sales"] for r in rows))

    # --- seasonal indices (independent recompute) ---
    idx = indices_for(rows)
    check("seasonal indices mean = 1.0",
          abs(sum(idx.values()) / 12 - 1.0) < 1e-9,
          f"{sum(idx.values()) / 12}")
    check("seasonal indices all in 0.7..1.3",
          all(0.7 < v < 1.3 for v in idx.values()))
    for m in range(1, 13):
        check(f"index {MONTH_NAMES[m - 1]} matches summary",
              abs(idx[m] - s["seasonal_indices"][MONTH_NAMES[m - 1]]) < 0.00005,
              f"{idx[m]} vs {s['seasonal_indices'][MONTH_NAMES[m - 1]]}")
        check(f"index {MONTH_NAMES[m - 1]} matches indices CSV",
              abs(idx[m] - idx_csv[m]) < 0.00005)

    # --- trend + forecast (independent recompute) ---
    xs = list(range(22))
    ys = [r["sales"] / idx[r["month_no"]] for r in rows]
    intercept, slope = ols(xs, ys)
    check("trend intercept matches summary",
          abs(intercept - s["trend_intercept_pkr"]) < 1.0,
          f"{intercept} vs {s['trend_intercept_pkr']}")
    check("trend slope matches summary",
          abs(slope - s["trend_slope_pkr_per_month"]) < 1.0,
          f"{slope} vs {s['trend_slope_pkr_per_month']}")
    check("trend slope positive (shop is growing)", slope > 0)
    check("forecast rows = 6", len(fc_csv) == 6)
    for f in fc_csv:
        t, m = int(f["t"]), int(f["month_no"])
        want = round((intercept + slope * t) * idx[m])
        check(f"forecast {f['month']} recomputed",
              abs(int(f["forecast_pkr"]) - want) <= 1,
              f"{f['forecast_pkr']} vs {want}")
        check(f"forecast {f['month']} trend recomputed",
              abs(int(f["trend_pkr"]) - round(intercept + slope * t)) <= 1)
    check("forecast total = sum of months",
          s["forecast_total_pkr"] == sum(int(f["forecast_pkr"]) for f in fc_csv))
    check("forecast avg = total / 6",
          s["forecast_avg_pkr"] == round(s["forecast_total_pkr"] / 6))
    check("forecast growth vs last 6m recomputed",
          s["forecast_growth_vs_last6_pct"]
          == round(100 * (s["forecast_total_pkr"] / s["last_6m_total_pkr"] - 1), 1))

    # --- backtest (independent recompute, fit on first 19 months) ---
    train, test = rows[:-3], rows[-3:]
    b_idx = indices_for(train)
    b_xs = list(range(19))
    b_ys = [r["sales"] / b_idx[r["month_no"]] for r in train]
    b_intercept, b_slope = ols(b_xs, b_ys)
    check("backtest intercept matches summary",
          abs(b_intercept - s["backtest"]["trend_intercept_pkr"]) < 1.0)
    check("backtest slope matches summary",
          abs(b_slope - s["backtest"]["trend_slope_pkr_per_month"]) < 1.0)
    check("backtest rows = 3", len(bt_csv) == 3)
    apes = []
    for i, b in enumerate(bt_csv):
        t = 19 + i
        want = round((b_intercept + b_slope * t) * b_idx[test[i]["month_no"]])
        check(f"backtest {b['month']} forecast recomputed",
              abs(int(b["forecast_pkr"]) - want) <= 1,
              f"{b['forecast_pkr']} vs {want}")
        check(f"backtest {b['month']} actual matches history",
              int(b["actual_pkr"]) == test[i]["sales"])
        ape = abs(int(b["forecast_pkr"]) - int(b["actual_pkr"])) / int(b["actual_pkr"])
        apes.append(ape)
        check(f"backtest {b['month']} APE recomputed",
              abs(float(b["ape_pct"]) - round(100 * ape, 2)) < 0.01)
    check("backtest MAPE recomputed",
          abs(s["backtest"]["mape_pct"] - round(100 * sum(apes) / 3, 2)) < 0.01,
          f"{s['backtest']['mape_pct']} vs {round(100 * sum(apes) / 3, 2)}")

    # --- SQL vs Python ---
    con = sqlite3.connect(DB)
    sql_rows = con.execute(SQL.read_text(encoding="utf-8")).fetchall()
    check("SQL forecast returns 6 rows", len(sql_rows) == 6, f"got {len(sql_rows)}")
    for (month, t, sidx, trend, fc_sql), f in zip(sql_rows, fc_csv):
        check(f"SQL forecast {month} within 1% of Python",
              abs(fc_sql - int(f["forecast_pkr"])) <= 0.01 * int(f["forecast_pkr"]),
              f"SQL {fc_sql} vs Python {f['forecast_pkr']}")

    # --- SQLite integrity ---
    check("SQLite months = 22",
          con.execute("SELECT COUNT(*) FROM dim_month").fetchone()[0] == 22)
    check("SQLite category rows = 110",
          con.execute("SELECT COUNT(*) FROM fact_monthly_sales").fetchone()[0] == 110)
    check("SQLite totals = 22",
          con.execute("SELECT COUNT(*) FROM fact_monthly_totals").fetchone()[0] == 22)
    check("SQLite revenue = total",
          con.execute("SELECT SUM(sales_pkr) FROM fact_monthly_totals").fetchone()[0]
          == total)
    check("SQLite category sums = monthly totals",
          con.execute("SELECT COUNT(*) FROM fact_monthly_totals t WHERE "
                      "t.sales_pkr <> (SELECT SUM(sales_pkr) FROM "
                      "fact_monthly_sales s WHERE s.month_key = t.month_key)")
          .fetchone()[0] == 0)
    check("SQLite no orphan category rows",
          con.execute("SELECT COUNT(*) FROM fact_monthly_sales s LEFT JOIN "
                      "dim_month m ON s.month_key = m.month_key "
                      "WHERE m.month_key IS NULL").fetchone()[0] == 0)
    check("SQLite forecast rows = 6",
          con.execute("SELECT COUNT(*) FROM fact_forecast").fetchone()[0] == 6)
    check("SQLite forecast total = summary",
          con.execute("SELECT SUM(forecast_pkr) FROM fact_forecast").fetchone()[0]
          == s["forecast_total_pkr"])
    con.close()

    # --- workbook structure + formulas ---
    wb = load_workbook(WORKBOOK)
    check("workbook sheets",
          wb.sheetnames == ["Dashboard", "Method", "History", "Forecast",
                            "Backtest", "What-If"],
          f"{wb.sheetnames}")
    hs = wb["History"]
    check("History rows = 22", hs.max_row == 24, f"max_row {hs.max_row}")
    check("History avg-order cells are formulas",
          all(isinstance(hs.cell(row=r, column=5).value, str)
              and hs.cell(row=r, column=5).value.startswith("=")
              for r in range(2, 24)))
    check("History seasonal-index cells are formulas",
          all(isinstance(hs.cell(row=r, column=13).value, str)
              and hs.cell(row=r, column=13).value.startswith("=INDEX")
              for r in range(2, 24)))
    check("History trend cells are formulas",
          all(isinstance(hs.cell(row=r, column=14).value, str)
              and hs.cell(row=r, column=14).value.startswith("=Method!")
              for r in range(2, 24)))
    check("History fitted cells are formulas",
          all(isinstance(hs.cell(row=r, column=15).value, str)
              and hs.cell(row=r, column=15).value.startswith("=")
              for r in range(2, 24)))
    check("History sales values match raw CSV",
          all(hs.cell(row=2 + i, column=2).value == rows[i]["sales"]
              for i in range(22)))
    fc_ws = wb["Forecast"]
    check("Forecast rows = 6", fc_ws.max_row == 8, f"max_row {fc_ws.max_row}")
    check("Forecast cells are formulas",
          all(isinstance(fc_ws.cell(row=r, column=c).value, str)
              and fc_ws.cell(row=r, column=c).value.startswith("=")
              for r in range(2, 8) for c in (4, 5, 6, 7, 8)))
    bt_ws = wb["Backtest"]
    check("Backtest forecast cells are formulas",
          all(isinstance(bt_ws.cell(row=r, column=5).value, str)
              and bt_ws.cell(row=r, column=5).value.startswith("=")
              for r in range(2, 5)))
    check("Backtest MAPE cell is a formula",
          isinstance(bt_ws["G5"].value, str) and bt_ws["G5"].value.startswith("="))
    wi = wb["What-If"]
    check("What-If inputs are 0% (base case)",
          wi["B3"].value == 0 and wi["B4"].value == 0)
    check("What-If forecast cells are formulas",
          all(isinstance(wi.cell(row=r, column=c).value, str)
              and wi.cell(row=r, column=c).value.startswith("=")
              for r in range(7, 13) for c in (2, 3, 4, 5)))
    db_ws = wb["Dashboard"]
    kpi_formulas = [db_ws.cell(row=r, column=2).value for r in range(5, 18)]
    check("Dashboard KPIs are formulas",
          all(isinstance(v, str) and v.startswith("=") for v in kpi_formulas),
          f"{kpi_formulas}")
    check("Method parameters match summary",
          abs(wb["Method"]["B5"].value - s["trend_intercept_pkr"]) < 1.0
          and abs(wb["Method"]["B6"].value - s["trend_slope_pkr_per_month"]) < 1.0)
    check("Method seasonal table matches summary",
          all(abs(wb["Method"].cell(row=12 + i, column=2).value
                  - s["seasonal_indices"][MONTH_NAMES[i]]) < 0.00005
              for i in range(12)))

    # --- report numbers + SAMPLE labelling ---
    check("report states history total",
          f"{s['history_total_pkr']:,}" in report)
    check("report states forecast total",
          f"{s['forecast_total_pkr']:,}" in report)
    check("report states MAPE", f"{s['backtest']['mape_pct']}%" in report)
    check("report names all 6 forecast months",
          all(f["month"] in report for f in fc_csv))
    readme = README.read_text(encoding="utf-8")
    check("README labels data SAMPLE",
          "SAMPLE" in readme and "Noor Electronics" in readme)
    check("workbook title labels SAMPLE",
          "SAMPLE" in db_ws["A1"].value)

    # --- LibreOffice recalculated values (if the recalc copy exists) ---
    if RECALC.exists():
        wb2 = load_workbook(RECALC, data_only=True)
        d2 = wb2["Dashboard"]
        expected = {
            "B5": s["history_months"], "B6": s["history_total_pkr"],
            "B7": s["avg_monthly_pkr"],
            "B9": s["best_month_sales_pkr"],
            "B10": s["last_3m_avg_pkr"],
            "B11": s["forecast_total_pkr"],
            "B12": s["forecast_avg_pkr"],
            "B15": max(int(f["forecast_pkr"]) for f in fc_csv),
            "B17": s["forecast_total_pkr"],
        }
        for cell, want in expected.items():
            got = d2[cell].value
            check(f"recalc Dashboard {cell} = {want}",
                  got is not None and round(float(got)) == want,
                  f"got {got!r}")
        check("recalc Dashboard best month",
              d2["B8"].value == s["best_month"], f"got {d2['B8'].value!r}")
        check("recalc Dashboard best forecast month",
              d2["B14"].value == max(fc_csv, key=lambda f: int(f["forecast_pkr"]))["month"],
              f"got {d2['B14'].value!r}")
        check("recalc Dashboard MAPE",
              d2["B16"].value is not None
              and round(float(d2["B16"].value) * 100, 2) == s["backtest"]["mape_pct"],
              f"got {d2['B16'].value!r}")
        check("recalc Dashboard forecast growth",
              d2["B13"].value is not None
              and round(float(d2["B13"].value) * 100, 1)
              == s["forecast_growth_vs_last6_pct"],
              f"got {d2['B13'].value!r}")
        f2 = wb2["Forecast"]
        for i, f in enumerate(fc_csv, start=2):
            check(f"recalc Forecast {f['month']}",
                  f2.cell(row=i, column=6).value is not None
                  and round(float(f2.cell(row=i, column=6).value))
                  == int(f["forecast_pkr"]),
                  f"got {f2.cell(row=i, column=6).value!r}")
        check("recalc Forecast TOTAL",
              f2.cell(row=8, column=6).value is not None
              and round(float(f2.cell(row=8, column=6).value))
              == s["forecast_total_pkr"])
        b2 = wb2["Backtest"]
        check("recalc Backtest MAPE",
              b2["G5"].value is not None
              and round(float(b2["G5"].value) * 100, 2) == s["backtest"]["mape_pct"],
              f"got {b2['G5'].value!r}")
        w2 = wb2["What-If"]
        check("recalc What-If total = base forecast at 0%/0%",
              w2["C13"].value is not None
              and round(float(w2["C13"].value)) == s["forecast_total_pkr"],
              f"got {w2['C13'].value!r}")
        h2 = wb2["History"]
        check("recalc History TOTAL sales",
              h2.cell(row=24, column=2).value is not None
              and round(float(h2.cell(row=24, column=2).value)) == total)
        check("recalc History category totals = sales total",
              all(round(float(h2.cell(row=24, column=c).value)) for c in (6, 7, 8, 9, 10))
              and round(sum(float(h2.cell(row=24, column=c).value)
                            for c in (6, 7, 8, 9, 10))) == total)
    else:
        print("  NOTE: no LibreOffice recalc copy found at "
              f"{RECALC} — recalc checks skipped")

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        print("Failures:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
