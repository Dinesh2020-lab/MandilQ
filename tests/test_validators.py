import pandas as pd
from src.validate.validators import standardize, validate
from src.analytics.anomaly import detect


def _df(**o):
    r = dict(price_date="05/03/2024", state=" maharashtra ", district="pune", market="pune", commodity="onion",
             variety=None, grade=None, min_price="100", max_price="200", modal_price="150", arrivals=None)
    r.update(o)
    return pd.DataFrame([r])


def test_valid_and_standardized():
    ok, bad = validate(standardize(_df()))
    assert len(ok) == 1 and bad.empty
    assert ok.iloc[0]["state"] == "Maharashtra" and ok.iloc[0]["variety"] == "Unknown"


def test_rejections():
    cases = {"non_positive_price": dict(modal_price="-1"), "price_order_violation": dict(min_price="300"),
             "future_date": dict(price_date="01/01/2099"), "missing_mandatory_field": dict(market=None),
             "missing_or_non_numeric_price": dict(modal_price="abc")}
    for reason, kw in cases.items():
        ok, bad = validate(standardize(_df(**kw)))
        assert ok.empty and bad.iloc[0]["reject_reason"] == reason, reason


def test_anomaly_detects_spike():
    prices = [100.0 + (i % 5) for i in range(60)]
    prices[40] = 400.0
    df = pd.DataFrame({"date_id": range(60), "market_id": 1, "commodity_id": 1, "modal_price": prices})
    flags = detect(df)
    assert 40 in flags["date_id"].tolist()
