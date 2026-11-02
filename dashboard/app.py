import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text
from src.db import admin_engine, readonly_engine

st.set_page_config("MandiIQ", layout="wide")
ro, admin = readonly_engine(), admin_engine()


@st.cache_data(ttl=600)
def q(sql: str, params: tuple = ()) -> pd.DataFrame:
    with ro.connect() as c:
        return pd.read_sql(text(sql), c, params=dict(params))


st.title("MandiIQ: Agricultural Price Intelligence")
st.caption("Analysis of reported mandi prices (INR/quintal). Not official statistics.")
page = st.sidebar.radio("Page", ["Dashboard", "Ask a question", "Data quality"])

if page == "Dashboard":
    comms = q("SELECT DISTINCT commodity FROM v_prices ORDER BY 1")["commodity"].tolist()
    states = q("SELECT DISTINCT state FROM v_prices ORDER BY 1")["state"].tolist()
    if not comms:
        st.warning("No data loaded yet. Run the ETL first."); st.stop()
    com = st.sidebar.selectbox("Commodity", comms)
    sel = st.sidebar.multiselect("States", states, default=states[:5])
    lo, hi = q("SELECT MIN(price_date) a, MAX(price_date) b FROM v_prices").iloc[0]
    d1, d2 = st.sidebar.date_input("Date range", (lo, hi))
    p = (("c", com), ("a", d1), ("b", d2))
    f = q("SELECT price_date, state, AVG(modal_price) AS modal FROM v_prices WHERE commodity=:c "
          "AND price_date BETWEEN :a AND :b GROUP BY 1,2", p)
    f = f[f["state"].isin(sel)] if sel else f
    k1, k2, k3 = st.columns(3)
    k1.metric("Avg modal price", f"{f['modal'].mean():,.0f}" if len(f) else "n/a")
    k2.metric("Observations (state-days)", f"{len(f):,}")
    an = q("SELECT price_date, state, modal_price FROM v_anomalies WHERE commodity=:c AND price_date BETWEEN :a AND :b", p)
    k3.metric("Anomalies flagged", f"{len(an):,}")
    fig = px.line(f, x="price_date", y="modal", color="state", title=f"{com}: modal price trend")
    if len(an):
        an = an[an["state"].isin(sel)] if sel else an
        fig.add_scatter(x=an["price_date"], y=an["modal_price"], mode="markers", name="anomaly",
                        marker=dict(color="red", size=8, symbol="x"))
    st.plotly_chart(fig, use_container_width=True)
    c1, c2 = st.columns(2)
    seas = q("SELECT commodity, month, seasonal_index FROM v_seasonality")
    if len(seas):
        c1.plotly_chart(px.imshow(seas.pivot(index="commodity", columns="month", values="seasonal_index"),
                                  aspect="auto", color_continuous_midpoint=1, title="Seasonal index (month x commodity)"),
                        use_container_width=True)
    st_cmp = f.groupby("state", as_index=False)["modal"].mean().sort_values("modal")
    c2.plotly_chart(px.bar(st_cmp, x="modal", y="state", orientation="h", title="State comparison (avg modal)"),
                    use_container_width=True)
    vol = q("SELECT state, cv FROM v_volatility WHERE commodity=:c ORDER BY cv DESC", (("c", com),))
    st.plotly_chart(px.bar(vol, x="state", y="cv", title="Volatility ranking (CV of monthly price)"),
                    use_container_width=True)

elif page == "Ask a question":
    from src.assistant.llm import ask
    question = st.text_input("Ask in plain English", "Which state had the most volatile onion prices?")
    if st.button("Run") and question:
        res = ask(question, ro, admin)
        if res["message"]:
            st.error(res["message"])
        if res["sql"]:
            st.code(res["sql"], language="sql")
        if res["df"] is not None:
            st.dataframe(res["df"])
            num = res["df"].select_dtypes("number").columns
            if len(res["df"].columns) >= 2 and len(num):
                st.bar_chart(res["df"].set_index(res["df"].columns[0])[num[0]])

else:
    rp = Path("data/clean/data_quality_report.json")
    if rp.exists():
        r = json.loads(rp.read_text())
        a, b, c = st.columns(3)
        a.metric("Rows read", f"{r['read']:,}"); b.metric("Rejected", f"{r['rejected']:,}")
        c.metric("Duplicates skipped", f"{r['duplicates_skipped']:,}")
        st.write("Rejections by reason", r["reject_reasons"])
        st.dataframe(pd.DataFrame(r["coverage_state_year"]))
    else:
        st.info("No report yet. Run the ETL.")
