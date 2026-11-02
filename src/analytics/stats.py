"""FR-14: Mann-Whitney U on post- vs pre-monsoon prices, with rank-biserial effect size."""
import pandas as pd
from scipy.stats import mannwhitneyu

PRE, POST = [4, 5], [10, 11]  # Apr-May vs Oct-Nov (assumption; document in README)


def monsoon_test(prices: pd.DataFrame) -> dict:
    """prices needs columns: month, modal_price (one commodity)."""
    a = prices.loc[prices["month"].isin(PRE), "modal_price"].astype(float)
    b = prices.loc[prices["month"].isin(POST), "modal_price"].astype(float)
    u, p = mannwhitneyu(b, a, alternative="two-sided")
    return {"n_pre": len(a), "n_post": len(b), "U": float(u), "p_value": float(p),
            "rank_biserial": float(2 * u / (len(a) * len(b)) - 1),
            "median_pre": float(a.median()), "median_post": float(b.median())}
