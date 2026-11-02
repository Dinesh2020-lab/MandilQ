"""Robust z-score anomaly detection with rolling median/MAD per commodity-market (FR-11)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sqlalchemy import text

WINDOW, MIN_OBS, THRESHOLD = 30, 10, 3.5


def robust_z(s: pd.Series, window: int = WINDOW, min_obs: int = MIN_OBS) -> tuple[pd.Series, pd.Series]:
    """Score each point against the PRECEDING window (shifted) so a spike cannot mask itself."""
    past = s.shift(1)
    med = past.rolling(window, min_periods=min_obs).median()
    mad = (past - med).abs().rolling(window, min_periods=min_obs).median()
    mad = mad.replace(0, np.nan)
    return med, 0.6745 * (s - med) / mad


def detect(df: pd.DataFrame, threshold: float = THRESHOLD) -> pd.DataFrame:
    df = df.sort_values("date_id")
    med, z = robust_z(df["modal_price"].astype(float))
    out = df.assign(rolling_median=med, robust_z=z)
    return out[out["robust_z"].abs() > threshold][
        ["date_id", "market_id", "commodity_id", "modal_price", "rolling_median", "robust_z"]]


def run(threshold: float = THRESHOLD) -> int:
    from src.db import admin_engine
    eng = admin_engine()
    prices = pd.read_sql("SELECT date_id, market_id, commodity_id, modal_price FROM fact_prices", eng)
    parts = [detect(g, threshold) for _, g in prices.groupby(["market_id", "commodity_id"])]
    flags = pd.concat(parts) if parts else pd.DataFrame()
    with eng.begin() as conn:
        conn.execute(text("TRUNCATE anomalies"))
        if len(flags):
            flags.to_sql("anomalies", conn, if_exists="append", index=False)
    print(f"{len(flags)} anomalies flagged (threshold={threshold})")
    return len(flags)


if __name__ == "__main__":
    run()
