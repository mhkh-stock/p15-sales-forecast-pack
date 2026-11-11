#!/usr/bin/env python3
"""Generate the SAMPLE monthly sales file for P15 (Sales Forecast Pack).

Fictional shop: Noor Electronics, Lahore — electronics retailer,
Jan 2024 – Oct 2025 (22 months). Monthly totals are built from a
base level, a steady growth trend and a Pakistani electronics
seasonality: Ramadan / Eid peaks (Mar–Apr, Jun), a summer cooling
peak (Jun–Jul), a wedding-season lift (Nov) and a winter dip
(Dec–Jan). Nothing here is real client data — the forecast method is
the product, the file proves it.

Run: python3 src/generate_data.py
Outputs: data/raw/monthly_sales_SAMPLE.csv
"""
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SEED = 20261111

BASE = 2_600_000        # PKR/month at t = 0 (Jan 2024), before seasonality
GROWTH = 0.015          # +1.5% trend growth per month
# Calendar-month seasonal factors (mean = 1.0 by construction).
SEASON = {1: 0.86, 2: 0.92, 3: 1.16, 4: 1.10, 5: 0.98, 6: 1.14,
          7: 1.04, 8: 0.96, 9: 0.97, 10: 1.02, 11: 1.09, 12: 0.90}
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# Ramadan / Eid notes (Ramadan 2024: ~11 Mar–9 Apr, Eid al-Fitr 10 Apr;
# Ramadan 2025: ~1–29 Mar, Eid al-Fitr 30 Mar; Eid al-Adha 2024: 17 Jun,
# 2025: 7 Jun).
NOTES = {
    (2024, 3): "Ramadan — pre-Eid shopping peak",
    (2024, 4): "Eid al-Fitr — peak",
    (2024, 6): "Eid al-Adha + summer cooling demand",
    (2024, 11): "Wedding season",
    (2025, 3): "Ramadan + Eid al-Fitr — peak",
    (2025, 6): "Eid al-Adha + summer cooling demand",
    (2025, 11): "—",
    (2024, 1): "Winter dip",
    (2025, 1): "Winter dip",
    (2024, 12): "Winter dip",
}

CATEGORIES = [
    # (name, base share, avg ticket PKR for unit counts)
    ("Mobiles & Tablets", 0.34, 42_000),
    ("TVs & Audio", 0.22, 65_000),
    ("Home Appliances", 0.20, 28_000),
    ("Fans & Cooling", 0.12, 9_500),
    ("Accessories", 0.12, 2_800),
]
# Fans & Cooling share shifts with the season (summer up, winter down).
FAN_SHIFT = {5: 0.05, 6: 0.08, 7: 0.08, 8: 0.05,
             12: -0.05, 1: -0.05, 2: -0.03}


def main():
    rng = random.Random(SEED)
    rows = []
    t = 0
    for year in (2024, 2025):
        for month in range(1, 13):
            if year == 2025 and month > 10:
                break
            noise = rng.uniform(0.96, 1.04)
            total = round(BASE * (1 + GROWTH) ** t
                          * SEASON[month] * noise / 100) * 100

            # Category split: base shares, Fans & Cooling shifted by
            # season, small noise, renormalised; last category takes
            # the rounding remainder so the categories sum exactly.
            shares = []
            for name, base, _ in CATEGORIES:
                s = base + rng.uniform(-0.015, 0.015)
                if name == "Fans & Cooling":
                    s += FAN_SHIFT.get(month, 0.0)
                shares.append(max(0.02, s))
            scale = sum(shares)
            shares = [s / scale for s in shares]
            cat_sales = []
            running = 0
            for i, (name, _, _) in enumerate(CATEGORIES):
                if i == len(CATEGORIES) - 1:
                    cat_sales.append(total - running)
                else:
                    v = round(total * shares[i] / 100) * 100
                    cat_sales.append(v)
                    running += v

            units = sum(round(cs / price)
                        for cs, (_, _, price) in zip(cat_sales, CATEGORIES))
            avg_ticket = round(14_500 * rng.uniform(0.95, 1.05))
            orders = round(total / avg_ticket)
            rows.append({
                "month": f"{MONTH_NAMES[month - 1]} {year}",
                "year": str(year),
                "month_no": str(month),
                "sales_pkr": str(total),
                "orders": str(orders),
                "units": str(units),
                "mobiles_pkr": str(cat_sales[0]),
                "tvs_audio_pkr": str(cat_sales[1]),
                "home_appliances_pkr": str(cat_sales[2]),
                "fans_cooling_pkr": str(cat_sales[3]),
                "accessories_pkr": str(cat_sales[4]),
                "notes": NOTES.get((year, month), ""),
            })
            t += 1

    RAW.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with open(RAW / "monthly_sales_SAMPLE.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    total = sum(int(r["sales_pkr"]) for r in rows)
    print(f"wrote {len(rows)} months, total PKR {total:,}, "
          f"avg PKR {total // len(rows):,} / month")
    print(f"range: {rows[0]['month']} .. {rows[-1]['month']}, "
          f"best {max(rows, key=lambda r: int(r['sales_pkr']))['month']} "
          f"PKR {max(int(r['sales_pkr']) for r in rows):,}")


if __name__ == "__main__":
    main()
