
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="FORESIGHT - Demand & Inventory Planning", layout="wide")

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"


@st.cache_data
def load_data():
    sales = pd.read_csv(DATA_DIR / "analysis_with_forecast.csv", parse_dates=["date"])
    risk = pd.read_csv(DATA_DIR / "risk_scores.csv")
    return sales, risk


sales, risk = load_data()

st.title("FORESIGHT — Demand & Inventory Planning")
st.caption("NorthBay Living | Updated from latest pipeline run")


st.sidebar.header("Filters")
categories = ["All"] + sorted(sales["category"].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("Category", categories)

filtered_risk = risk if selected_category == "All" else risk[risk["category"] == selected_category]


col1, col2, col3, col4 = st.columns(4)
col1.metric("Total revenue at risk", f"Rs {filtered_risk['revenue_at_risk'].sum():,.0f}")
col2.metric("Capital locked in overstock", f"Rs {filtered_risk['capital_locked'].sum():,.0f}")
col3.metric("SKUs to reorder now", int((filtered_risk["risk_quadrant"] == "Reorder Now").sum()))
col4.metric("SKUs to markdown/clear", int((filtered_risk["risk_quadrant"] == "Markdown / Clear").sum()))

st.divider()


st.subheader("Prioritised reorder / markdown list")
if len(filtered_risk) == 0:
    st.info("No SKUs match this filter.")
else:
    action_list = filtered_risk[filtered_risk["risk_quadrant"] != "Healthy"].sort_values(
        "rupee_value_at_stake", ascending=False
    )
    if len(action_list) == 0:
        st.success("No SKUs currently need action - all healthy.")
    else:
        st.dataframe(
            action_list[["sku_id", "product_name", "category", "risk_quadrant",
                          "recommended_action", "rupee_value_at_stake"]],
            use_container_width=True, hide_index=True,
        )

st.divider()


st.subheader("Stockout vs overstock risk grid")
if len(filtered_risk) > 0:
    fig = px.scatter(
        filtered_risk, x="overstock_risk", y="stockout_risk", size="rupee_value_at_stake",
        color="risk_quadrant", hover_name="product_name",
        labels={"overstock_risk": "Overstock risk", "stockout_risk": "Stockout risk"},
        color_discrete_map={
            "Reorder Now": "#d9534f", "Markdown / Clear": "#5bc0de",
            "Watch / Volatile": "#f0ad4e", "Healthy": "#5cb85c",
        },
    )
    fig.add_hline(y=0.5, line_dash="dash", line_color="gray")
    fig.add_vline(x=0.5, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data for this filter.")

st.divider()


st.subheader("Forecast vs actual — single SKU")
sku_options = sorted(sales["sku_id"].unique().tolist())
selected_sku = st.selectbox("Choose a SKU", sku_options)

sku_history = sales[sales["sku_id"] == selected_sku].sort_values("date").tail(120)
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=sku_history["date"], y=sku_history["units_sold"],
                            mode="lines", name="Actual demand"))
if "baseline_pred" in sku_history.columns:
    fig2.add_trace(go.Scatter(x=sku_history["date"], y=sku_history["baseline_pred"],
                                mode="lines", name="Seasonal-naive baseline", line=dict(dash="dash")))
fig2.update_layout(xaxis_title="Date", yaxis_title="Units sold", height=400)
st.plotly_chart(fig2, use_container_width=True)

st.caption("FORESIGHT v1.0 - Zidio Development internal analytics engine")
