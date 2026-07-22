"""
Vendor Dashboard — Vendor-specific analytics with sales, products,
orders overview and commission summary.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from authentication import check_auth, require_role
from database import get_connection
from utils.marketplace import get_vendor_by_user_id, get_all_products, get_vendor_commissions
from utils.orders import get_all_orders
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON, CHART_COLORS

st.set_page_config(page_title=f"{APP_NAME} — Vendor Dashboard", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Vendor Dashboard")

vendor = get_vendor_by_user_id(user["user_id"])
if not vendor:
    st.error("Vendor profile not found.", icon=":material/error:")
    st.stop()

vid = vendor["vendor_id"]

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("space_dashboard", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Vendor Dashboard</h1>
</div>
<p style="color:#6C757D;margin-top:-0.5rem;">Welcome back, <strong>{vendor['business_name']}</strong>!</p>
""", unsafe_allow_html=True)
st.markdown("---")

# Load data
products = get_all_products(vendor_id=vid)
orders = get_all_orders(vendor_id=vid)
commissions = get_vendor_commissions(vid)

# KPIs
total_revenue = sum(o["net_amount"] for o in orders)
total_orders = len(orders)
active_products = sum(1 for p in products if p["status"] == "Active")
total_commission = sum(c["commission_amount"] for c in commissions)

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="kpi-card blue animate-in"><div class="kpi-icon" style="color:var(--secondary);">{render_html_icon("payments", size="2.5rem")}</div><div class="kpi-value">\u20b9{total_revenue:,.0f}</div><div class="kpi-label">Total Revenue</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card green animate-in"><div class="kpi-icon" style="color:var(--success);">{render_html_icon("receipt_long", size="2.5rem")}</div><div class="kpi-value">{total_orders}</div><div class="kpi-label">Total Orders</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card gold animate-in"><div class="kpi-icon" style="color:var(--accent);">{render_html_icon("inventory_2", size="2.5rem")}</div><div class="kpi-value">{active_products}</div><div class="kpi-label">Active Products</div></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card teal animate-in"><div class="kpi-icon" style="color:var(--info);">{render_html_icon("account_balance_wallet", size="2.5rem")}</div><div class="kpi-value">\u20b9{total_commission:,.0f}</div><div class="kpi-label">Commission Earned</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Charts
if orders:
    col1, col2 = st.columns(2)

    with col1:
        # Order status distribution
        status_counts = pd.DataFrame(orders).groupby("status").size().reset_index(name="count")
        fig = px.pie(status_counts, names="status", values="count", title="Order Status Distribution",
                     color_discrete_sequence=CHART_COLORS)
        fig.update_layout(template="plotly_white", height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Top products by revenue
        conn = get_connection()
        df_items = pd.read_sql(f"""
            SELECT p.name, SUM(oi.total_price) as revenue
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.vendor_id = '{vid}'
            GROUP BY p.name
            ORDER BY revenue DESC
            LIMIT 5
        """, conn)
        conn.close()
        if not df_items.empty:
            fig = px.bar(df_items, x="name", y="revenue", title="Top Products by Revenue",
                         color_discrete_sequence=CHART_COLORS)
            fig.update_layout(template="plotly_white", height=350, xaxis_title="Product", yaxis_title="Revenue")
            st.plotly_chart(fig, use_container_width=True)

# Recent orders
st.markdown(f'<div class="section-header">{render_html_icon("history", size="18px")} Recent Orders</div>', unsafe_allow_html=True)
if orders:
    df_orders = pd.DataFrame(orders[:10])
    cols = ["order_id", "customer_id", "net_amount", "status", "placed_at"]
    cols = [c for c in cols if c in df_orders.columns]
    st.dataframe(df_orders[cols], use_container_width=True, hide_index=True)
else:
    st.info("No orders yet. Products need to be purchased first.", icon=":material/info:")
