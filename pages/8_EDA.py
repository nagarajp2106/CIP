"""
Exploratory Data Analysis Page — Interactive Plotly visualizations.
"""
import streamlit as st
from utils.icons import render_html_icon
import pandas as pd
import numpy as np
from authentication import check_auth, require_role
from database import get_connection
from utils.visualization import (
    create_histogram, create_bar_chart, create_box_plot, create_violin,
    create_scatter, create_correlation_matrix, create_sunburst,
    create_line_chart, create_pie_chart, apply_layout
)

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("EDA")

st.markdown(f"# {render_html_icon('analytics', size='30px')} Exploratory Data Analysis", unsafe_allow_html=True)
st.markdown("Interactive visualizations for banking data exploration")
st.markdown("---")

conn = get_connection()
customers_df = pd.read_sql("SELECT * FROM customers", conn)
transactions_df = pd.read_sql("SELECT * FROM transactions", conn)
loans_df = pd.read_sql("SELECT * FROM loans", conn)
accounts_df = pd.read_sql("SELECT * FROM accounts", conn)
conn.close()

if customers_df.empty:
    st.warning("No data available for analysis.", icon=":material/warning:")
    st.stop()

# Summary stats
st.markdown(f"### {render_html_icon('analytics', size='22px')} Summary Statistics", unsafe_allow_html=True)
numeric_df = customers_df.select_dtypes(include=[np.number])
st.dataframe(numeric_df.describe().round(2), use_container_width=True)

st.markdown("---")

# ── Row 1: Age & Income ──
c1, c2 = st.columns(2)
with c1:
    fig = create_histogram(customers_df, "age", "Age Distribution", nbins=30)
    st.plotly_chart(fig, use_container_width=True)
with c2:
    fig = create_violin(customers_df, "occupation", "income", "Income by Occupation")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Balance & Loan Amount ──
c3, c4 = st.columns(2)
with c3:
    fig = create_box_plot(customers_df, "region", "balance", "Balance by Region")
    st.plotly_chart(fig, use_container_width=True)
with c4:
    if not loans_df.empty:
        fig = create_histogram(loans_df, "loan_amount", "Loan Amount Distribution", nbins=40)
        st.plotly_chart(fig, use_container_width=True)

# ── Row 3: Transaction Distribution & Correlation ──
c5, c6 = st.columns(2)
with c5:
    if not transactions_df.empty:
        fig = create_histogram(transactions_df, "amount", "Transaction Amount Distribution", nbins=50)
        st.plotly_chart(fig, use_container_width=True)
with c6:
    fig = create_correlation_matrix(customers_df, "Correlation Matrix")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 4: Branch & Occupation Analysis ──
c7, c8 = st.columns(2)
with c7:
    branch_stats = customers_df.groupby("branch").agg(
        count=("customer_id", "count"),
        avg_balance=("balance", "mean")
    ).reset_index().sort_values("count", ascending=False)
    fig = create_bar_chart(branch_stats, "branch", "count", "Branch Analysis — Customer Count")
    st.plotly_chart(fig, use_container_width=True)
with c8:
    occ_stats = customers_df.groupby("occupation").agg(
        count=("customer_id", "count"),
        avg_income=("income", "mean")
    ).reset_index()
    fig = create_bar_chart(occ_stats, "occupation", "avg_income", "Average Income by Occupation")
    st.plotly_chart(fig, use_container_width=True)

# ── Row 5: Regional Analysis & Product Usage ──
c9, c10 = st.columns(2)
with c9:
    region_stats = customers_df.groupby("region").agg(
        customers=("customer_id", "count"),
        avg_balance=("balance", "mean"),
        avg_income=("income", "mean")
    ).reset_index()
    fig = create_bar_chart(region_stats, "region", "customers", "Regional Analysis")
    st.plotly_chart(fig, use_container_width=True)
with c10:
    if not accounts_df.empty:
        product_usage = accounts_df.groupby("account_type").size().reset_index(name="count")
        fig = create_pie_chart(product_usage, "account_type", "count", "Product Usage")
        st.plotly_chart(fig, use_container_width=True)

# ── Monthly Growth ──
st.markdown("---")
if not transactions_df.empty:
    transactions_df["date"] = pd.to_datetime(transactions_df["date"], errors="coerce")
    monthly = transactions_df.groupby(transactions_df["date"].dt.to_period("M").astype(str)).agg(
        transactions=("transaction_id", "count"),
        volume=("amount", "sum")
    ).reset_index()
    monthly.columns = ["month", "transactions", "volume"]
    fig = create_line_chart(monthly, "month", "volume", "Monthly Transaction Volume Growth")
    st.plotly_chart(fig, use_container_width=True)

# ── Custom Analysis ──
st.markdown("---")
st.markdown(f"### {render_html_icon('track_changes', size='22px')} Custom Analysis", unsafe_allow_html=True)
cc1, cc2 = st.columns(2)
with cc1:
    x_col = st.selectbox("X Axis", numeric_df.columns.tolist(), key="eda_x")
with cc2:
    y_col = st.selectbox("Y Axis", [c for c in numeric_df.columns if c != x_col], key="eda_y")

color_col = st.selectbox("Color By (optional)", ["None"] + customers_df.select_dtypes(include=['object']).columns.tolist(), key="eda_color")

fig = create_scatter(
    customers_df, x_col, y_col,
    f"{x_col.title()} vs {y_col.title()}",
    color=color_col if color_col != "None" else None
)
st.plotly_chart(fig, use_container_width=True)