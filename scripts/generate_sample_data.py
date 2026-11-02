"""Generate SYNTHETIC mandi data (with injected bad rows and spikes) for demos and pipeline testing.
Replace with real Agmarknet / India Data Portal / CEDA CSVs in data/raw/ for real analysis."""
import numpy as np, pandas as pd

rng = np.random.default_rng(42)
states = {"Maharashtra": ["Pune", "Nashik"], "Tripura": ["Agartala"], "Manipur": ["Imphal"],
          "Assam": ["Guwahati"], "Uttar Pradesh": ["Lucknow"]}
base = {"Onion": 1800, "Potato": 1500, "Tomato": 2200}
dates = pd.date_range("2022-01-01", "2025-12-31", freq="3D")
rows = []
for s, mk in states.items():
    for m in mk:
        for c, b in base.items():
            seas = 1 + 0.25 * np.sin(2 * np.pi * (dates.dayofyear - 60) / 365)
            modal = b * seas * (1 + rng.normal(0, 0.05, len(dates)))
            spikes = rng.random(len(dates)) < 0.01
            modal = np.where(spikes, modal * rng.choice([2.5, 0.4], len(dates)), modal)
            rows.append(pd.DataFrame({"price_date": dates.strftime("%d/%m/%Y"), "state": s, "district": m,
                "market": m, "commodity": c, "variety": "Local", "grade": "FAQ",
                "min_price": (modal * 0.9).round(), "max_price": (modal * 1.1).round(),
                "modal_price": modal.round(), "arrivals": rng.integers(5, 200, len(dates))}))
df = pd.concat(rows, ignore_index=True)
bad = rng.choice(len(df), 300, replace=False)
df.loc[bad[:100], "modal_price"] = -5
df.loc[bad[100:200], "min_price"] = df.loc[bad[100:200], "max_price"] + 10
df.loc[bad[200:], "price_date"] = "01/01/2099"
df.to_csv("data/raw/sample_synthetic.csv", index=False)
print(len(df), "rows written")
