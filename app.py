"""
AI-Powered Retail Banking Customer Insights Platform
Main Streamlit Application Entry Point
"""
import streamlit as st
import os
from config import APP_NAME, APP_ICON, ASSETS_DIR, ROLES
from database import init_db, seed_demo_data
from authentication import login_page, check_auth, logout, get_role_badge_html, render_sidebar

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
    return True

setup_database()

# ──────────────────────────────────────────────
# Authentication Gate
# ──────────────────────────────────────────────
user = check_auth()

if not user:
    login_page()
    st.stop()

# ──────────────────────────────────────────────
# Sidebar — Authenticated User
# ──────────────────────────────────────────────
render_sidebar()

# ──────────────────────────────────────────────
# Main Content — Welcome Page
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="color: #1B2A4A; font-size: 2.2rem;">Welcome, {user['full_name']}! 👋</h1>
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
        <div class="kpi-icon">👥</div>
        <div class="kpi-value">{count:,}</div>
        <div class="kpi-label">Total Customers</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    count = pd.read_sql("SELECT COUNT(*) as c FROM accounts", conn).iloc[0]["c"]
    st.markdown(f"""
    <div class="kpi-card gold animate-in">
        <div class="kpi-icon">🏧</div>
        <div class="kpi-value">{count:,}</div>
        <div class="kpi-label">Total Accounts</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    count = pd.read_sql("SELECT COUNT(*) as c FROM transactions", conn).iloc[0]["c"]
    st.markdown(f"""
    <div class="kpi-card green animate-in">
        <div class="kpi-icon">💳</div>
        <div class="kpi-value">{count:,}</div>
        <div class="kpi-label">Total Transactions</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    count = pd.read_sql("SELECT COUNT(*) as c FROM loans", conn).iloc[0]["c"]
    st.markdown(f"""
    <div class="kpi-card teal animate-in">
        <div class="kpi-icon">💰</div>
        <div class="kpi-value">{count:,}</div>
        <div class="kpi-label">Total Loans</div>
    </div>
    """, unsafe_allow_html=True)

conn.close()

st.markdown("---")

# Navigation cards for quick access
st.markdown('<div class="section-header">📌 Quick Navigation</div>', unsafe_allow_html=True)

role = user["role"]
nav_items = []

if role in ["admin", "bank_manager", "relationship_manager", "loan_officer", "data_analyst", "auditor"]:
    nav_items.append(("📊", "Dashboard", "View KPIs, charts, and executive summary"))
if role in ["admin", "data_analyst"]:
    nav_items.append(("📤", "Data Upload", "Upload and validate banking datasets"))
if role in ["admin", "bank_manager", "relationship_manager"]:
    nav_items.append(("👤", "Customer Management", "Search, view, and manage customers"))
if role in ["admin", "bank_manager", "loan_officer"]:
    nav_items.append(("🏦", "Loan Analytics", "Loan portfolio analysis and metrics"))
if role in ["admin", "bank_manager", "relationship_manager"]:
    nav_items.append(("🔮", "Churn Prediction", "Predict customer churn probability"))
if role in ["admin", "bank_manager", "loan_officer"]:
    nav_items.append(("⚡", "Credit Risk", "Assess customer credit risk"))
if role in ["admin", "bank_manager", "auditor"]:
    nav_items.append(("🛡️", "Fraud Detection", "Detect suspicious transactions"))
if role in ["admin", "bank_manager"]:
    nav_items.append(("📈", "AI Business Insights", "AI-generated analytical insights"))
if role in ["admin", "bank_manager", "auditor"]:
    nav_items.append(("📑", "Reports", "Generate and export professional reports"))

cols = st.columns(3)
for idx, (icon, title, desc) in enumerate(nav_items):
    with cols[idx % 3]:
        st.markdown(f"""
        <div class="kpi-card" style="cursor: pointer; border-left-color: {'#2E86AB' if idx % 3 == 0 else '#D4AF37' if idx % 3 == 1 else '#28A745'};">
            <div style="font-size: 1.8rem;">{icon}</div>
            <div style="font-weight: 700; color: #1B2A4A; margin: 0.3rem 0;">{title}</div>
            <div style="color: #6C757D; font-size: 0.85rem;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #A0AEC0; font-size: 0.8rem; padding: 1rem 0;">
    AI Banking Customer Insights Platform v1.0 · Powered by Streamlit & Machine Learning
</div>
""", unsafe_allow_html=True)
