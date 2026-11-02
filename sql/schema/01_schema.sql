CREATE TABLE IF NOT EXISTS dim_date (
  date_id INT PRIMARY KEY, price_date DATE NOT NULL UNIQUE,
  year INT NOT NULL, month INT NOT NULL);
CREATE TABLE IF NOT EXISTS dim_market (
  market_id SERIAL PRIMARY KEY, state TEXT NOT NULL, district TEXT NOT NULL, market TEXT NOT NULL,
  UNIQUE (state, district, market));
CREATE TABLE IF NOT EXISTS dim_commodity (
  commodity_id SERIAL PRIMARY KEY, commodity TEXT NOT NULL, variety TEXT NOT NULL DEFAULT 'Unknown',
  commodity_group TEXT, UNIQUE (commodity, variety));
CREATE TABLE IF NOT EXISTS fact_prices (
  date_id INT NOT NULL REFERENCES dim_date, market_id INT NOT NULL REFERENCES dim_market,
  commodity_id INT NOT NULL REFERENCES dim_commodity, grade TEXT,
  min_price NUMERIC NOT NULL, max_price NUMERIC NOT NULL, modal_price NUMERIC NOT NULL,
  arrivals NUMERIC,
  PRIMARY KEY (date_id, market_id, commodity_id),
  CHECK (min_price > 0 AND min_price <= modal_price AND modal_price <= max_price));
CREATE INDEX IF NOT EXISTS ix_fact_market ON fact_prices (market_id);
CREATE INDEX IF NOT EXISTS ix_fact_commodity_date ON fact_prices (commodity_id, date_id);
CREATE INDEX IF NOT EXISTS ix_market_state ON dim_market (state);
CREATE TABLE IF NOT EXISTS anomalies (
  date_id INT, market_id INT, commodity_id INT, modal_price NUMERIC,
  rolling_median NUMERIC, robust_z NUMERIC, PRIMARY KEY (date_id, market_id, commodity_id));
CREATE TABLE IF NOT EXISTS assistant_log (
  id SERIAL PRIMARY KEY, asked_at TIMESTAMPTZ DEFAULT now(), question TEXT, generated_sql TEXT,
  validation_ok BOOLEAN, validation_msg TEXT, exec_ms INT, error TEXT);
