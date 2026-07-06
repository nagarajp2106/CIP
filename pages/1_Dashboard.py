"""
Dashboard Page — Banking KPIs, interactive charts, and executive summary.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from authentication import check_auth, require_role
from database import get_connection
from utils.visualization import (
    kpi_card, create_line_chart, create_bar_chart, create_pie_chart,
    create_donut_chart, create_area_chart, apply_layout, CHART_COLORS
)

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Dashboard")

st.markdown("# 📊 Executive Dashboard")
st.markdown("Real-time banking KPIs and performance metrics")
st.markdown("---")

conn = get_connection()

# ──────────────────────────────────────────────
# KPI Cards
# ──────────────────────────────────────────────
total_customers = pd.read_sql("SELECT COUNT(*) as c FROM customers", conn).iloc[0]["c"]
total_accounts = pd.read_sql("SELECT COUNT(*) as c FROM accounts", conn).iloc[0]["c"]
active_customers = pd.read_sql("SELECT COUNT(*) as c FROM customers WHERE is_active = 1", conn).iloc[0]["c"]
total_deposits = pd.read_sql("SELECT COALESCE(SUM(amount), 0) as s FROM transactions WHERE type = 'Deposit'", conn).iloc[0]["s"]
total_loans_amt = pd.read_sql("SELECT COALESCE(SUM(loan_amount), 0) as s FROM loans", conn).iloc[0]["s"]
avg_balance = pd.read_sql("SELECT COALESCE(AVG(balance), 0) as a FROM customers", conn).iloc[0]["a"]
total_revenue = pd.read_sql("SELECT COALESCE(SUM(amount), 0) as s FROM transactions", conn).iloc[0]["s"]
monthly_txns = pd.read_sql("SELECT COUNT(*) as c FROM transactions WHERE date >= date('now', '-30 days')", conn).iloc[0]["c"]
churn_rate = round((1 - active_customers / max(total_customers, 1)) * 100, 1)
fraud_alerts = pd.read_sql("SELECT COUNT(*) as c FROM transactions WHERE is_fraud = 1", conn).iloc[0]["c"]

# Loan approval rate
total_loans = pd.read_sql("SELECT COUNT(*) as c FROM loans", conn).iloc[0]["c"]
approved_loans = pd.read_sql("SELECT COUNT(*) as c FROM loans WHERE status IN ('Active', 'Closed')", conn).iloc[0]["c"]
approval_rate = round(approved_loans / max(total_loans, 1) * 100, 1)

# Row 1
r1c1, r1c2, r1c3, r1c4 = st.columns(4)
with r1c1:
    st.markdown(kpi_card("Total Customers", f"{total_customers:,}", "👥", color="blue"), unsafe_allow_html=True)
with r1c2:
    st.markdown(kpi_card("Total Accounts", f"{total_accounts:,}", "🏧", color="gold"), unsafe_allow_html=True)
with r1c3:
    st.markdown(kpi_card("Active Customers", f"{active_customers:,}", "✅", color="green"), unsafe_allow_html=True)
with r1c4:
    st.markdown(kpi_card("Total Deposits", f"${total_deposits:,.0f}", "💰", color="teal"), unsafe_allow_html=True)

# Row 2
r2c1, r2c2, r2c3, r2c4 = st.columns(4)
with r2c1:
    st.markdown(kpi_card("Total Loans", f"${total_loans_amt:,.0f}", "🏦", color="purple"), unsafe_allow_html=True)
with r2c2:
    st.markdown(kpi_card("Avg Balance", f"${avg_balance:,.0f}", "📈", color="blue"), unsafe_allow_html=True)
with r2c3:
    st.markdown(kpi_card("Monthly Transactions", f"{monthly_txns:,}", "💳", color="orange"), unsafe_allow_html=True)
with r2c4:
    st.markdown(kpi_card("Churn Rate", f"{churn_rate}%", "📉", color="red"), unsafe_allow_html=True)

# Row 3
r3c1, r3c2, r3c3 = st.columns(3)
with r3c1:
    st.markdown(kpi_card("Total Revenue", f"${total_revenue:,.0f}", "💵", color="green"), unsafe_allow_html=True)
with r3c2:
    st.markdown(kpi_card("Fraud Alerts", f"{fraud_alerts:,}", "🛡️", color="red"), unsafe_allow_html=True)
with r3c3:
    st.markdown(kpi_card("Loan Approval Rate", f"{approval_rate}%", "✔️", color="teal"), unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Dashboard Charts
# ──────────────────────────────────────────────
st.markdown('<div class="section-header">📈 Performance Analytics</div>', unsafe_allow_html=True)

# Row 1: Customer Growth & Deposits Trend
ch1, ch2 = st.columns(2)

with ch1:
    df_growth = pd.read_sql("""
        SELECT strftime('%Y-%m', customer_since) as month, COUNT(*) as new_customers
        FROM customers
        WHERE customer_since IS NOT NULL
        GROUP BY month ORDER BY month
    """, conn)
    if not df_growth.empty:
        df_growth["cumulative"] = df_growth["new_customers"].cumsum()
        fig = create_area_chart(df_growth, "month", "cumulative", "📈 Customer Growth Over Time")
        st.plotly_chart(fig, use_container_width=True)

with ch2:
    df_deposits = pd.read_sql("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total_deposits
        FROM transactions WHERE type = 'Deposit'
        GROUP BY month ORDER BY month
    """, conn)
    if not df_deposits.empty:
        fig = create_bar_chart(df_deposits, "month", "total_deposits", "💰 Monthly Deposits Trend")
        st.plotly_chart(fig, use_container_width=True)

# Row 2: Loan Trend & Revenue Trend
ch3, ch4 = st.columns(2)

with ch3:
    df_loans = pd.read_sql("""
        SELECT loan_type, COUNT(*) as count, SUM(loan_amount) as total_amount
        FROM loans GROUP BY loan_type ORDER BY total_amount DESC
    """, conn)
    if not df_loans.empty:
        fig = create_bar_chart(df_loans, "loan_type", "total_amount", "🏦 Loan Distribution by Type")
        st.plotly_chart(fig, use_container_width=True)

with ch4:
    df_revenue = pd.read_sql("""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as revenue
        FROM transactions GROUP BY month ORDER BY month
    """, conn)
    if not df_revenue.empty:
        fig = create_line_chart(df_revenue, "month", "revenue", "💵 Revenue Trend")
        st.plotly_chart(fig, use_container_width=True)

# Row 3: Customer Distribution & Regional Analysis
ch5, ch6 = st.columns(2)

with ch5:
    df_region = pd.read_sql("""
        SELECT region, COUNT(*) as customers FROM customers
        GROUP BY region ORDER BY customers DESC
    """, conn)
    if not df_region.empty:
        fig = create_pie_chart(df_region, "region", "customers", "🌍 Customer Distribution by Region")
        st.plotly_chart(fig, use_container_width=True)

with ch6:
    df_branch = pd.read_sql("""
        SELECT branch, COUNT(*) as customers FROM customers
        GROUP BY branch ORDER BY customers DESC LIMIT 10
    """, conn)
    if not df_branch.empty:
        fig = create_bar_chart(df_branch, "branch", "customers", "🏢 Top Branches by Customers")
        st.plotly_chart(fig, use_container_width=True)

# Row 4: Monthly Transactions & Product Distribution
ch7, ch8 = st.columns(2)

with ch7:
    df_monthly = pd.read_sql("""
        SELECT strftime('%Y-%m', date) as month, type, COUNT(*) as count
        FROM transactions GROUP BY month, type ORDER BY month
    """, conn)
    if not df_monthly.empty:
        fig = create_bar_chart(df_monthly, "month", "count", "💳 Monthly Transactions by Type", color="type", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

with ch8:
    df_products = pd.read_sql("""
        SELECT account_type, COUNT(*) as count FROM accounts
        GROUP BY account_type ORDER BY count DESC
    """, conn)
    if not df_products.empty:
        fig = create_donut_chart(df_products, "account_type", "count", "📦 Product Distribution")
        st.plotly_chart(fig, use_container_width=True)

conn.close()
