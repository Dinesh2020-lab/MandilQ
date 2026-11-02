"""Row-level cleaning and validation (FR-2, FR-3). Failing rows are returned with a reason."""
from __future__ import annotations
import pandas as pd

RENAME = {"arrival_date": "price_date", "date": "price_date", "min_price": "min_price", "max_price": "max_price",
          "modal_price": "modal_price", "state_name": "state", "district_name": "district",
          "market_name": "market", "commodity_name": "commodity", "arrivals_in_qtl": "arrivals"}
MANDATORY = ["price_date", "state", "district", "market", "commodity"]
PRICE_COLS = ["min_price", "max_price", "modal_price"]
SPELLING = {"Orissa": "Odisha", "Uttaranchal": "Uttarakhand", "Pondicherry": "Puducherry",
            "Tamilnadu": "Tamil Nadu", "Potato ": "Potato", "Onion Big": "Onion"}


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns=RENAME)
    for c in ["state", "district", "market", "commodity", "variety", "grade"]:
        if c not in df:
            df[c] = pd.NA
        df[c] = df[c].astype("string").str.strip().str.replace(r"\s+", " ", regex=True).str.title()
        df[c] = df[c].replace(SPELLING)
    if "arrivals" not in df:
        df["arrivals"] = pd.NA
    df["price_date"] = pd.to_datetime(df["price_date"], errors="coerce", dayfirst=True, format="mixed")
    for c in PRICE_COLS + ["arrivals"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["variety"] = df["variety"].fillna("Unknown")
    return df


def validate(df: pd.DataFrame, today: pd.Timestamp | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (valid_rows, rejected_rows_with_reason). First failing rule wins."""
    today = today or pd.Timestamp.today().normalize()
    reason = pd.Series("", index=df.index, dtype=object)

    def mark(mask: pd.Series, msg: str) -> None:
        reason[(reason == "") & mask.fillna(True)] = msg

    mark(df[MANDATORY].isna().any(axis=1), "missing_mandatory_field")
    mark(df[PRICE_COLS].isna().any(axis=1), "missing_or_non_numeric_price")
    mark((df[PRICE_COLS] <= 0).any(axis=1), "non_positive_price")
    mark((df["min_price"] > df["modal_price"]) | (df["modal_price"] > df["max_price"]), "price_order_violation")
    mark(df["price_date"] > today, "future_date")
    bad = reason != ""
    rejected = df[bad].assign(reject_reason=reason[bad])
    return df[~bad].copy(), rejected
