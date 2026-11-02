#!/bin/bash
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<SQL
CREATE ROLE ${RO_USER} LOGIN PASSWORD '${RO_PASSWORD}' NOSUPERUSER NOCREATEDB NOCREATEROLE;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM ${RO_USER};
GRANT USAGE ON SCHEMA public TO ${RO_USER};
GRANT SELECT ON v_prices, v_monthly_prices, v_seasonality, v_volatility, v_anomalies TO ${RO_USER};
ALTER ROLE ${RO_USER} SET statement_timeout = '10s';
SQL
