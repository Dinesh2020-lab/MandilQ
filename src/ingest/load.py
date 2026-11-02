"""Chunked, idempotent ETL: raw CSV -> validate -> staging -> star schema (FR-1..FR-6, FR-8)."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from src.db import admin_engine
from src.validate.validators import standardize, validate

RAW, CLEAN = Path("data/raw"), Path("data/clean")
CHUNK = 100_000
COLS = ["price_date", "state", "district", "market", "commodity", "variety", "grade",
        "min_price", "max_price", "modal_price", "arrivals"]

INSERTS = [
    """INSERT INTO dim_date(date_id, price_date, year, month)
       SELECT DISTINCT to_char(price_date,'YYYYMMDD')::int, price_date::date,
              extract(year FROM price_date)::int, extract(month FROM price_date)::int
       FROM stg_prices ON CONFLICT DO NOTHING""",
    "INSERT INTO dim_market(state, district, market) SELECT DISTINCT state, district, market FROM stg_prices ON CONFLICT DO NOTHING",
    "INSERT INTO dim_commodity(commodity, variety) SELECT DISTINCT commodity, variety FROM stg_prices ON CONFLICT DO NOTHING",
    """INSERT INTO fact_prices(date_id, market_id, commodity_id, grade, min_price, max_price, modal_price, arrivals)
       SELECT DISTINCT ON (d.date_id, m.market_id, c.commodity_id)
              d.date_id, m.market_id, c.commodity_id, s.grade, s.min_price, s.max_price, s.modal_price, s.arrivals
       FROM stg_prices s
       JOIN dim_date d ON d.price_date = s.price_date::date
       JOIN dim_market m ON (m.state, m.district, m.market) = (s.state, s.district, s.market)
       JOIN dim_commodity c ON (c.commodity, c.variety) = (s.commodity, s.variety)
       ON CONFLICT DO NOTHING""",
]


def run() -> dict:
    CLEAN.mkdir(parents=True, exist_ok=True)
    rej_path = CLEAN / "rejected_records.csv"
    rej_path.unlink(missing_ok=True)
    eng = admin_engine()
    stats = {"read": 0, "valid": 0, "rejected": 0, "inserted": 0, "reject_reasons": {}}
    for f in sorted(RAW.glob("*.csv")):
        for chunk in pd.read_csv(f, chunksize=CHUNK, dtype=str):
            stats["read"] += len(chunk)
            ok, bad = validate(standardize(chunk))
            if len(bad):
                bad.assign(source_file=f.name).to_csv(rej_path, mode="a", index=False, header=not rej_path.exists())
                for r, n in bad["reject_reason"].value_counts().items():
                    stats["reject_reasons"][r] = stats["reject_reasons"].get(r, 0) + int(n)
            stats["valid"] += len(ok)
            stats["rejected"] += len(bad)
            if ok.empty:
                continue
            with eng.begin() as conn:
                ok[COLS].to_sql("stg_prices", conn, if_exists="replace", index=False)
                for q in INSERTS[:-1]:
                    conn.execute(text(q))
                stats["inserted"] += conn.execute(text(INSERTS[-1])).rowcount
                conn.execute(text("DROP TABLE stg_prices"))
    stats["duplicates_skipped"] = stats["valid"] - stats["inserted"]
    with eng.connect() as conn:
        stats["coverage_state_year"] = [dict(r._mapping) for r in conn.execute(text(
            "SELECT state, year, COUNT(*) n FROM v_prices GROUP BY state, year ORDER BY state, year"))] \
            if _view_exists(conn) else []
        stats["null_rate_arrivals"] = float(conn.execute(text(
            "SELECT COALESCE(AVG((arrivals IS NULL)::int),0) FROM fact_prices")).scalar())
    (CLEAN / "data_quality_report.json").write_text(json.dumps(stats, indent=2, default=str))
    print(json.dumps({k: v for k, v in stats.items() if k != "coverage_state_year"}, indent=2))
    return stats


def _view_exists(conn) -> bool:
    return bool(conn.execute(text("SELECT to_regclass('v_prices')")).scalar())


if __name__ == "__main__":
    run()
