"""Reusable campaign KPI, incrementality, and budget-allocation logic."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def _divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.div(denominator.replace(0, np.nan)).fillna(0.0)


def campaign_performance(exposures: pd.DataFrame, campaigns: pd.DataFrame) -> pd.DataFrame:
    treated = exposures.loc[exposures["assignment"] == "treatment"]
    result = treated.groupby("campaign_id", as_index=False).agg(
        reached_customers=("customer_id", "nunique"),
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        conversions=("converted", "sum"),
        revenue=("order_value", "sum"),
        spend=("media_cost", "sum"),
    )
    result["ctr"] = _divide(result["clicks"], result["impressions"])
    result["conversion_rate"] = _divide(result["conversions"], result["reached_customers"])
    result["cpa"] = _divide(result["spend"], result["conversions"])
    result["roas"] = _divide(result["revenue"], result["spend"])
    return result.merge(campaigns[["campaign_id", "campaign_name", "channel", "planned_budget"]], on="campaign_id")


def incrementality(exposures: pd.DataFrame, campaigns: pd.DataFrame) -> pd.DataFrame:
    grouped = exposures.groupby(["campaign_id", "assignment"], as_index=False).agg(
        customers=("customer_id", "nunique"), conversions=("converted", "sum"),
        revenue=("order_value", "sum"), spend=("media_cost", "sum")
    )
    wide = grouped.pivot(index="campaign_id", columns="assignment")
    rows = []
    for campaign_id in wide.index:
        nt = float(wide.loc[campaign_id, ("customers", "treatment")])
        nc = float(wide.loc[campaign_id, ("customers", "control")])
        xt = float(wide.loc[campaign_id, ("conversions", "treatment")])
        xc = float(wide.loc[campaign_id, ("conversions", "control")])
        pt, pc = xt / nt, xc / nc
        lift = pt - pc
        standard_error = math.sqrt(pt * (1 - pt) / nt + pc * (1 - pc) / nc)
        spend = float(wide.loc[campaign_id, ("spend", "treatment")])
        avg_value = float(wide.loc[campaign_id, ("revenue", "treatment")]) / max(xt, 1.0)
        incremental_conversions = lift * nt
        incremental_revenue = incremental_conversions * avg_value
        rows.append(
            {
                "campaign_id": campaign_id,
                "treatment_customers": int(nt),
                "control_customers": int(nc),
                "treatment_cvr": pt,
                "control_cvr": pc,
                "absolute_lift": lift,
                "relative_lift": lift / pc if pc else np.nan,
                "ci95_low": lift - 1.96 * standard_error,
                "ci95_high": lift + 1.96 * standard_error,
                "incremental_conversions": incremental_conversions,
                "incremental_revenue": incremental_revenue,
                "spend": spend,
                "incremental_roas": incremental_revenue / spend if spend else 0.0,
            }
        )
    result = pd.DataFrame(rows)
    return result.merge(campaigns[["campaign_id", "campaign_name", "channel"]], on="campaign_id")


def recommend_budget(incremental: pd.DataFrame, total_budget: float | None = None) -> pd.DataFrame:
    """Allocate a fixed scenario budget using conservative positive iROAS signals.

    The allocation is intentionally transparent: every campaign keeps 25% of its
    current spend, no campaign receives more than 2x spend, and the remainder is
    weighted by the lower-confidence lift signal and incremental ROAS.
    """
    result = incremental[["campaign_id", "campaign_name", "channel", "spend", "incremental_roas", "ci95_low"]].copy()
    if total_budget is None:
        total_budget = float(result["spend"].sum())
    minimum = result["spend"] * 0.25
    capacity = result["spend"] * 2.0 - minimum
    score = result["incremental_roas"].clip(lower=0) * (result["ci95_low"] > 0).astype(float)
    if score.sum() == 0:
        score = result["incremental_roas"].clip(lower=0) + 0.01
    allocation = minimum.copy()
    remaining = max(0.0, total_budget - float(allocation.sum()))
    active = capacity > 1e-9
    while remaining > 1e-6 and active.any():
        weights = score.where(active, 0.0)
        if weights.sum() <= 0:
            weights = active.astype(float)
        proposed = remaining * weights / weights.sum()
        add = np.minimum(proposed, capacity)
        allocation += add
        capacity -= add
        spent = float(add.sum())
        remaining -= spent
        active = capacity > 1e-9
        if spent <= 1e-9:
            break
    result["recommended_budget"] = allocation
    result["budget_change"] = result["recommended_budget"] - result["spend"]
    result["expected_incremental_revenue"] = result["recommended_budget"] * result["incremental_roas"].clip(lower=0)
    return result.sort_values("recommended_budget", ascending=False).reset_index(drop=True)

