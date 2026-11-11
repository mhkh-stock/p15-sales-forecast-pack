#!/usr/bin/env python3
"""Build the client deliverable workbook for P15 (Noor Electronics, SAMPLE).

Sheets:
  Dashboard — KPIs + forecast at a glance, all LIVE formulas over
              History / Forecast / Backtest / What-If.
  History   — 22 months of actuals + category split (values) and
              seasonal index / trend / fitted (live formulas over
              the Method sheet's parameters).
  Forecast  — Nov 2025–Apr 2026: seasonal index, trend and forecast
              are all live formulas (trend * index).
  Backtest  — Aug–Oct 2025 actual vs the honest hold-out forecast
              (live formulas from the backtest parameters), APE and MAPE.
  What-If   — two editable inputs (extra monthly growth %, seasonal
              uplift %) that recompute all 6 forecast months live.
  Method    — parameters + seasonal index table + how it works.

Run: python3 src/build_workbook.py   (after src/forecast.py)
Output: outputs/sales_forecast_SAMPLE.xlsx
"""
import csv
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "monthly_sales_SAMPLE.csv"
FORECAST = ROOT / "data" / "processed" / "forecast.csv"
BACKTEST = ROOT / "data" / "processed" / "backtest.csv"
SUMMARY = ROOT / "outputs" / "forecast_summary.json"
OUT = ROOT / "outputs" / "sales_forecast_SAMPLE.xlsx"
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

TITLE_FONT = Font(bold=True, size=14)
HEAD_FONT = Font(bold=True, size=11, color="FFFFFF")
HEAD_FILL = PatternFill("solid", fgColor="1F4E5F")
KPI_FONT = Font(bold=True, size=12)
MONEY_FMT = '#,##0'
PCT_FMT = '0.0%'
PCT2_FMT = '0.00%'


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HEAD_FONT
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(horizontal="center", wrap_text=True)


def main():
    raw = list(csv.DictReader(open(RAW, encoding="utf-8")))
    fc = list(csv.DictReader(open(FORECAST, encoding="utf-8")))
    bt = list(csv.DictReader(open(BACKTEST, encoding="utf-8")))
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))
    n = len(raw)  # 22
    last_row = n + 1  # History data rows 2..23

    wb = Workbook()

    # ---------- Method (parameters + seasonal index table) ----------
    md = wb.active
    md.title = "Method"
    md["A1"] = "How the forecast is made — Noor Electronics (SAMPLE)"
    md["A1"].font = TITLE_FONT
    md["A2"] = ("Classical decomposition: OLS trend on deseasonalised "
                "monthly sales × calendar-month seasonal index. "
                "All parameters below are values from src/forecast.py; "
                "every forecast cell in this workbook is a live formula "
                "over them.")
    md["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    md.merge_cells("A2:D2")
    md.row_dimensions[2].height = 30
    md["A4"] = "Model parameters"
    md["A4"].font = Font(bold=True, size=12)
    md["A5"] = "Trend intercept (PKR)"
    md["B5"] = s["trend_intercept_pkr"]
    md["A6"] = "Trend slope (PKR / month)"
    md["B6"] = s["trend_slope_pkr_per_month"]
    md["A7"] = "Backtest intercept (PKR, fit on Jan 2024–Jul 2025)"
    md["B7"] = s["backtest"]["trend_intercept_pkr"]
    md["A8"] = "Backtest slope (PKR / month)"
    md["B8"] = s["backtest"]["trend_slope_pkr_per_month"]
    for r in (5, 6, 7, 8):
        md.cell(row=r, column=2).number_format = MONEY_FMT
    md["A10"] = "Seasonal index table (12 indices average exactly 1.0)"
    md["A10"].font = Font(bold=True, size=12)
    md["A11"] = "Month"
    md["B11"] = "Index (full fit)"
    md["C11"] = "Index (backtest fit)"
    style_header(md, 11, 3)
    for i, name in enumerate(MONTH_NAMES):
        r = 12 + i
        md.cell(row=r, column=1, value=name)
        md.cell(row=r, column=2,
               value=s["seasonal_indices"][name]).number_format = '0.0000'
        md.cell(row=r, column=3,
               value=s["backtest"]["seasonal_indices"][name]).number_format = '0.0000'
    md["A25"] = "How to read it"
    md["A25"].font = Font(bold=True, size=12)
    notes = [
        "1. Seasonal index: mean sales in that calendar month divided by "
        "the grand monthly mean, normalised so the 12 indices average 1.0. "
        "Mar (Ramadan/Eid) is the peak; Jan/Dec (winter) the dip.",
        "2. Trend: ordinary least squares of deseasonalised sales "
        "(sales / index) on time t = 0..21. Slope is PKR per month.",
        "3. Forecast = trend(t) × index(month) for t = 22..27 "
        "(Nov 2025–Apr 2026). Change the parameters above and the "
        "History, Forecast and Backtest sheets recompute.",
        "4. Backtest: the model was re-fitted on Jan 2024–Jul 2025 only "
        "and forecast Aug–Oct 2025, which it had never seen. MAPE is the "
        "honest error to plan around.",
        "5. Nov and Dec indices rest on one observation each (the file has "
        "only one Nov and one Dec). Re-run the forecast every month as "
        "new actuals arrive.",
    ]
    for i, text in enumerate(notes):
        md.cell(row=26 + i, column=1, value=text)
        md.merge_cells(start_row=26 + i, start_column=1,
                       end_row=26 + i, end_column=4)
        md.cell(row=26 + i, column=1).alignment = Alignment(wrap_text=True)
    md.column_dimensions["A"].width = 46
    md.column_dimensions["B"].width = 18
    md.column_dimensions["C"].width = 20
    md.column_dimensions["D"].width = 18

    # ---------- History (values + live formulas) ----------
    hs = wb.create_sheet("History")
    headers = ["Month", "Sales (PKR)", "Orders", "Units", "Avg Order (PKR)",
               "Mobiles & Tablets (PKR)", "TVs & Audio (PKR)",
               "Home Appliances (PKR)", "Fans & Cooling (PKR)",
               "Accessories (PKR)", "t", "Calendar Month",
               "Seasonal Index", "Trend (PKR)", "Fitted (PKR)"]
    hs.append(headers)
    style_header(hs, 1, len(headers))
    for i, r in enumerate(raw):
        row = 2 + i
        hs.cell(row=row, column=1, value=r["month"])
        hs.cell(row=row, column=2, value=int(r["sales_pkr"]))
        hs.cell(row=row, column=3, value=int(r["orders"]))
        hs.cell(row=row, column=4, value=int(r["units"]))
        hs.cell(row=row, column=5, value=f"=IFERROR(B{row}/C{row},\"\")")
        hs.cell(row=row, column=6, value=int(r["mobiles_pkr"]))
        hs.cell(row=row, column=7, value=int(r["tvs_audio_pkr"]))
        hs.cell(row=row, column=8, value=int(r["home_appliances_pkr"]))
        hs.cell(row=row, column=9, value=int(r["fans_cooling_pkr"]))
        hs.cell(row=row, column=10, value=int(r["accessories_pkr"]))
        hs.cell(row=row, column=11, value=i)
        hs.cell(row=row, column=12, value=int(r["month_no"]))
        hs.cell(row=row, column=13,
               value=f"=INDEX(Method!$B$12:$B$23,L{row})")
        hs.cell(row=row, column=14,
               value=f"=Method!$B$5+Method!$B$6*K{row}")
        hs.cell(row=row, column=15, value=f"=M{row}*N{row}")
    tr = last_row + 1  # total row 24
    hs.cell(row=tr, column=1, value="TOTAL").font = Font(bold=True)
    for col in (2, 3, 4, 6, 7, 8, 9, 10):
        letter = get_column_letter(col)
        hs.cell(row=tr, column=col,
               value=f"=SUM({letter}2:{letter}{last_row})").font = Font(bold=True)
    hs.cell(row=tr, column=5,
           value=f"=IFERROR(B{tr}/C{tr},\"\")").font = Font(bold=True)
    for r in range(2, tr + 1):
        for col in (2, 5, 6, 7, 8, 9, 10, 14, 15):
            hs.cell(row=r, column=col).number_format = MONEY_FMT
        hs.cell(row=r, column=13).number_format = '0.0000'
    widths = [12, 14, 9, 9, 14, 18, 15, 17, 15, 14, 5, 14, 14, 14, 14]
    for i, w in enumerate(widths, 1):
        hs.column_dimensions[get_column_letter(i)].width = w
    hs.freeze_panes = "A2"
    hs.auto_filter.ref = f"A1:O{last_row}"

    # ---------- Forecast (live formulas) ----------
    fc_ws = wb.create_sheet("Forecast")
    fc_ws.append(["Month", "t", "Calendar Month", "Seasonal Index",
                  "Trend (PKR)", "Forecast (PKR)", "Share of Total",
                  "Cumulative (PKR)"])
    style_header(fc_ws, 1, 8)
    for i, f in enumerate(fc):
        row = 2 + i
        fc_ws.cell(row=row, column=1, value=f["month"])
        fc_ws.cell(row=row, column=2, value=int(f["t"]))
        fc_ws.cell(row=row, column=3, value=int(f["month_no"]))
        fc_ws.cell(row=row, column=4,
                  value=f"=INDEX(Method!$B$12:$B$23,C{row})")
        fc_ws.cell(row=row, column=5,
                  value=f"=Method!$B$5+Method!$B$6*B{row}")
        fc_ws.cell(row=row, column=6, value=f"=ROUND(D{row}*E{row},0)")
        fc_ws.cell(row=row, column=7, value=f"=IFERROR(F{row}/F$8,\"\")")
        fc_ws.cell(row=row, column=8, value=f"=SUM($F$2:F{row})")
    fc_ws.cell(row=8, column=1, value="TOTAL").font = Font(bold=True)
    fc_ws.cell(row=8, column=6, value="=SUM(F2:F7)").font = Font(bold=True)
    fc_ws.cell(row=8, column=7, value="=SUM(G2:G7)").font = Font(bold=True)
    fc_ws.cell(row=8, column=8, value="=F8").font = Font(bold=True)
    for r in range(2, 9):
        for col in (5, 6, 8):
            fc_ws.cell(row=r, column=col).number_format = MONEY_FMT
        fc_ws.cell(row=r, column=4).number_format = '0.0000'
        fc_ws.cell(row=r, column=7).number_format = PCT_FMT
    fc_ws.column_dimensions["A"].width = 12
    fc_ws.column_dimensions["B"].width = 6
    fc_ws.column_dimensions["C"].width = 15
    fc_ws.column_dimensions["D"].width = 15
    fc_ws.column_dimensions["E"].width = 14
    fc_ws.column_dimensions["F"].width = 15
    fc_ws.column_dimensions["G"].width = 14
    fc_ws.column_dimensions["H"].width = 16
    fc_ws.freeze_panes = "A2"

    # ---------- Backtest (live formulas from backtest parameters) ----------
    bt_ws = wb.create_sheet("Backtest")
    bt_ws.append(["Month", "t", "Calendar Month", "Actual (PKR)",
                  "Forecast (PKR)", "Error (PKR)", "Abs % Error"])
    style_header(bt_ws, 1, 7)
    for i, b in enumerate(bt):
        row = 2 + i
        bt_ws.cell(row=row, column=1, value=b["month"])
        bt_ws.cell(row=row, column=2, value=int(b["t"]))
        bt_ws.cell(row=row, column=3, value=int(b["month_no"]))
        bt_ws.cell(row=row, column=4, value=int(b["actual_pkr"]))
        bt_ws.cell(row=row, column=5,
                  value=f"=ROUND((Method!$B$7+Method!$B$8*B{row})"
                        f"*INDEX(Method!$C$12:$C$23,C{row}),0)")
        bt_ws.cell(row=row, column=6, value=f"=E{row}-D{row}")
        bt_ws.cell(row=row, column=7, value=f"=IFERROR(ABS(F{row})/D{row},\"\")")
    bt_ws.cell(row=5, column=1, value="MAPE").font = Font(bold=True)
    bt_ws.cell(row=5, column=7, value="=AVERAGE(G2:G4)").font = Font(bold=True)
    for r in range(2, 6):
        for col in (4, 5, 6):
            bt_ws.cell(row=r, column=col).number_format = MONEY_FMT
        bt_ws.cell(row=r, column=7).number_format = PCT2_FMT
    bt_ws["A7"] = ("Backtest: fitted on Jan 2024–Jul 2025 only, forecast "
                   "Aug–Oct 2025 unseen. MAPE is the average absolute "
                   "percentage error — the honest planning error.")
    bt_ws["A7"].alignment = Alignment(wrap_text=True, vertical="top")
    bt_ws.merge_cells("A7:G7")
    bt_ws.row_dimensions[7].height = 30
    bt_ws.column_dimensions["A"].width = 12
    bt_ws.column_dimensions["B"].width = 6
    bt_ws.column_dimensions["C"].width = 15
    bt_ws.column_dimensions["D"].width = 15
    bt_ws.column_dimensions["E"].width = 15
    bt_ws.column_dimensions["F"].width = 14
    bt_ws.column_dimensions["G"].width = 13

    # ---------- What-If (editable inputs, live recompute) ----------
    wi = wb.create_sheet("What-If")
    wi["A1"] = "What-If — change the inputs, the forecast recomputes"
    wi["A1"].font = TITLE_FONT
    wi["A3"] = "Extra monthly growth (compounds each forecast month)"
    wi["B3"] = 0
    wi["B3"].number_format = PCT_FMT
    wi["A4"] = "Seasonal uplift (applies to all 6 months)"
    wi["B4"] = 0
    wi["B4"].number_format = PCT_FMT
    wi["A5"] = ("Try: +2% growth with 0% uplift, or 0% growth with +5% "
                "uplift for a strong-Ramadan scenario. Base case is 0% / 0%.")
    wi["A5"].font = Font(italic=True, size=10)
    wi.merge_cells("A5:E5")
    wi.append([])  # row 6 header
    wi["A6"] = "Month"
    wi["B6"] = "Base Forecast (PKR)"
    wi["C6"] = "What-If Forecast (PKR)"
    wi["D6"] = "Change (PKR)"
    wi["E6"] = "Change %"
    style_header(wi, 6, 5)
    for i, f in enumerate(fc):
        row = 7 + i
        wi.cell(row=row, column=1, value=f["month"])
        wi.cell(row=row, column=2, value=f"='Forecast'!F{2 + i}")
        wi.cell(row=row, column=3,
               value=f"=B{row}*(1+$B$3)^(ROW()-7)*(1+$B$4)")
        wi.cell(row=row, column=4, value=f"=C{row}-B{row}")
        wi.cell(row=row, column=5, value=f"=IFERROR(D{row}/B{row},\"\")")
    wi.cell(row=13, column=1, value="TOTAL").font = Font(bold=True)
    for col in (2, 3, 4):
        letter = get_column_letter(col)
        wi.cell(row=13, column=col,
               value=f"=SUM({letter}7:{letter}12)").font = Font(bold=True)
    wi.cell(row=13, column=5, value="=IFERROR(D13/B13,\"\")").font = Font(bold=True)
    for r in range(7, 14):
        for col in (2, 3, 4):
            wi.cell(row=r, column=col).number_format = MONEY_FMT
        wi.cell(row=r, column=5).number_format = PCT_FMT
    wi.column_dimensions["A"].width = 46
    wi.column_dimensions["B"].width = 20
    wi.column_dimensions["C"].width = 22
    wi.column_dimensions["D"].width = 15
    wi.column_dimensions["E"].width = 11

    # ---------- Dashboard (live formulas) ----------
    db = wb.create_sheet("Dashboard", 0)
    db["A1"] = "Sales Forecast — Noor Electronics, Lahore (SAMPLE)"
    db["A1"].font = TITLE_FONT
    db["A2"] = ("Fictional electronics shop, Jan 2024–Oct 2025 · Forecast "
                "Nov 2025–Apr 2026 · SAMPLE data — method is real, the shop "
                "is not.")
    db["A2"].font = Font(italic=True, size=10)
    db["A4"] = "KPI"
    db["B4"] = "Value"
    db["C4"] = "How it is calculated"
    style_header(db, 4, 3)
    hist = "'History'"
    fcs = "'Forecast'"
    kpis = [
        ("History months", f"=COUNTA({hist}!$A$2:$A${last_row})",
         "Count of history months"),
        ("History total sales (PKR)", f"=SUM({hist}!$B$2:$B${last_row})",
         "Sum of monthly sales, Jan 2024–Oct 2025"),
        ("Avg monthly sales (PKR)", f"=AVERAGE({hist}!$B$2:$B${last_row})",
         "History total / 22 months"),
        ("Best month", f"=INDEX({hist}!$A$2:$A${last_row},"
         f"MATCH(MAX({hist}!$B$2:$B${last_row}),{hist}!$B$2:$B${last_row},0))",
         "Month with the highest sales"),
        ("Best month sales (PKR)", f"=MAX({hist}!$B$2:$B${last_row})",
         "Highest monthly sales"),
        ("Last 3 months avg (PKR)", f"=AVERAGE({hist}!$B$21:$B$23)",
         "Aug–Oct 2025 average"),
        ("6-month forecast total (PKR)", f"=SUM({fcs}!$F$2:$F$7)",
         "Sum of Nov 2025–Apr 2026 forecasts"),
        ("Forecast avg / month (PKR)", f"=AVERAGE({fcs}!$F$2:$F$7)",
         "Forecast total / 6"),
        ("Forecast vs last 6 months",
         f"=IFERROR(B11/SUM({hist}!$B$18:$B$23)-1,\"\")",
         "Forecast total vs May–Oct 2025 actuals"),
        ("Best forecast month", f"=INDEX({fcs}!$A$2:$A$7,"
         f"MATCH(MAX({fcs}!$F$2:$F$7),{fcs}!$F$2:$F$7,0))",
         "Highest forecast month"),
        ("Best forecast month sales (PKR)", f"=MAX({fcs}!$F$2:$F$7)",
         "Highest monthly forecast"),
        ("Backtest MAPE", "='Backtest'!G5",
         "Average absolute % error, Aug–Oct 2025 hold-out"),
        ("What-If total (current inputs)", "='What-If'!C13",
         "6-month total at the current What-If inputs (0% / 0% = base)"),
    ]
    row = 5
    for label, formula, how in kpis:
        db.cell(row=row, column=1, value=label)
        db.cell(row=row, column=2, value=formula).font = KPI_FONT
        db.cell(row=row, column=3, value=how)
        row += 1
    for r in (6, 7, 9, 10, 11, 12, 15, 17):
        db.cell(row=r, column=2).number_format = MONEY_FMT
    db.cell(row=13, column=2).number_format = PCT_FMT
    db.cell(row=16, column=2).number_format = PCT2_FMT

    seg_start = 20
    db.cell(row=seg_start, column=1,
           value="Forecast at a glance (live from the Forecast sheet)").font = Font(bold=True, size=12)
    db.cell(row=seg_start + 1, column=1, value="Month")
    db.cell(row=seg_start + 1, column=2, value="Forecast (PKR)")
    db.cell(row=seg_start + 1, column=3, value="Share of Total")
    style_header(db, seg_start + 1, 3)
    for i, f in enumerate(fc):
        r = seg_start + 2 + i
        db.cell(row=r, column=1, value=f["month"])
        db.cell(row=r, column=2, value=f"={fcs}!F{2 + i}").number_format = MONEY_FMT
        db.cell(row=r, column=3, value=f"={fcs}!G{2 + i}").number_format = PCT_FMT
    tr = seg_start + 8
    db.cell(row=tr, column=1, value="TOTAL").font = Font(bold=True)
    db.cell(row=tr, column=2,
           value=f"=SUM(B{seg_start + 2}:B{seg_start + 7})").font = Font(bold=True)
    db.cell(row=tr, column=2).number_format = MONEY_FMT
    db.cell(row=tr, column=3,
           value=f"=SUM(C{seg_start + 2}:C{seg_start + 7})").font = Font(bold=True)
    db.cell(row=tr, column=3).number_format = PCT_FMT
    db.column_dimensions["A"].width = 34
    db.column_dimensions["B"].width = 22
    db.column_dimensions["C"].width = 52

    wb.active = wb["Dashboard"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print(f"wrote {OUT} ({n} history months, {len(fc)} forecast months)")


if __name__ == "__main__":
    main()
