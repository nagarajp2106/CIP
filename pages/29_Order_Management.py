"""
Order Management — Admin/Vendor page for processing orders.
Status pipeline, filters, and bulk status updates.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from utils.orders import get_all_orders, get_order_details, update_order_status, cancel_order
from utils.marketplace import get_vendor_by_user_id
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON, ORDER_STATUSES

st.set_page_config(page_title=f"{APP_NAME} — Order Management", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Order Management")

role = user["role"]
vendor_id = None
if role == "vendor":
    vendor = get_vendor_by_user_id(user["user_id"])
    if vendor:
        vendor_id = vendor["vendor_id"]

# ──────────────────────────────────────────────
# Page Header
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("list_alt", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Order Management</h1>
</div>
<p style="color:#6C757D;margin-top:-0.5rem;">Process and manage marketplace orders.</p>
""", unsafe_allow_html=True)

st.markdown("---")

# Filters
f1, f2, _ = st.columns([2, 2, 6])
with f1:
    status_filter = st.selectbox("Status", ["All"] + ORDER_STATUSES, key="order_status_filter")
with f2:
    search_order = st.text_input("Order ID", placeholder="ORD000001...", key="order_search")

status_val = None if status_filter == "All" else status_filter
orders = get_all_orders(status=status_val, vendor_id=vendor_id)

if search_order:
    orders = [o for o in orders if search_order.lower() in o["order_id"].lower()]

# KPI Cards
all_orders = get_all_orders(vendor_id=vendor_id)
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class="kpi-card blue animate-in">
        <div class="kpi-value">{len(all_orders)}</div>
        <div class="kpi-label">Total Orders</div>
    </div>""", unsafe_allow_html=True)
with k2:
    pending = sum(1 for o in all_orders if o["status"] in ("Placed", "Confirmed", "Processing"))
    st.markdown(f"""
    <div class="kpi-card gold animate-in">
        <div class="kpi-value">{pending}</div>
        <div class="kpi-label">Pending</div>
    </div>""", unsafe_allow_html=True)
with k3:
    delivered = sum(1 for o in all_orders if o["status"] == "Delivered")
    st.markdown(f"""
    <div class="kpi-card green animate-in">
        <div class="kpi-value">{delivered}</div>
        <div class="kpi-label">Delivered</div>
    </div>""", unsafe_allow_html=True)
with k4:
    total_gmv = sum(o["net_amount"] for o in all_orders)
    st.markdown(f"""
    <div class="kpi-card teal animate-in">
        <div class="kpi-value">\u20b9{total_gmv:,.0f}</div>
        <div class="kpi-label">Total Revenue</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# Orders Table
if not orders:
    st.info("No orders found.", icon=":material/info:")
else:
    st.markdown(f'<div class="section-header">{render_html_icon("list_alt", size="18px")} Orders ({len(orders)})</div>', unsafe_allow_html=True)

    df = pd.DataFrame(orders)
    cols = ["order_id", "customer_id", "net_amount", "status", "placed_at"]
    cols = [c for c in cols if c in df.columns]
    df_show = df[cols].copy()
    df_show.columns = [c.replace("_", " ").title() for c in cols]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Update Order Status
    st.markdown(f'<div class="section-header">{render_html_icon("update", size="18px")} Update Order Status</div>', unsafe_allow_html=True)

    selected_order = st.selectbox(
        "Select Order",
        [f"{o['order_id']} — {o['status']} — \u20b9{o['net_amount']:,.2f}" for o in orders],
        key="update_order_select",
    )

    if selected_order:
        oid = selected_order.split(" — ")[0]
        details = get_order_details(oid)

        if details:
            # Show items
            if details.get("items"):
                items_data = [{
                    "Product": i.get("product_name", i["product_id"]),
                    "Vendor": i.get("vendor_name", ""),
                    "Qty": i["quantity"],
                    "Total": f"\u20b9{i['total_price']:,.2f}",
                    "Status": i["status"],
                } for i in details["items"]]
                st.dataframe(pd.DataFrame(items_data), use_container_width=True, hide_index=True)

            u1, u2 = st.columns(2)
            with u1:
                current_idx = ORDER_STATUSES.index(details["status"]) if details["status"] in ORDER_STATUSES else 0
                new_status = st.selectbox("New Status", ORDER_STATUSES, index=current_idx, key="new_order_status")
            with u2:
                st.markdown(f"**Current:** {details['status']}")
                st.markdown(f"**Placed:** {details['placed_at']}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Update Status", type="primary", key="btn_update_order", use_container_width=True):
                    update_order_status(oid, new_status)
                    st.success(f"Order {oid} updated to **{new_status}**!", icon=":material/check:")
                    st.rerun()
            with c2:
                if details["status"] not in ("Cancelled", "Delivered", "Returned"):
                    if st.button("Cancel Order", type="secondary", key="btn_cancel_order", use_container_width=True):
                        cancel_order(oid)
                        st.warning(f"Order {oid} cancelled.", icon=":material/cancel:")
                        st.rerun()
