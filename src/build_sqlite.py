#!/usr/bin/env python3
"""Load the SAMPLE monthly sales + forecast into SQLite (P15).

Star-lite model: dim_month (22 months) + dim_category (5 categories)
+ fact_monthly_sales (22 x 5 category rows) + fact_monthly_totals
(22 rows) + fact_forecast (6 rows). Rebuildable from the pushed
scripts and CSVs — the .db is NOT uploaded.

Run: python3 src/build_sqlite.py   (after src/forecast.py)
Output: data/processed/sales.db
"""
import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "monthly_sales_SAMPLE.csv"
FORECAST = ROOT / "data" / "processed" / "forecast.csv"
DB = ROOT / "data" / "processed" / "sales.db"
SCHEMA = ROOT / "sql" / "schema.sql"

CATEGORIES = [
    ("MOB", "Mobiles & Tablets", 42_000, "mobiles_pkr"),
    ("TV", "TVs & Audio", 65_000, "tvs_audio_pkr"),
    ("HOME", "Home Appliances", 28_000, "home_appliances_pkr"),
    ("FAN", "Fans & Cooling", 9_500, "fans_cooling_pkr"),
    ("ACC", "Accessories", 2_800, "accessories_pkr"),
]


def main():
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA.read_text(encoding="utf-8"))
    con.executemany("INSERT INTO dim_category VALUES (?,?,?)",
                    [(c, n, p) for c, n, p, _ in CATEGORIES])

    rows = list(csv.DictReader(open(RAW, encoding="utf-8")))
    for t, r in enumerate(rows):
        key = f"{r['year']}-{int(r['month_no']):02d}"
        con.execute(
            "INSERT INTO dim_month VALUES (?,?,?,?,?)",
            (key, r["month"], int(r["year"]), int(r["month_no"]), t))
        con.execute(
            "INSERT INTO fact_monthly_totals VALUES (?,?,?,?)",
            (key, int(r["sales_pkr"]), int(r["orders"]), int(r["units"])))
        for code, _, _, col in CATEGORIES:
            con.execute(
                "INSERT INTO fact_monthly_sales VALUES (?,?,?,?)",
                (key, code, int(r[col]),
                 round(int(r[col]) / dict((c, p) for c, _, p, _ in CATEGORIES)[code])))

    fc = list(csv.DictReader(open(FORECAST, encoding="utf-8")))
    for f in fc:
        key = f"{f['year']}-{int(f['month_no']):02d}"
        con.execute(
            "INSERT INTO fact_forecast VALUES (?,?,?,?,?,?,?,?)",
            (key, f["month"], int(f["year"]), int(f["month_no"]),
             int(f["t"]), float(f["seasonal_index"]),
             int(f["trend_pkr"]), int(f["forecast_pkr"])))
    con.commit()
    n_m = con.execute("SELECT COUNT(*) FROM dim_month").fetchone()[0]
    n_s = con.execute("SELECT COUNT(*) FROM fact_monthly_sales").fetchone()[0]
    total = con.execute("SELECT SUM(sales_pkr) FROM fact_monthly_totals").fetchone()[0]
    n_f = con.execute("SELECT COUNT(*) FROM fact_forecast").fetchone()[0]
    con.close()
    print(f"sales.db: {n_m} months, {n_s} category rows, "
          f"PKR {total:,} total, {n_f} forecast months")


if __name__ == "__main__":
    main()
