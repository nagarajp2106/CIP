"""
Marketplace Reports — Admin page to export marketplace data as reports.
"""
import streamlit as st
import pandas as pd
import io
from authentication import check_auth, require_role
from database import get_connection
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — Marketplace Reports", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Marketplace Reports")

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("summarize", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Marketplace Reports</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

conn = get_connection()

# Report selector
report_type = st.selectbox("Select Report", [
    "Vendor Summary",
    "Product Inventory",
    "Order History",
    "Commission Summary",
    "Category Performance",
])

st.markdown("---")

df = pd.DataFrame()

if report_type == "Vendor Summary":
    df = pd.read_sql("""
        SELECT v.vendor_id, v.business_name, v.owner_name, v.email, v.phone,
               v.city, v.state, v.commission_rate, v.status,
               COUNT(DISTINCT p.product_id) as products,
               COALESCE(SUM(oi.total_price), 0) as total_sales
        FROM vendors v
        LEFT JOIN products p ON v.vendor_id = p.vendor_id
        LEFT JOIN order_items oi ON v.vendor_id = oi.vendor_id
        GROUP BY v.vendor_id
        ORDER BY total_sales DESC
    """, conn)

elif report_type == "Product Inventory":
    df = pd.read_sql("""
        SELECT p.product_id, p.name, p.price, p.mrp, p.discount_pct, p.status,
               p.rating_avg, v.business_name as vendor,
               c.name as category,
               COALESCE(i.quantity, 0) as stock,
               COALESCE(i.reserved, 0) as reserved
        FROM products p
        JOIN vendors v ON p.vendor_id = v.vendor_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        LEFT JOIN inventory i ON p.product_id = i.product_id
        ORDER BY p.name
    """, conn)

elif report_type == "Order History":
    df = pd.read_sql("""
        SELECT o.order_id, o.customer_id, o.total_amount, o.tax_amount,
               o.shipping_amount, o.net_amount, o.status, o.placed_at,
               o.shipping_city, o.shipping_state,
               COUNT(oi.id) as items
        FROM orders o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        GROUP BY o.order_id
        ORDER BY o.placed_at DESC
    """, conn)

elif report_type == "Commission Summary":
    df = pd.read_sql("""
        SELECT v.business_name, v.commission_rate,
               COUNT(cl.id) as transactions,
               COALESCE(SUM(cl.order_amount), 0) as order_total,
               COALESCE(SUM(cl.commission_amount), 0) as commission_total
        FROM vendors v
        LEFT JOIN commission_ledger cl ON v.vendor_id = cl.vendor_id
        GROUP BY v.vendor_id
        ORDER BY commission_total DESC
    """, conn)

elif report_type == "Category Performance":
    df = pd.read_sql("""
        SELECT c.name as category, c.category_id,
               COUNT(DISTINCT p.product_id) as products,
               COALESCE(SUM(oi.total_price), 0) as revenue,
               COALESCE(SUM(oi.quantity), 0) as units_sold
        FROM categories c
        LEFT JOIN products p ON c.category_id = p.category_id
        LEFT JOIN order_items oi ON p.product_id = oi.product_id
        GROUP BY c.category_id
        ORDER BY revenue DESC
    """, conn)

conn.close()

# Display & Export
if not df.empty:
    st.markdown(f'<div class="section-header">{render_html_icon("table_chart", size="18px")} {report_type} ({len(df)} rows)</div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export buttons
    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv, f"{report_type.lower().replace(' ', '_')}.csv",
            "text/csv", use_container_width=True,
        )
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Report")
        st.download_button(
            "Download Excel",
            buffer.getvalue(),
            f"{report_type.lower().replace(' ', '_')}.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
else:
    st.info(f"No data available for {report_type}.", icon=":material/info:")
