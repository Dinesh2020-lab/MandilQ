"""Text-to-SQL assistant: schema-only prompt, safety validation, one retry, logging (FR-19..FR-24)."""
from __future__ import annotations
import os, re, time
import pandas as pd
import requests
from sqlalchemy import text
from src.assistant.safety import validate_sql

SCHEMA = """PostgreSQL views (prices are INR per quintal, from reported Agmarknet-style data):
v_prices(price_date date, year int, month int, state, district, market, commodity, variety, min_price, max_price, modal_price, arrivals)
v_monthly_prices(state, commodity, year, month, month_start date, avg_modal_price, n_obs)
v_seasonality(commodity, month, seasonal_index, n_obs)  -- >1 means dearer than the yearly average
v_volatility(commodity, state, cv, n_months)  -- coefficient of variation of monthly price
v_anomalies(price_date, state, market, commodity, variety, modal_price, rolling_median, robust_z)"""
SYSTEM = ("You translate questions into ONE PostgreSQL SELECT over the views below. Use only these views. "
          "Return only the SQL in a ```sql block, nothing else.\n" + SCHEMA)


def _groq(messages: list[dict]) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set.")
    for attempt in range(3):
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers={"Authorization": f"Bearer {key}"}, timeout=30,
                          json={"model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                                "messages": messages, "temperature": 0})
        if r.status_code == 429:
            time.sleep(2 ** attempt); continue
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    raise RuntimeError("The language model is rate-limited. Please try again shortly.")


def _extract(reply: str) -> str:
    m = re.search(r"```(?:sql)?\s*(.*?)```", reply, re.S | re.I)
    return (m.group(1) if m else reply).strip()


def _log(admin, question, sql, ok, msg, ms, err=None) -> None:
    with admin.begin() as c:
        c.execute(text("INSERT INTO assistant_log(question, generated_sql, validation_ok, validation_msg, exec_ms, error) "
                       "VALUES (:q,:s,:o,:m,:t,:e)"), dict(q=question, s=sql, o=ok, m=msg, t=ms, e=err))


def ask(question: str, ro_engine, admin_engine) -> dict:
    """Returns {df, sql, message}. Only the schema text is sent to the LLM, never row data."""
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    last_err, sql = "", ""
    for attempt in range(2):  # original + one retry with the error fed back
        try:
            sql = _extract(_groq(msgs))
        except Exception as e:
            return {"df": None, "sql": "", "message": f"Assistant unavailable: {e}"}
        v = validate_sql(sql)
        t0 = time.time()
        if v.ok:
            try:
                with ro_engine.connect() as c:
                    df = pd.read_sql(text(v.sql), c)
                _log(admin_engine, question, v.sql, True, "ok", int((time.time() - t0) * 1000))
                return {"df": df, "sql": v.sql, "message": ""}
            except Exception as e:
                last_err = str(e).split("\n")[0][:200]
        else:
            last_err = v.message
        _log(admin_engine, question, sql, v.ok, v.message, int((time.time() - t0) * 1000), last_err)
        msgs += [{"role": "assistant", "content": f"```sql\n{sql}\n```"},
                 {"role": "user", "content": f"That failed: {last_err}. Fix it and return only the SQL."}]
    return {"df": None, "sql": sql, "message": f"Sorry, I couldn't produce a safe, working query. ({last_err})"}
