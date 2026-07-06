"""
Transaction Analytics Page — KPIs, charts, and transaction insights.
"""
import streamlit as st
import pandas as pd
import numpy as np
from authentication import check_auth, require_role
from database import get_connection
from utils.visualization import (
    kpi_card, create_bar_chart, create_line_chart, create_area_chart,
    create_pie_chart, create_treemap, create_heatmap, apply_layout
)

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Transaction Analytics")

st.markdown("# 💳 Transaction Analytics")
st.markdown("Comprehensive analysis of banking transactions")
st.markdown("---")

conn = get_connection()
txn_df = pd.read_sql("SELECT * FROM transactions", conn)

if txn_df.empty:
    st.warning("⚠️ No transaction data available.")
    conn.close()
    st.stop()

txn_df["date"] = pd.to_datetime(txn_df["date"], errors="coerce")
txn_df["month"] = txn_df["date"].dt.to_period("M").astype(str)
txn_df["day_of_week"] = txn_df["date"].dt.day_name()
txn_df["hour"] = txn_df["date"].dt.hour if txn_df["date"].dt.hour.notna().any() else 12

# ── KPI Cards ──
avg_txn = txn_df["amount"].mean()
monthly_vol = len(txn_df) / max(txn_df["month"].nunique(), 1)
max_txn = txn_df["amount"].max()
min_txn = txn_df["amount"].min()

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("Average Transaction", f"${avg_txn:,.2f}", "📊", color="blue"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Monthly Volume", f"{monthly_vol:,.0f}", "📈", color="gold"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Highest Transaction", f"${max_txn:,.2f}", "🔝", color="green"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Lowest Transaction", f"${min_txn:,.2f}", "🔻", color="teal"), unsafe_allow_html=True)

st.markdown("---")

# ── Charts ──
# Row 1: Monthly Transactions & Transaction Volume
c1, c2 = st.columns(2)

with c1:
    monthly = txn_df.groupby("month").agg(count=("amount", "size"), total=("amount", "sum")).reset_index()
    fig = create_bar_chart(monthly, "month", "count", "📊 Monthly Transaction Count")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = create_area_chart(monthly, "month", "total", "📈 Transaction Volume (Amount)")
    st.plotly_chart(fig, use_container_width=True)

# Row 2: Deposit Trend & Withdrawal Trend
c3, c4 = st.columns(2)

with c3:
    deposits = txn_df[txn_df["type"] == "Deposit"].groupby("month")["amount"].sum().reset_index()
    fig = create_line_chart(deposits, "month", "amount", "💰 Deposit Trend")
    st.plotly_chart(fig, use_container_width=True)

with c4:
    withdrawals = txn_df[txn_df["type"] == "Withdrawal"].groupby("month")["amount"].sum().reset_index()
    fig = create_line_chart(withdrawals, "month", "amount", "💸 Withdrawal Trend")
    st.plotly_chart(fig, use_container_width=True)

# Row 3: Branch Transactions & Payment Channel
c5, c6 = st.columns(2)

with c5:
    # Get branch info by joining with customers
    cust_df = pd.read_sql("SELECT customer_id, branch FROM customers", conn)
    branch_txn = txn_df.merge(cust_df, on="customer_id", how="left")
    branch_summary = branch_txn.groupby("branch")["amount"].agg(["count", "sum"]).reset_index()
    branch_summary.columns = ["branch", "count", "total"]
    branch_summary = branch_summary.sort_values("count", ascending=False).head(10)
    fig = create_bar_chart(branch_summary, "branch", "count", "🏢 Branch Transaction Count")
    st.plotly_chart(fig, use_container_width=True)

with c6:
    channel = txn_df.groupby("channel")["amount"].size().reset_index(name="count")
    fig = create_pie_chart(channel, "channel", "count", "📱 Payment Channel Distribution")
    st.plotly_chart(fig, use_container_width=True)

# Row 4: Merchant Analysis & Transaction Heatmap
c7, c8 = st.columns(2)

with c7:
    merchant_df = txn_df[txn_df["merchant"] != ""].groupby("merchant")["amount"].agg(["count", "sum"]).reset_index()
    merchant_df.columns = ["merchant", "count", "total"]
    merchant_df = merchant_df.sort_values("total", ascending=False).head(15)
    if not merchant_df.empty:
        fig = create_bar_chart(merchant_df, "merchant", "total", "🏪 Top Merchants by Amount", orientation="v")
        st.plotly_chart(fig, use_container_width=True)

with c8:
    # Transaction heatmap by day of week
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    type_day = txn_df.groupby(["day_of_week", "type"]).size().reset_index(name="count")
    pivot = type_day.pivot_table(index="day_of_week", columns="type", values="count", fill_value=0)
    # Reorder
    available_days = [d for d in days_order if d in pivot.index]
    if available_days:
        pivot = pivot.reindex(available_days)
        fig = create_heatmap(pivot.values, pivot.columns.tolist(), pivot.index.tolist(), "🗓️ Transaction Heatmap")
        st.plotly_chart(fig, use_container_width=True)

conn.close()
