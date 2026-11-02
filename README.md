# MandiIQ: Agricultural Price Intelligence Platform

ETL, PostgreSQL star schema, SQL analytics, robust-z anomaly detection, a Streamlit dashboard and a guarded text-to-SQL assistant for Indian mandi prices. Based on the SRS v1.0.

> Findings are analysis of **reported** prices, not official statistics. Cite your data source (Agmarknet, India Data Portal, CEDA) and respect its license.

## Quick start
```bash
cp .env.example .env            # set passwords and GROQ_API_KEY
docker compose up -d db
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
# put real CSVs in data/raw/  (or: python scripts/generate_sample_data.py for SYNTHETIC demo data)
python -m src.ingest.load       # ETL -> rejected_records.csv + data_quality_report.json
python -m src.analytics.anomaly # fills anomalies table
streamlit run dashboard/app.py  # or: docker compose up app
pytest                          # validators, anomaly scoring, SQL safety layer
```
Expected CSV columns (case/spacing flexible): date, state, district, market, commodity, variety, grade, min/max/modal price, arrivals (optional).

## Layout
`sql/schema` DDL and read-only role, `sql/views` analytics views, `sql/analysis` 6 saved analyses (add a one-line insight after running each on real data), `src/{ingest,validate,analytics,assistant}`, `dashboard/app.py`, `tests/`.

## Design notes
- **Idempotent ETL**: unique key (date, market, commodity, variety) plus `ON CONFLICT DO NOTHING`; chunked reads of 100k rows.
- **Anomalies**: each point is scored against the preceding 30 observations (median/MAD), so a spike can't mask itself. Threshold 3.5 (`src/analytics/anomaly.py`).
- **Assistant safety (defense in depth)**: LLM sees schema only; sqlglot validator (single SELECT, allowlisted views and functions, forced LIMIT); read-only role with SELECT on views only, 10 s timeout, read-only transactions; every attempt logged to `assistant_log`.
- **Monsoon test** (`src/analytics/stats.py`): Mann-Whitney U, Apr-May vs Oct-Nov, with rank-biserial effect size. The month windows are my assumption; adjust per crop.

## Results (fill with measured numbers only)
Rows loaded: [N] | Rejected: [X] | Anomalies: [N] (manual precision check: [..]) | Assistant accuracy: [Y]% on [Z] questions | Dashboard screenshots: [..]

## Not yet done
Assistant evaluation set (FR-25), optional forecasting (FR-16), manual anomaly review, NFR-1 timing measurements, SQL insights, screenshots.
