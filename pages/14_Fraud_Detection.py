"""
Fraud Detection Page — Isolation Forest anomaly detection.
"""
import streamlit as st
import pandas as pd
import numpy as np
from authentication import check_auth, require_role
from database import get_connection
from utils.prediction import load_model, train_fraud_model
from utils.visualization import (
    kpi_card, create_scatter, create_bar_chart, create_pie_chart,
    create_heatmap, create_line_chart, apply_layout
)

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Fraud Detection")

st.markdown("# 🛡️ Fraud Detection")
st.markdown("AI-powered fraud detection using Isolation Forest anomaly detection")
st.markdown("---")

conn = get_connection()
txn_df = pd.read_sql("SELECT * FROM transactions", conn)
cust_df = pd.read_sql("SELECT customer_id, name, region, branch FROM customers", conn)
conn.close()

if txn_df.empty:
    st.warning("⚠️ No transaction data available.")
    st.stop()

txn_df["date"] = pd.to_datetime(txn_df["date"], errors="coerce")

# Load or train
model_data = load_model("fraud")
if model_data is None:
    with st.spinner("🤖 Training fraud detection model..."):
        model_data, _ = train_fraud_model(txn_df)

model = model_data["model"]
features = model_data["features"]

# Predict
X = txn_df[features].fillna(0)
predictions = model.predict(X)
txn_df["fraud_prediction"] = ["Fraudulent" if p == -1 else "Normal" for p in predictions]
txn_df["anomaly_score"] = model.decision_function(X)

# Merge with customer data
txn_df = txn_df.merge(cust_df, on="customer_id", how="left")

fraud_count = (txn_df["fraud_prediction"] == "Fraudulent").sum()
normal_count = (txn_df["fraud_prediction"] == "Normal").sum()
fraud_amount = txn_df[txn_df["fraud_prediction"] == "Fraudulent"]["amount"].sum()
fraud_pct = round(fraud_count / max(len(txn_df), 1) * 100, 2)

# ── KPIs ──
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("Total Transactions", f"{len(txn_df):,}", "💳", color="blue"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Fraud Detected", f"{fraud_count:,}", "🚨", color="red"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Fraud Amount", f"${fraud_amount:,.0f}", "💸", color="orange"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Fraud Rate", f"{fraud_pct}%", "📊", color="gold"), unsafe_allow_html=True)

st.markdown("---")

# ── Visualizations ──
c1, c2 = st.columns(2)

with c1:
    # Fraud Timeline
    fraud_txns = txn_df[txn_df["fraud_prediction"] == "Fraudulent"].copy()
    if not fraud_txns.empty:
        fraud_timeline = fraud_txns.groupby(fraud_txns["date"].dt.to_period("M").astype(str)).size().reset_index(name="count")
        fraud_timeline.columns = ["month", "count"]
        fig = create_bar_chart(fraud_timeline, "month", "count", "🕐 Fraud Timeline")
        st.plotly_chart(fig, use_container_width=True)

with c2:
    # Fraud by Channel
    if "channel" in txn_df.columns:
        channel_fraud = txn_df[txn_df["fraud_prediction"] == "Fraudulent"].groupby("channel").size().reset_index(name="count")
        fig = create_pie_chart(channel_fraud, "channel", "count", "📱 Fraud by Channel", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    # Fraud by Region
    if "region" in txn_df.columns:
        region_fraud = txn_df[txn_df["fraud_prediction"] == "Fraudulent"].groupby("region").size().reset_index(name="count")
        fig = create_bar_chart(region_fraud, "region", "count", "🌍 Fraud by Region")
        st.plotly_chart(fig, use_container_width=True)

with c4:
    # Fraud amount distribution
    if not fraud_txns.empty:
        import plotly.express as px
        fig = px.histogram(fraud_txns, x="amount", nbins=30, title="💰 Fraud Transaction Amount Distribution")
        fig = apply_layout(fig, "💰 Fraud Transaction Amount Distribution")
        st.plotly_chart(fig, use_container_width=True)

# ── Risk Heatmap ──
st.markdown("### 🔥 Risk Heatmap")
if not fraud_txns.empty and "date" in fraud_txns.columns:
    fraud_txns["day"] = fraud_txns["date"].dt.day_name()
    fraud_txns["type_cat"] = fraud_txns["type"]
    heatmap_data = fraud_txns.groupby(["day", "type_cat"]).size().reset_index(name="count")
    pivot = heatmap_data.pivot_table(index="day", columns="type_cat", values="count", fill_value=0)
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    available_days = [d for d in days_order if d in pivot.index]
    if available_days:
        pivot = pivot.reindex(available_days)
        fig = create_heatmap(pivot.values, pivot.columns.tolist(), pivot.index.tolist(), "🗓️ Fraud Risk Heatmap")
        st.plotly_chart(fig, use_container_width=True)

# ── Flagged Transactions Table ──
st.markdown("---")
st.markdown("### 🚨 Flagged Transactions")
flagged = txn_df[txn_df["fraud_prediction"] == "Fraudulent"][
    ["transaction_id", "customer_id", "name", "amount", "date", "type", "channel", "anomaly_score"]
].sort_values("amount", ascending=False)
st.dataframe(flagged.head(50), use_container_width=True)

csv = flagged.to_csv(index=False)
st.download_button("📥 Download Fraud Report", csv, "fraud_report.csv", "text/csv")
