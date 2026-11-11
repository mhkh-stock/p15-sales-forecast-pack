#!/usr/bin/env python3
"""Forecast model for P15 (Sales Forecast Pack) — stdlib only.

Method (classical decomposition, trend + seasonal index):
  1. Seasonal index per calendar month: mean sales in that month
     divided by the grand mean of all months, normalised so the 12
     indices average exactly 1.0.
  2. Deseasonalise: y_t = sales_t / index(month_t).
  3. Trend: ordinary least squares of y_t on t = 0..21
     (Jan 2024 = 0). Slope/intercept from the closed-form OLS
     formulas — no numpy, no pandas.
  4. Forecast Nov 2025 – Apr 2026 (t = 22..27):
     forecast = trend(t) * index(month).
  5. Backtest (honest, no leakage): re-fit steps 1–3 on Jan 2024 –
     Jul 2025 only (19 months) and forecast Aug–Oct 2025; report
     per-month error and MAPE.

Run: python3 src/forecast.py   (after src/generate_data.py)
Outputs: data/processed/seasonal_indices.csv,
         data/processed/forecast.csv, data/processed/backtest.csv,
         outputs/forecast_summary.json
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "monthly_sales_SAMPLE.csv"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FORECAST_MONTHS = [("Nov 2025", 2025, 11, 22), ("Dec 2025", 2025, 12, 23),
                   ("Jan 2026", 2026, 1, 24), ("Feb 2026", 2026, 2, 25),
                   ("Mar 2026", 2026, 3, 26), ("Apr 2026", 2026, 4, 27)]
BACKTEST_MONTHS = 3  # hold out the last 3 months (Aug–Oct 2025)


def ols(xs, ys):
    """Closed-form OLS: returns (intercept, slope)."""
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    intercept = (sy - slope * sx) / n
    return intercept, slope


def seasonal_indices(rows):
    """Calendar-month index = mean sales in that month / grand mean,
    normalised so the 12 indices average 1.0. Months with a single
    observation (Nov, Dec) use that one month."""
    grand = sum(r["sales"] for r in rows) / len(rows)
    raw = {}
    for m in range(1, 13):
        vals = [r["sales"] for r in rows if r["month_no"] == m]
        raw[m] = (sum(vals) / len(vals)) / grand if vals else 1.0
    mean_raw = sum(raw.values()) / 12
    return {m: raw[m] / mean_raw for m in range(1, 13)}


def fit(rows):
    """Fit (indices, intercept, slope) on the given rows."""
    idx = seasonal_indices(rows)
    xs = list(range(len(rows)))
    ys = [r["sales"] / idx[r["month_no"]] for r in rows]
    intercept, slope = ols(xs, ys)
    return idx, intercept, slope


def predict(idx, intercept, slope, t, month_no):
    return (intercept + slope * t) * idx[month_no]


def main():
    raw = list(csv.DictReader(open(RAW, encoding="utf-8")))
    rows = [{"month": r["month"], "year": int(r["year"]),
             "month_no": int(r["month_no"]), "sales": int(r["sales_pkr"]),
             "orders": int(r["orders"]), "units": int(r["units"])}
            for r in raw]
    assert len(rows) == 22, f"expected 22 months, got {len(rows)}"

    # --- full fit + 6-month forecast ---
    idx, intercept, slope = fit(rows)
    forecast = []
    for name, year, month_no, t in FORECAST_MONTHS:
        trend = intercept + slope * t
        fc = predict(idx, intercept, slope, t, month_no)
        forecast.append({"month": name, "year": year, "month_no": month_no,
                         "t": t, "seasonal_index": round(idx[month_no], 4),
                         "trend_pkr": round(trend),
                         "forecast_pkr": round(fc)})
    fc_total = sum(f["forecast_pkr"] for f in forecast)
    for f in forecast:
        f["share_pct"] = round(100 * f["forecast_pkr"] / fc_total, 1)

    # --- backtest: fit on the first 19 months, forecast the last 3 ---
    train, test = rows[:-BACKTEST_MONTHS], rows[-BACKTEST_MONTHS:]
    b_idx, b_intercept, b_slope = fit(train)
    backtest = []
    for i, r in enumerate(test):
        t = len(train) + i
        fc = predict(b_idx, b_intercept, b_slope, t, r["month_no"])
        ape = abs(fc - r["sales"]) / r["sales"]
        backtest.append({"month": r["month"], "t": t,
                         "month_no": r["month_no"],
                         "actual_pkr": r["sales"],
                         "forecast_pkr": round(fc),
                         "error_pkr": round(fc) - r["sales"],
                         "ape_pct": round(100 * ape, 2)})
    mape = round(sum(b["ape_pct"] for b in backtest) / len(backtest), 2)

    # --- summary ---
    total = sum(r["sales"] for r in rows)
    best = max(rows, key=lambda r: r["sales"])
    last6 = sum(r["sales"] for r in rows[-6:])
    last3_avg = round(sum(r["sales"] for r in rows[-3:]) / 3)
    summary = {
        "shop": "Noor Electronics, Lahore (SAMPLE)",
        "period": "Jan 2024 – Oct 2025",
        "snapshot_date": "2025-10-31",
        "forecast_period": "Nov 2025 – Apr 2026 (6 months)",
        "method": "Classical decomposition: OLS trend on deseasonalised "
                  "sales + calendar-month seasonal index (stdlib only)",
        "history_months": len(rows),
        "history_total_pkr": total,
        "avg_monthly_pkr": round(total / len(rows)),
        "best_month": best["month"],
        "best_month_sales_pkr": best["sales"],
        "worst_month": min(rows, key=lambda r: r["sales"])["month"],
        "worst_month_sales_pkr": min(r["sales"] for r in rows),
        "last_3m_avg_pkr": last3_avg,
        "last_6m_total_pkr": last6,
        "total_orders": sum(r["orders"] for r in rows),
        "total_units": sum(r["units"] for r in rows),
        "trend_intercept_pkr": intercept,
        "trend_slope_pkr_per_month": slope,
        "seasonal_indices": {MONTH_NAMES[m - 1]: idx[m]
                             for m in range(1, 13)},
        "forecast": forecast,
        "forecast_total_pkr": fc_total,
        "forecast_avg_pkr": round(fc_total / len(forecast)),
        "forecast_growth_vs_last6_pct":
            round(100 * (fc_total / last6 - 1), 1),
        "backtest": {
            "train_months": len(train),
            "months": backtest,
            "mape_pct": mape,
            "trend_intercept_pkr": b_intercept,
            "trend_slope_pkr_per_month": b_slope,
            "seasonal_indices": {MONTH_NAMES[m - 1]: b_idx[m]
                                 for m in range(1, 13)},
        },
    }

    PROC.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(PROC / "seasonal_indices.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["month_no", "month", "index_full_fit",
                    "index_backtest_fit"])
        for m in range(1, 13):
            w.writerow([m, MONTH_NAMES[m - 1], round(idx[m], 4),
                        round(b_idx[m], 4)])
    with open(PROC / "forecast.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(forecast[0].keys()))
        w.writeheader()
        w.writerows(forecast)
    with open(PROC / "backtest.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(backtest[0].keys()))
        w.writeheader()
        w.writerows(backtest)
    (OUT / "forecast_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"history PKR {total:,} over {len(rows)} months "
          f"(avg PKR {total // len(rows):,})")
    print(f"forecast Nov 2025–Apr 2026: PKR {fc_total:,} "
          f"(avg PKR {fc_total // 6:,} / month)")
    print(f"backtest MAPE (Aug–Oct 2025): {mape}%")
    print(f"trend: intercept PKR {intercept:,.0f}, "
          f"slope PKR {slope:,.0f} / month")


if __name__ == "__main__":
    main()
