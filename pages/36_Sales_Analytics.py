"""
Sales Analytics — Admin sales overview with charts and trend analysis.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from authentication import check_auth, require_role
from database import get_connection
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON, CHART_COLORS

st.set_page_config(page_title=f"{APP_NAME} — Sales Analytics", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Sales Analytics")

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("trending_up", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Sales Analytics</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

conn = get_connection()

# KPIs
total_orders = pd.read_sql("SELECT COUNT(*) as c FROM orders", conn).iloc[0]["c"]
total_gmv = pd.read_sql("SELECT COALESCE(SUM(net_amount), 0) as s FROM orders", conn).iloc[0]["s"]
avg_order = total_gmv / total_orders if total_orders > 0 else 0
delivered = pd.read_sql("SELECT COUNT(*) as c FROM orders WHERE status='Delivered'", conn).iloc[0]["c"]

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="kpi-card blue animate-in"><div class="kpi-value">{total_orders}</div><div class="kpi-label">Total Orders</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card green animate-in"><div class="kpi-value">\u20b9{total_gmv:,.0f}</div><div class="kpi-label">Total GMV</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card gold animate-in"><div class="kpi-value">\u20b9{avg_order:,.0f}</div><div class="kpi-label">Avg Order Value</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card teal animate-in"><div class="kpi-value">{delivered}</div><div class="kpi-label">Delivered</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Charts
col1, col2 = st.columns(2)

with col1:
    # Sales by vendor
    df = pd.read_sql("""
        SELECT v.business_name, SUM(oi.total_price) as revenue
        FROM order_items oi
        JOIN vendors v ON oi.vendor_id = v.vendor_id
        GROUP BY v.business_name
        ORDER BY revenue DESC
    """, conn)
    if not df.empty:
        fig = px.bar(df, x="business_name", y="revenue", title="Revenue by Vendor",
                     color_discrete_sequence=CHART_COLORS)
        fig.update_layout(template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sales data yet.")

with col2:
    # Order status breakdown
    df = pd.read_sql("SELECT status, COUNT(*) as count FROM orders GROUP BY status", conn)
    if not df.empty:
        fig = px.pie(df, names="status", values="count", title="Order Status Breakdown",
                     color_discrete_sequence=CHART_COLORS)
        fig.update_layout(template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)

# Top selling products
st.markdown(f'<div class="section-header">{render_html_icon("trending_up", size="18px")} Top Selling Products</div>', unsafe_allow_html=True)
df_top = pd.read_sql("""
    SELECT p.name, p.price, SUM(oi.quantity) as units_sold, SUM(oi.total_price) as revenue
    FROM order_items oi
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY p.name
    ORDER BY revenue DESC
    LIMIT 10
""", conn)
if not df_top.empty:
    st.dataframe(df_top, use_container_width=True, hide_index=True)
else:
    st.info("No sales data yet.")

# Payment methods
st.markdown(f'<div class="section-header">{render_html_icon("credit_card", size="18px")} Payment Method Distribution</div>', unsafe_allow_html=True)
df_pay = pd.read_sql("SELECT method, COUNT(*) as count, SUM(amount) as total FROM payments GROUP BY method", conn)
if not df_pay.empty:
    fig = px.bar(df_pay, x="method", y="total", title="Revenue by Payment Method",
                 text="count", color_discrete_sequence=CHART_COLORS)
    fig.update_layout(template="plotly_white", height=350)
    st.plotly_chart(fig, use_container_width=True)

conn.close()
