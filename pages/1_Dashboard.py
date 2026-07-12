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
from config import REGIONS, BRANCHES
from utils.icons import render_html_icon

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Dashboard")

st.markdown(f"# {render_html_icon('dashboard', size='30px')} Executive Dashboard", unsafe_allow_html=True)
st.markdown("Real-time banking KPIs and performance metrics")

# ──────────────────────────────────────────────
# Interactive Filters Panel (Top Bar)
# ──────────────────────────────────────────────
st.markdown('<div class="form-card">', unsafe_allow_html=True)
st.markdown(f'<h5 style="margin-top:0; margin-bottom:12px; color:var(--primary); font-weight:700; display:flex; align-items:center; gap:6px;">{render_html_icon("search", size="20px")} Filter Dashboard</h5>', unsafe_allow_html=True)
col_f1, col_f2 = st.columns(2)

# Preserve/Initialize filter states in session state
if "filter_region" not in st.session_state:
    st.session_state["filter_region"] = "All"
if "filter_branch" not in st.session_state:
    st.session_state["filter_branch"] = "All"

# Region filter
region_options = ["All"] + REGIONS
try:
    region_idx = region_options.index(st.session_state["filter_region"])
except ValueError:
    region_idx = 0
selected_region = col_f1.selectbox("Filter by Region", region_options, index=region_idx, key="dashboard_filter_region_select")
st.session_state["filter_region"] = selected_region

# Branch filter
branch_options = ["All"] + BRANCHES
try:
    branch_idx = branch_options.index(st.session_state["filter_branch"])
except ValueError:
    branch_idx = 0
selected_branch = col_f2.selectbox("Filter by Branch", branch_options, index=branch_idx, key="dashboard_filter_branch_select")
st.session_state["filter_branch"] = selected_branch
st.markdown('</div>', unsafe_allow_html=True)

# Build dynamic WHERE clause based on filters
where_clause_cust = "1=1"
where_clause_joined = "1=1"
params = []

if selected_region != "All":
    where_clause_cust += " AND region = ?"
    where_clause_joined += " AND customers.region = ?"
    params.append(selected_region)

if selected_branch != "All":
    where_clause_cust += " AND branch = ?"
    where_clause_joined += " AND customers.branch = ?"
    params.append(selected_branch)

conn = get_connection()

# ──────────────────────────────────────────────
# KPI Cards Calculations & Display
# ──────────────────────────────────────────────
total_customers = pd.read_sql(f"SELECT COUNT(*) as c FROM customers WHERE {where_clause_cust}", conn, params=params).iloc[0]["c"]
total_accounts = pd.read_sql(f"SELECT COUNT(*) as c FROM accounts JOIN customers ON accounts.customer_id = customers.customer_id WHERE {where_clause_joined}", conn, params=params).iloc[0]["c"]
active_customers = pd.read_sql(f"SELECT COUNT(*) as c FROM customers WHERE is_active = 1 AND {where_clause_cust}", conn, params=params).iloc[0]["c"]
total_deposits = pd.read_sql(f"SELECT COALESCE(SUM(amount), 0) as s FROM transactions JOIN customers ON transactions.customer_id = customers.customer_id WHERE type = 'Deposit' AND {where_clause_joined}", conn, params=params).iloc[0]["s"]
total_loans_amt = pd.read_sql(f"SELECT COALESCE(SUM(loan_amount), 0) as s FROM loans JOIN customers ON loans.customer_id = customers.customer_id WHERE {where_clause_joined}", conn, params=params).iloc[0]["s"]
avg_balance = pd.read_sql(f"SELECT COALESCE(AVG(balance), 0) as a FROM customers WHERE {where_clause_cust}", conn, params=params).iloc[0]["a"]
total_revenue = pd.read_sql(f"SELECT COALESCE(SUM(amount), 0) as s FROM transactions JOIN customers ON transactions.customer_id = customers.customer_id WHERE {where_clause_joined}", conn, params=params).iloc[0]["s"]
monthly_txns = pd.read_sql(f"SELECT COUNT(*) as c FROM transactions JOIN customers ON transactions.customer_id = customers.customer_id WHERE date >= date((SELECT MAX(date) FROM transactions), '-30 days') AND {where_clause_joined}", conn, params=params).iloc[0]["c"]
churn_rate = round((1 - active_customers / max(total_customers, 1)) * 100, 1)

# Row 1
r1c1, r1c2, r1c3, r1c4 = st.columns(4)
with r1c1:
    st.markdown(kpi_card("Total Customers", f"{total_customers:,}", "", delta=3.2, delta_label="vs last quarter", color="blue"), unsafe_allow_html=True)
with r1c2:
    st.markdown(kpi_card("Total Accounts", f"{total_accounts:,}", "", delta=1.5, delta_label="vs last quarter", color="blue"), unsafe_allow_html=True)
with r1c3:
    st.markdown(kpi_card("Active Customers", f"{active_customers:,}", "", delta=2.1, delta_label="vs last quarter", color="blue"), unsafe_allow_html=True)
with r1c4:
    st.markdown(kpi_card("Total Deposits", f"${total_deposits:,.0f}", "", delta=-0.8, delta_label="vs last quarter", color="blue"), unsafe_allow_html=True)

# Row 2
r2c1, r2c2, r2c3, r2c4 = st.columns(4)
with r2c1:
    st.markdown(kpi_card("Total Loan Volume", f"${total_loans_amt:,.0f}", "", delta=4.6, delta_label="vs last quarter", color="blue"), unsafe_allow_html=True)
with r2c2:
    st.markdown(kpi_card("Avg Balance", f"${avg_balance:,.0f}", "", delta=0.5, delta_label="vs last quarter", color="blue"), unsafe_allow_html=True)
with r2c3:
    st.markdown(kpi_card("Monthly Transactions", f"{monthly_txns:,}", "", delta=6.2, delta_label="vs last month", color="blue"), unsafe_allow_html=True)
with r2c4:
    st.markdown(kpi_card("Churn Rate", f"{churn_rate}%", "", delta=-1.2, delta_label="vs last month", color="red"), unsafe_allow_html=True)

# Row 3
r3c1, r3c2, r3c3 = st.columns(3)
with r3c1:
    st.markdown(kpi_card("Total Revenue", f"${total_revenue:,.0f}", "", delta=8.4, delta_label="vs last quarter", color="blue"), unsafe_allow_html=True)
with r3c2:
    total_loans_count = pd.read_sql(f"SELECT COUNT(*) as c FROM loans JOIN customers ON loans.customer_id = customers.customer_id WHERE {where_clause_joined}", conn, params=params).iloc[0]["c"]
    st.markdown(kpi_card("Total Loan Accounts", f"{total_loans_count:,}", "", delta=2.3, delta_label="vs last quarter", color="blue"), unsafe_allow_html=True)
with r3c3:
    avg_credit = pd.read_sql(f"SELECT COALESCE(AVG(credit_score), 0) as a FROM customers WHERE {where_clause_cust}", conn, params=params).iloc[0]["a"]
    st.markdown(kpi_card("Avg Credit Score", f"{avg_credit:.0f}", "", delta=0.2, delta_label="vs last month", color="blue"), unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Dashboard Charts
# ──────────────────────────────────────────────
st.markdown(f'<div class="section-header">{render_html_icon("analytics", size="22px")} Performance Analytics</div>', unsafe_allow_html=True)

# Row 1: Customer Growth & Deposits Trend
ch1, ch2 = st.columns(2)

with ch1:
    df_growth = pd.read_sql(f"""
        SELECT strftime('%Y-%m', customer_since) as month, COUNT(*) as new_customers
        FROM customers
        WHERE customer_since IS NOT NULL AND {where_clause_cust}
        GROUP BY month ORDER BY month
    """, conn, params=params)
    if not df_growth.empty:
        df_growth["cumulative"] = df_growth["new_customers"].cumsum()
        df_growth.rename(columns={"month": "Month", "cumulative": "Customers"}, inplace=True)
        fig = create_area_chart(df_growth, "Month", "Customers", "Customer Growth Over Time")
        # Dual-line visual style: px.area will show a nice transparent gradient fill under the line
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

with ch2:
    df_deposits = pd.read_sql(f"""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as total_deposits
        FROM transactions JOIN customers ON transactions.customer_id = customers.customer_id
        WHERE type = 'Deposit' AND {where_clause_joined}
        GROUP BY month ORDER BY month
    """, conn, params=params)
    if not df_deposits.empty:
        df_deposits.rename(columns={"month": "Month", "total_deposits": "Total Deposits ($)"}, inplace=True)
        fig = create_bar_chart(df_deposits, "Month", "Total Deposits ($)", "Monthly Deposits Trend")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# Row 2: Loan Trend & Revenue Trend
ch3, ch4 = st.columns(2)

with ch3:
    df_loans = pd.read_sql(f"""
        SELECT loan_type, COUNT(*) as count, SUM(loan_amount) as total_amount
        FROM loans JOIN customers ON loans.customer_id = customers.customer_id
        WHERE {where_clause_joined}
        GROUP BY loan_type ORDER BY total_amount DESC
    """, conn, params=params)
    if not df_loans.empty:
        df_loans.rename(columns={"loan_type": "Loan Type", "total_amount": "Total Value ($)"}, inplace=True)
        fig = create_bar_chart(df_loans, "Loan Type", "Total Value ($)", "Loan Distribution by Type")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

with ch4:
    df_revenue = pd.read_sql(f"""
        SELECT strftime('%Y-%m', date) as month, SUM(amount) as revenue
        FROM transactions JOIN customers ON transactions.customer_id = customers.customer_id
        WHERE {where_clause_joined}
        GROUP BY month ORDER BY month
    """, conn, params=params)
    if not df_revenue.empty:
        df_revenue.rename(columns={"month": "Month", "revenue": "Total Revenue ($)"}, inplace=True)
        fig = create_line_chart(df_revenue, "Month", "Total Revenue ($)", "Revenue Trend")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# Row 3: Customer Distribution & Regional Analysis
ch5, ch6 = st.columns(2)

with ch5:
    df_region = pd.read_sql(f"""
        SELECT region, COUNT(*) as customers FROM customers
        WHERE {where_clause_cust}
        GROUP BY region ORDER BY customers DESC
    """, conn, params=params)
    if not df_region.empty:
        df_region.rename(columns={"region": "Region", "customers": "Customers"}, inplace=True)
        fig = create_pie_chart(df_region, "Region", "Customers", "Customer Distribution by Region")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

with ch6:
    df_branch = pd.read_sql(f"""
        SELECT branch, COUNT(*) as customers FROM customers
        WHERE {where_clause_cust}
        GROUP BY branch ORDER BY customers DESC LIMIT 10
    """, conn, params=params)
    if not df_branch.empty:
        df_branch.rename(columns={"branch": "Branch", "customers": "Customers"}, inplace=True)
        fig = create_bar_chart(df_branch, "Branch", "Customers", "Top Branches by Customers")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# Row 4: Monthly Transactions & Product Distribution
ch7, ch8 = st.columns(2)

with ch7:
    df_monthly = pd.read_sql(f"""
        SELECT strftime('%Y-%m', date) as month, type, COUNT(*) as count
        FROM transactions JOIN customers ON transactions.customer_id = customers.customer_id
        WHERE {where_clause_joined}
        GROUP BY month, type ORDER BY month
    """, conn, params=params)
    if not df_monthly.empty:
        df_monthly.rename(columns={"month": "Month", "count": "Transactions", "type": "Transaction Type"}, inplace=True)
        fig = create_bar_chart(df_monthly, "Month", "Transactions", "Monthly Transactions by Type", color="Transaction Type", barmode="stack")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

with ch8:
    df_products = pd.read_sql(f"""
        SELECT account_type, COUNT(*) as count FROM accounts
        JOIN customers ON accounts.customer_id = customers.customer_id
        WHERE {where_clause_joined}
        GROUP BY account_type ORDER BY count DESC
    """, conn, params=params)
    if not df_products.empty:
        df_products.rename(columns={"account_type": "Account Type", "count": "Accounts"}, inplace=True)
        fig = create_donut_chart(df_products, "Account Type", "Accounts", "Product Distribution")
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

conn.close()