CREATE OR REPLACE VIEW v_prices AS
SELECT f.date_id, d.price_date, d.year, d.month, m.market_id, m.state, m.district, m.market,
       c.commodity_id, c.commodity, c.variety, f.min_price, f.max_price, f.modal_price, f.arrivals
FROM fact_prices f JOIN dim_date d USING (date_id)
JOIN dim_market m USING (market_id) JOIN dim_commodity c USING (commodity_id);

CREATE OR REPLACE VIEW v_monthly_prices AS
SELECT state, commodity, year, month, MAKE_DATE(year, month, 1) AS month_start,
       AVG(modal_price) AS avg_modal_price, COUNT(*) AS n_obs
FROM v_prices GROUP BY state, commodity, year, month;

CREATE OR REPLACE VIEW v_seasonality AS
WITH yr AS (SELECT commodity, year, AVG(modal_price) AS yr_avg FROM v_prices GROUP BY commodity, year)
SELECT p.commodity, p.month, AVG(p.modal_price / yr.yr_avg) AS seasonal_index, COUNT(*) AS n_obs
FROM v_prices p JOIN yr USING (commodity, year) GROUP BY p.commodity, p.month;

CREATE OR REPLACE VIEW v_volatility AS
SELECT commodity, state, STDDEV_SAMP(avg_modal_price) / NULLIF(AVG(avg_modal_price), 0) AS cv,
       COUNT(*) AS n_months
FROM v_monthly_prices GROUP BY commodity, state HAVING COUNT(*) >= 12;

CREATE OR REPLACE VIEW v_anomalies AS
SELECT d.price_date, m.state, m.market, c.commodity, c.variety, a.modal_price, a.rolling_median, a.robust_z
FROM anomalies a JOIN dim_date d USING (date_id) JOIN dim_market m USING (market_id)
JOIN dim_commodity c USING (commodity_id);
