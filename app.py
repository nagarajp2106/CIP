"""
AI-Powered Retail Banking Customer Insights Platform
Main Streamlit Application Entry Point
"""
import streamlit as st
import os
from config import APP_NAME, APP_ICON, ASSETS_DIR, ROLES
from database import init_db, seed_demo_data, seed_marketplace_data
from authentication import login_page, check_auth, logout, get_role_badge_html, render_sidebar
from utils.icons import render_html_icon, get_native_icon

# ──────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Load Custom CSS
# ──────────────────────────────────────────────
css_path = os.path.join(ASSETS_DIR, "style.css")
if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Initialize Database on First Run
# ──────────────────────────────────────────────
@st.cache_resource
def setup_database():
    """Initialize and seed database (runs once)."""
    init_db()
    seed_demo_data()
    seed_marketplace_data()
    return True

setup_database()

# ──────────────────────────────────────────────
# Authentication Gate
# ──────────────────────────────────────────────
user = check_auth()

if not user:
    login_page()
    st.stop()

role = user["role"]

# ──────────────────────────────────────────────
# Sidebar — Authenticated User
# ──────────────────────────────────────────────
render_sidebar("Home")

# ──────────────────────────────────────────────
# Main Content — Welcome Page
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="color: #1B2A4A; font-size: 2.2rem; display: flex; align-items: center; justify-content: center; gap: 8px;">Welcome, {user['full_name']}!</h1>
    <p style="color: #6C757D; font-size: 1.1rem; max-width: 600px; margin: 0 auto;">
        AI-Powered Retail Banking Customer Insights Platform — Your intelligent dashboard for
        customer analytics, risk assessment, and data-driven decision making.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Quick stats
from database import get_connection
import pandas as pd

conn = get_connection()

col1, col2, col3, col4 = st.columns(4)

with col1:
    count = pd.read_sql("SELECT COUNT(*) as c FROM customers", conn).iloc[0]["c"]
    st.markdown(f"""
    <div class="kpi-card blue animate-in">
        <div class="kpi-icon" style="color: var(--secondary);">{render_html_icon("group", size="2.5rem")}</div>
        <div class="kpi-value">{count:,}</div>
        <div class="kpi-label">Total Customers</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    count = pd.read_sql("SELECT COUNT(*) as c FROM accounts", conn).iloc[0]["c"]
    st.markdown(f"""
    <div class="kpi-card gold animate-in">
        <div class="kpi-icon" style="color: var(--accent);">{render_html_icon("credit_card", size="2.5rem")}</div>
        <div class="kpi-value">{count:,}</div>
        <div class="kpi-label">Total Accounts</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    count = pd.read_sql("SELECT COUNT(*) as c FROM transactions", conn).iloc[0]["c"]
    st.markdown(f"""
    <div class="kpi-card green animate-in">
        <div class="kpi-icon" style="color: var(--success);">{render_html_icon("credit_card", size="2.5rem")}</div>
        <div class="kpi-value">{count:,}</div>
        <div class="kpi-label">Total Transactions</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    count = pd.read_sql("SELECT COUNT(*) as c FROM loans", conn).iloc[0]["c"]
    st.markdown(f"""
    <div class="kpi-card teal animate-in">
        <div class="kpi-icon" style="color: var(--info);">{render_html_icon("savings", size="2.5rem")}</div>
        <div class="kpi-value">{count:,}</div>
        <div class="kpi-label">Total Loans</div>
    </div>
    """, unsafe_allow_html=True)

conn.close()

# Marketplace KPIs (for admin/manager)
if role in ["admin", "bank_manager"]:
    st.markdown("---")
    st.markdown(f'<div class="section-header">{render_html_icon("storefront", size="22px")} Marketplace Overview</div>', unsafe_allow_html=True)
    conn = get_connection()
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)

    with mcol1:
        try:
            count = pd.read_sql("SELECT COUNT(*) as c FROM products", conn).iloc[0]["c"]
        except Exception:
            count = 0
        st.markdown(f"""
        <div class="kpi-card blue animate-in">
            <div class="kpi-icon" style="color: var(--secondary);">{render_html_icon("inventory_2", size="2.5rem")}</div>
            <div class="kpi-value">{count:,}</div>
            <div class="kpi-label">Total Products</div>
        </div>
        """, unsafe_allow_html=True)

    with mcol2:
        try:
            count = pd.read_sql("SELECT COUNT(*) as c FROM vendors WHERE status='Active'", conn).iloc[0]["c"]
        except Exception:
            count = 0
        st.markdown(f"""
        <div class="kpi-card gold animate-in">
            <div class="kpi-icon" style="color: var(--accent);">{render_html_icon("storefront", size="2.5rem")}</div>
            <div class="kpi-value">{count:,}</div>
            <div class="kpi-label">Active Vendors</div>
        </div>
        """, unsafe_allow_html=True)

    with mcol3:
        try:
            count = pd.read_sql("SELECT COUNT(*) as c FROM orders", conn).iloc[0]["c"]
        except Exception:
            count = 0
        st.markdown(f"""
        <div class="kpi-card green animate-in">
            <div class="kpi-icon" style="color: var(--success);">{render_html_icon("receipt_long", size="2.5rem")}</div>
            <div class="kpi-value">{count:,}</div>
            <div class="kpi-label">Marketplace Orders</div>
        </div>
        """, unsafe_allow_html=True)

    with mcol4:
        try:
            gmv = pd.read_sql("SELECT COALESCE(SUM(net_amount), 0) as g FROM orders", conn).iloc[0]["g"]
        except Exception:
            gmv = 0
        st.markdown(f"""
        <div class="kpi-card teal animate-in">
            <div class="kpi-icon" style="color: var(--info);">{render_html_icon("payments", size="2.5rem")}</div>
            <div class="kpi-value">\u20b9{gmv:,.0f}</div>
            <div class="kpi-label">GMV (Total Sales)</div>
        </div>
        """, unsafe_allow_html=True)

    conn.close()

st.markdown("---")

# Navigation cards for quick access
st.markdown(f'<div class="section-header">{render_html_icon("explore", size="22px")} Quick Navigation</div>', unsafe_allow_html=True)

role = user["role"]
nav_items = []

if role in ["admin", "bank_manager", "data_analyst"]:
    nav_items.append(("dashboard", "Dashboard", "View KPIs, charts, and executive summary", "pages/1_Dashboard.py"))
if role in ["admin", "data_analyst"]:
    nav_items.append(("upload_file", "Data Upload", "Upload and validate banking datasets", "pages/2_Data_Upload.py"))
if role in ["admin", "bank_manager"]:
    nav_items.append(("group", "Customer Management", "Search, view, and manage customers", "pages/5_Customer_Management.py"))
if role in ["admin", "bank_manager"]:
    nav_items.append(("account_balance", "Loan Analytics", "Loan portfolio analysis and metrics", "pages/7_Loan_Analytics.py"))
if role in ["admin", "bank_manager"]:
    nav_items.append(("change_circle", "Churn Prediction", "Predict customer churn probability", "pages/10_Churn_Prediction.py"))
if role in ["admin", "bank_manager"]:
    nav_items.append(("insights", "CLV Prediction", "Estimate customer lifetime value", "pages/13_CLV_Prediction.py"))
if role in ["admin", "bank_manager"]:
    nav_items.append(("recommend", "Product Recommendation", "AI-powered product suggestions", "pages/15_Product_Recommendation.py"))
if role in ["admin", "bank_manager"]:
    nav_items.append(("smart_toy", "AI Business Insights", "AI-generated analytical insights", "pages/18_AI_Business_Insights.py"))
if role in ["admin", "bank_manager", "data_analyst"]:
    nav_items.append(("description", "Reports", "Generate and export professional reports", "pages/19_Reports.py"))

# Marketplace nav cards
if role in ["admin"]:
    nav_items.append(("storefront", "Vendor Management", "Manage vendor approvals and commissions", "pages/22_Vendor_Management.py"))
if role in ["admin", "vendor"]:
    nav_items.append(("inventory_2", "Product Catalog", "Manage product listings and inventory", "pages/23_Product_Catalog.py"))
if role in ["admin", "customer", "vendor", "guest"]:
    nav_items.append(("shopping_bag", "Shop", "Browse and buy products from the marketplace", "pages/25_Shop.py"))
if role in ["customer"]:
    nav_items.append(("shopping_cart", "Cart & Checkout", "View cart and complete your purchase", "pages/26_Cart_Checkout.py"))
    nav_items.append(("receipt_long", "My Orders", "Track your orders and download invoices", "pages/28_My_Orders.py"))
if role in ["vendor"]:
    nav_items.append(("space_dashboard", "Vendor Dashboard", "View your sales and performance", "pages/35_Vendor_Dashboard.py"))

cols = st.columns(3)
for idx, (icon_name, title, desc, path) in enumerate(nav_items):
    border_color = 'var(--secondary)' if idx % 3 == 0 else 'var(--accent)' if idx % 3 == 1 else 'var(--success)'
    with cols[idx % 3]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {border_color}; margin-bottom: 8px;">
            <div style="margin-bottom: 0.4rem;">{render_html_icon(icon_name, size="2rem", color=border_color)}</div>
            <div style="font-weight: 700; color: var(--primary); margin: 0.3rem 0; font-size: 1.05rem;">{title}</div>
            <div style="color: var(--text-muted); font-size: 0.85rem; line-height: 1.3; min-height: 38px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Go to {title}", key=f"nav_{idx}", use_container_width=True, type="secondary"):
            st.switch_page(path)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #A0AEC0; font-size: 0.8rem; padding: 1rem 0;">
    AI Banking Customer Insights Platform v1.0 · Powered by Streamlit & Machine Learning
</div>
""", unsafe_allow_html=True)
