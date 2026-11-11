-- P15 — Sales Forecast Pack (Noor Electronics, SAMPLE data)
-- The forecast model in SQL: the same classical decomposition as
-- src/forecast.py, recomputed from fact_monthly_totals.
--
--  1. seasonal index per calendar month = mean sales in that month /
--     grand mean, normalised so the 12 indices average 1.0
--     (months Nov/Dec have a single observation in this 22-month file)
--  2. deseasonalised sales = sales / index
--  3. OLS trend of deseasonalised sales on t, closed form:
--     slope = (n*SUM(t*y) - SUM(t)*SUM(y)) / (n*SUM(t*t) - SUM(t)^2)
--     intercept = (SUM(y) - slope*SUM(t)) / n
--  4. forecast for t = 22..27 = trend(t) * index(calendar month)
--
-- Run against data/processed/sales.db (built by src/build_sqlite.py):
--   sqlite3 data/processed/sales.db < sql/forecast_model.sql
-- The Python model (src/forecast.py) and this SQL must agree within
-- 1% per month — src/checks.py verifies that.

WITH grand AS (
    SELECT AVG(sales_pkr * 1.0) AS gmean,
           COUNT(*) AS n FROM fact_monthly_totals
),
raw_idx AS (
    SELECT m.month_no AS month_no,
           AVG(t.sales_pkr * 1.0) / (SELECT gmean FROM grand) AS raw_idx
    FROM fact_monthly_totals t
    JOIN dim_month m ON m.month_key = t.month_key
    GROUP BY m.month_no
),
norm AS (
    SELECT AVG(raw_idx) AS mean_raw FROM raw_idx
),
season AS (
    SELECT r.month_no AS month_no,
           r.raw_idx / (SELECT mean_raw FROM norm) AS idx
    FROM raw_idx r
),
deseas AS (
    SELECT m.t AS t, m.month_no AS month_no,
           t.sales_pkr * 1.0 / s.idx AS y
    FROM fact_monthly_totals t
    JOIN dim_month m ON m.month_key = t.month_key
    JOIN season s ON s.month_no = m.month_no
),
ols AS (
    SELECT COUNT(*) * 1.0 AS n,
           SUM(t) AS st, SUM(y) AS sy,
           SUM(t * t) AS stt, SUM(t * y) AS sty
    FROM deseas
),
trend AS (
    SELECT (n * sty - st * sy) / (n * stt - st * st) AS slope,
           (sy - ((n * sty - st * sy) / (n * stt - st * st)) * st) / n
               AS intercept
    FROM ols
),
future (t, month_no, month_label) AS (
    VALUES (22, 11, 'Nov 2025'), (23, 12, 'Dec 2025'),
           (24,  1, 'Jan 2026'), (25,  2, 'Feb 2026'),
           (26,  3, 'Mar 2026'), (27,  4, 'Apr 2026')
)
SELECT f.month_label AS month,
       f.t AS t,
       ROUND(s.idx, 4) AS seasonal_index,
       CAST(ROUND((tr.intercept + tr.slope * f.t)) AS INTEGER) AS trend_pkr,
       CAST(ROUND((tr.intercept + tr.slope * f.t) * s.idx) AS INTEGER)
           AS forecast_pkr
FROM future f
JOIN season s ON s.month_no = f.month_no
CROSS JOIN trend tr
ORDER BY f.t;
