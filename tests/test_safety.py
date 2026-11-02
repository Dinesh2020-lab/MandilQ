import pytest
from src.assistant.safety import validate_sql

GOOD = [
    "SELECT state, AVG(modal_price) FROM v_prices GROUP BY state",
    "WITH t AS (SELECT * FROM v_monthly_prices) SELECT commodity, LAG(avg_modal_price) OVER (PARTITION BY state ORDER BY month_start) FROM t",
    "SELECT commodity, ROUND(cv::numeric, 2), NTILE(4) OVER (ORDER BY cv) FROM v_volatility;",
    "SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY modal_price) FROM v_prices",
    "SELECT CASE WHEN modal_price > 100 THEN 'hi' ELSE 'lo' END, COUNT(*) FROM v_prices GROUP BY 1",
]
BAD = [
    "DROP TABLE fact_prices", "SELECT 1; DROP TABLE fact_prices", "DELETE FROM v_prices",
    "INSERT INTO anomalies VALUES (1,1,1,1,1,1)", "SELECT * FROM fact_prices", "SELECT * FROM pg_user",
    "SELECT pg_sleep(100)", "SELECT * FROM public.v_prices", "COPY v_prices TO '/tmp/x'",
    "SELECT * INTO newt FROM v_prices", "SELECT * FROM v_prices FOR UPDATE", "SELECT pg_read_file('/etc/passwd')",
    "UPDATE v_prices SET modal_price=0", "SELECT * FROM v_prices WHERE", "", "SELECT * FROM generate_series(1,10)",
]


@pytest.mark.parametrize("sql", GOOD)
def test_good(sql):
    v = validate_sql(sql)
    assert v.ok, v.message
    assert "LIMIT" in v.sql.upper()


@pytest.mark.parametrize("sql", BAD)
def test_bad(sql):
    assert not validate_sql(sql).ok


def test_limit_capped():
    assert "LIMIT 1000" in validate_sql("SELECT * FROM v_prices LIMIT 999999").sql.upper()
    assert "LIMIT 5" in validate_sql("SELECT * FROM v_prices LIMIT 5").sql.upper()
