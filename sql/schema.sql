-- P15 — Sales Forecast Pack (Noor Electronics, SAMPLE data)
-- Star-lite schema: one month dimension, one monthly-sales fact
-- (one row per month per category), one category dimension, and the
-- forecast fact (one row per forecast month). The forecast logic
-- lives in sql/forecast_model.sql and recomputes the trend +
-- seasonal-index forecast from fact_monthly_sales, so the SQL can
-- be checked against the Python model.
--
-- Run:  sqlite3 data/processed/sales.db < sql/schema.sql
-- (src/build_sqlite.py does this and loads the CSVs.)

CREATE TABLE IF NOT EXISTS dim_month (
    month_key   TEXT PRIMARY KEY,  -- e.g. '2024-01'
    month_label TEXT NOT NULL,     -- e.g. 'Jan 2024'
    year        INTEGER NOT NULL,
    month_no    INTEGER NOT NULL CHECK (month_no BETWEEN 1 AND 12),
    t           INTEGER NOT NULL   -- time index: Jan 2024 = 0
);

CREATE TABLE IF NOT EXISTS dim_category (
    category_code TEXT PRIMARY KEY,
    category_name TEXT NOT NULL,
    avg_ticket_pkr INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_monthly_sales (
    month_key     TEXT NOT NULL REFERENCES dim_month (month_key),
    category_code TEXT NOT NULL REFERENCES dim_category (category_code),
    sales_pkr     INTEGER NOT NULL CHECK (sales_pkr >= 0),
    units         INTEGER NOT NULL CHECK (units >= 0),
    PRIMARY KEY (month_key, category_code)
);

CREATE TABLE IF NOT EXISTS fact_monthly_totals (
    month_key  TEXT PRIMARY KEY REFERENCES dim_month (month_key),
    sales_pkr  INTEGER NOT NULL CHECK (sales_pkr > 0),
    orders     INTEGER NOT NULL CHECK (orders > 0),
    units      INTEGER NOT NULL CHECK (units > 0)
);

CREATE TABLE IF NOT EXISTS fact_forecast (
    month_key      TEXT PRIMARY KEY,
    month_label    TEXT NOT NULL,
    year           INTEGER NOT NULL,
    month_no       INTEGER NOT NULL CHECK (month_no BETWEEN 1 AND 12),
    t              INTEGER NOT NULL,
    seasonal_index REAL NOT NULL CHECK (seasonal_index > 0),
    trend_pkr      INTEGER NOT NULL,
    forecast_pkr   INTEGER NOT NULL CHECK (forecast_pkr > 0)
);

CREATE INDEX IF NOT EXISTS idx_sales_month ON fact_monthly_sales (month_key);
CREATE INDEX IF NOT EXISTS idx_sales_category ON fact_monthly_sales (category_code);
