"""Interactive Streamlit dashboard for campaign decision support."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"

st.set_page_config(page_title="Campaign Measurement", page_icon="📣", layout="wide")
st.title("Omnichannel campaign measurement")
st.caption("Synthetic randomized holdouts · portfolio case study · values shown in EUR")

performance = pd.read_csv(DATA / "campaign_performance.csv")
incremental = pd.read_csv(DATA / "campaign_incrementality.csv")
allocation = pd.read_csv(DATA / "budget_recommendation.csv")

channels = st.multiselect("Channel", sorted(performance["channel"].unique()), default=sorted(performance["channel"].unique()))
p = performance[performance["channel"].isin(channels)]
i = incremental[incremental["channel"].isin(channels)]
a = allocation[allocation["channel"].isin(channels)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Media spend", f"€{p['spend'].sum():,.0f}")
c2.metric("Observed ROAS", f"{p['revenue'].sum() / max(p['spend'].sum(), 1):.2f}×")
c3.metric("Incremental revenue", f"€{i['incremental_revenue'].sum():,.0f}")
c4.metric("Incremental ROAS", f"{i['incremental_revenue'].sum() / max(i['spend'].sum(), 1):.2f}×")

left, right = st.columns(2)
with left:
    st.subheader("Observed funnel by channel")
    funnel = p.groupby("channel", as_index=False)[["impressions", "clicks", "conversions"]].sum().melt("channel", var_name="stage", value_name="volume")
    st.plotly_chart(px.bar(funnel, x="channel", y="volume", color="stage", barmode="group"), use_container_width=True)
with right:
    st.subheader("Measured conversion lift")
    fig = px.scatter(i, x="absolute_lift", y="incremental_roas", color="channel", hover_name="campaign_name", size="treatment_customers")
    fig.add_vline(x=0, line_dash="dash", line_color="#829ab1")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Fixed-budget reallocation scenario")
budget_long = a.melt(id_vars=["campaign_name", "channel"], value_vars=["spend", "recommended_budget"], var_name="budget_type", value_name="budget")
st.plotly_chart(px.bar(budget_long, x="campaign_name", y="budget", color="budget_type", barmode="group", hover_data=["channel"]), use_container_width=True)
st.dataframe(a[["campaign_name", "channel", "spend", "recommended_budget", "budget_change", "incremental_roas"]], use_container_width=True, hide_index=True)
st.info("Incrementality uses randomized synthetic holdouts. The allocation is a transparent planning scenario with floors and caps—not a guaranteed forecast.")

