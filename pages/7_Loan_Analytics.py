"""
Loan Analytics Page — KPIs, distributions, and loan portfolio analysis.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.visualization import (
    kpi_card, create_bar_chart, create_pie_chart, create_gauge,
    create_sunburst, create_box_plot, create_scatter, create_histogram
)

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Loan Analytics")

st.markdown("# 🏦 Loan Analytics")
st.markdown("Loan portfolio analysis, approval rates, and risk metrics")
st.markdown("---")

conn = get_connection()
loans_df = pd.read_sql("SELECT * FROM loans", conn)

if loans_df.empty:
    st.warning("⚠️ No loan data available.")
    conn.close()
    st.stop()

# ── KPI Cards ──
total_loans = len(loans_df)
active_loans = len(loans_df[loans_df["status"] == "Active"])
closed_loans = len(loans_df[loans_df["status"] == "Closed"])
defaulted = len(loans_df[loans_df["status"] == "Defaulted"])
default_rate = round(defaulted / max(total_loans, 1) * 100, 1)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(kpi_card("Total Loans", f"{total_loans:,}", "📋", color="blue"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi_card("Active Loans", f"{active_loans:,}", "✅", color="green"), unsafe_allow_html=True)
with k3:
    st.markdown(kpi_card("Closed Loans", f"{closed_loans:,}", "🔒", color="teal"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi_card("Default Rate", f"{default_rate}%", "⚠️", color="red"), unsafe_allow_html=True)

st.markdown("---")

# ── Charts ──
c1, c2 = st.columns(2)

with c1:
    fig = create_histogram(loans_df, "loan_amount", "💰 Loan Amount Distribution", nbins=40)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    approved = len(loans_df[loans_df["status"].isin(["Active", "Closed"])])
    approval_rate = round(approved / max(total_loans, 1) * 100, 1)
    fig = create_gauge(approval_rate, "Loan Approval Rate (%)", 0, 100)
    st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    type_dist = loans_df.groupby("loan_type").agg(
        count=("loan_id", "count"),
        total_amount=("loan_amount", "sum")
    ).reset_index()
    fig = create_pie_chart(type_dist, "loan_type", "count", "📊 Loan Type Distribution", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with c4:
    fig = create_box_plot(loans_df, "loan_type", "interest_rate", "📈 Interest Rate by Loan Type")
    st.plotly_chart(fig, use_container_width=True)

c5, c6 = st.columns(2)

with c5:
    if "emi" in loans_df.columns:
        fig = create_scatter(loans_df, "loan_amount", "emi", "💳 EMI vs Loan Amount", color="loan_type")
        st.plotly_chart(fig, use_container_width=True)

with c6:
    # Branch-wise loans
    cust_df = pd.read_sql("SELECT customer_id, branch FROM customers", conn)
    loan_branch = loans_df.merge(cust_df, on="customer_id", how="left")
    branch_loans = loan_branch.groupby("branch")["loan_amount"].agg(["count", "sum"]).reset_index()
    branch_loans.columns = ["branch", "count", "total"]
    branch_loans = branch_loans.sort_values("total", ascending=False).head(10)
    fig = create_bar_chart(branch_loans, "branch", "total", "🏢 Branch-wise Loan Amount")
    st.plotly_chart(fig, use_container_width=True)

# ── Loan Details Table ──
st.markdown("---")
st.markdown("### 📋 Loan Details")
status_filter = st.multiselect("Filter by Status", loans_df["status"].unique().tolist(), default=loans_df["status"].unique().tolist())
filtered = loans_df[loans_df["status"].isin(status_filter)]
st.dataframe(filtered, use_container_width=True, height=300)

conn.close()
