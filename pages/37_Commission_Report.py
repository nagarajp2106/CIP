"""
Commission Report — Track and manage vendor commissions.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from authentication import check_auth, require_role
from database import get_connection
from utils.marketplace import get_vendor_by_user_id
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON, CHART_COLORS

st.set_page_config(page_title=f"{APP_NAME} — Commission Report", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Commission Report")

role = user["role"]
vendor_id = None
if role == "vendor":
    vendor = get_vendor_by_user_id(user["user_id"])
    if vendor:
        vendor_id = vendor["vendor_id"]

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("payments", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Commission Report</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

conn = get_connection()

if vendor_id:
    df = pd.read_sql(f"SELECT * FROM commission_ledger WHERE vendor_id = '{vendor_id}' ORDER BY created_at DESC", conn)
else:
    df = pd.read_sql("SELECT cl.*, v.business_name FROM commission_ledger cl JOIN vendors v ON cl.vendor_id = v.vendor_id ORDER BY cl.created_at DESC", conn)

# KPIs
total_comm = df["commission_amount"].sum() if not df.empty else 0
pending_comm = df[df["status"] == "Pending"]["commission_amount"].sum() if not df.empty else 0
entries = len(df)

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f'<div class="kpi-card blue animate-in"><div class="kpi-value">\u20b9{total_comm:,.0f}</div><div class="kpi-label">Total Commission</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card gold animate-in"><div class="kpi-value">\u20b9{pending_comm:,.0f}</div><div class="kpi-label">Pending Payout</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card green animate-in"><div class="kpi-value">{entries}</div><div class="kpi-label">Total Entries</div></div>', unsafe_allow_html=True)

st.markdown("---")

if not df.empty:
    # Commission by vendor (admin view)
    if role == "admin":
        df_vendor = df.groupby("business_name").agg(
            total=("commission_amount", "sum"),
            count=("id", "count")
        ).reset_index().sort_values("total", ascending=False)

        fig = px.bar(df_vendor, x="business_name", y="total", title="Commission by Vendor",
                     text="count", color_discrete_sequence=CHART_COLORS)
        fig.update_layout(template="plotly_white", height=400)
        st.plotly_chart(fig, use_container_width=True)

    # Ledger table
    st.markdown(f'<div class="section-header">{render_html_icon("table_chart", size="18px")} Commission Ledger</div>', unsafe_allow_html=True)
    cols = ["order_id", "order_amount", "commission_rate", "commission_amount", "status", "created_at"]
    if "business_name" in df.columns:
        cols.insert(0, "business_name")
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)
else:
    st.info("No commission records yet.", icon=":material/info:")

conn.close()
