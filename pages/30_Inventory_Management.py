"""
Inventory Management — Vendor/Admin page for managing stock levels,
low-stock alerts, and restocking.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from utils.marketplace import (
    get_inventory_for_vendor, get_vendor_by_user_id,
    update_inventory, get_all_products,
)
from database import get_connection
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — Inventory", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Inventory Management")

role = user["role"]
vendor_id = None
if role == "vendor":
    vendor = get_vendor_by_user_id(user["user_id"])
    if vendor:
        vendor_id = vendor["vendor_id"]

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("warehouse", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Inventory Management</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# Load inventory
if role == "admin":
    # Admin sees all — get all vendors' inventory
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, p.name as product_name, p.sku, p.vendor_id,
               v.business_name as vendor_name, w.name as warehouse_name
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN vendors v ON p.vendor_id = v.vendor_id
        JOIN warehouses w ON i.warehouse_id = w.warehouse_id
        ORDER BY p.name
    """)
    inventory = [dict(r) for r in cursor.fetchall()]
    conn.close()
else:
    inventory = get_inventory_for_vendor(vendor_id) if vendor_id else []

# KPIs
total_items = len(inventory)
total_stock = sum(i["quantity"] for i in inventory)
low_stock = [i for i in inventory if i["quantity"] <= i["reorder_level"]]

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f'<div class="kpi-card blue animate-in"><div class="kpi-value">{total_items}</div><div class="kpi-label">Products in Inventory</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card green animate-in"><div class="kpi-value">{total_stock:,}</div><div class="kpi-label">Total Stock Units</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card" style="border-left-color:#DC3545;"><div class="kpi-value">{len(low_stock)}</div><div class="kpi-label">Low Stock Alerts</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Low stock alerts
if low_stock:
    st.markdown(f'<div class="section-header">{render_html_icon("warning", size="18px", color="#DC3545")} Low Stock Alerts</div>', unsafe_allow_html=True)
    for item in low_stock:
        st.warning(f"**{item['product_name']}** ({item.get('sku', 'N/A')}) — Only **{item['quantity']}** units left (reorder at {item['reorder_level']})", icon=":material/warning:")

# Inventory table
if inventory:
    st.markdown(f'<div class="section-header">{render_html_icon("table_chart", size="18px")} Stock Levels</div>', unsafe_allow_html=True)
    df = pd.DataFrame(inventory)
    display_cols = ["product_name", "sku", "warehouse_name", "quantity", "reserved", "reorder_level", "last_restocked"]
    if role == "admin":
        display_cols.insert(0, "vendor_name")
    display_cols = [c for c in display_cols if c in df.columns]
    df_show = df[display_cols].copy()
    df_show.columns = [c.replace("_", " ").title() for c in display_cols]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # Update stock
    st.markdown("---")
    st.markdown(f'<div class="section-header">{render_html_icon("edit", size="18px")} Update Stock</div>', unsafe_allow_html=True)

    sel = st.selectbox("Select Product", [f"{i['product_name']} ({i['warehouse_name']})" for i in inventory], key="inv_select")
    if sel:
        idx = [f"{i['product_name']} ({i['warehouse_name']})" for i in inventory].index(sel)
        item = inventory[idx]
        with st.form("update_stock_form"):
            uc1, uc2, uc3 = st.columns(3)
            with uc1:
                new_qty = st.number_input("Quantity", min_value=0, value=item["quantity"], key="inv_qty")
            with uc2:
                new_res = st.number_input("Reserved", min_value=0, value=item["reserved"], key="inv_res")
            with uc3:
                new_reorder = st.number_input("Reorder Level", min_value=0, value=item["reorder_level"], key="inv_reorder")
            if st.form_submit_button("Update", type="primary", use_container_width=True):
                update_inventory(item["product_id"], item["warehouse_id"], new_qty, new_res, new_reorder)
                st.success("Stock updated!", icon=":material/check:")
                st.rerun()
else:
    st.info("No inventory records found.", icon=":material/info:")
