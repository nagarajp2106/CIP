"""
My Orders — Customer order history with detail expansion,
cancel order, and order status tracking.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from utils.orders import get_customer_orders, get_order_details, cancel_order
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — My Orders", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("My Orders")

CUSTOMER_ID = "CUST00001"

# ──────────────────────────────────────────────
# Page Header
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("receipt_long", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">My Orders</h1>
</div>
<p style="color:#6C757D;margin-top:-0.5rem;">Track your orders and view order history.</p>
""", unsafe_allow_html=True)

st.markdown("---")

orders = get_customer_orders(CUSTOMER_ID)

if not orders:
    st.markdown(f"""
    <div style="text-align:center;padding:3rem;background:#F8F9FA;border-radius:12px;border:2px dashed #E2E8F0;">
        {render_html_icon("receipt_long", size="4rem", color="#A0AEC0")}
        <h3 style="color:#6C757D;margin-top:1rem;">No orders yet</h3>
        <p style="color:#A0AEC0;">Start shopping to see your orders here.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Browse Shop", type="primary"):
        st.switch_page("pages/25_Shop.py")
    st.stop()

# Status badge colors
STATUS_COLORS = {
    "Placed": "#FFC107", "Confirmed": "#2E86AB", "Processing": "#6F42C1",
    "Shipped": "#17A2B8", "In Transit": "#6C757D", "Delivered": "#28A745",
    "Cancelled": "#DC3545", "Returned": "#FF8C00",
}

for order in orders:
    color = STATUS_COLORS.get(order["status"], "#6C757D")
    with st.expander(f"Order {order['order_id']} — \u20b9{order['net_amount']:,.2f} — {order['status']}", expanded=False):
        # Order header
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
            <div>
                <span style="color:#6C757D;font-size:0.85rem;">Placed on {order['placed_at']}</span>
            </div>
            <span style="background:{color};color:white;padding:4px 12px;border-radius:16px;font-size:0.8rem;font-weight:600;">{order['status']}</span>
        </div>
        """, unsafe_allow_html=True)

        # Get full details
        details = get_order_details(order["order_id"])
        if details and details.get("items"):
            # Items table
            items_data = []
            for item in details["items"]:
                items_data.append({
                    "Product": item.get("product_name", item["product_id"]),
                    "Vendor": item.get("vendor_name", item["vendor_id"]),
                    "Qty": item["quantity"],
                    "Price": f"\u20b9{item['unit_price']:,.2f}",
                    "Total": f"\u20b9{item['total_price']:,.2f}",
                })
            st.dataframe(pd.DataFrame(items_data), use_container_width=True, hide_index=True)

        # Summary
        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown(f"**Subtotal:** \u20b9{order['total_amount']:,.2f}")
            st.markdown(f"**Tax:** \u20b9{order['tax_amount']:,.2f}")
        with s2:
            st.markdown(f"**Shipping:** \u20b9{order['shipping_amount']:,.2f}")
            st.markdown(f"**Total:** \u20b9{order['net_amount']:,.2f}")
        with s3:
            if details and details.get("payment"):
                pay = details["payment"]
                st.markdown(f"**Payment:** {pay['method']} — {pay['status']}")
                if pay.get("transaction_ref"):
                    st.markdown(f"**Ref:** `{pay['transaction_ref']}`")

        # Shipping info
        if details and details.get("shipment"):
            ship = details["shipment"]
            st.markdown(f"**Carrier:** {ship.get('carrier', 'N/A')} | **Tracking:** {ship.get('tracking_number', 'N/A')} | **Status:** {ship.get('status', 'N/A')}")

        # Cancel button (only if Placed or Confirmed)
        if order["status"] in ("Placed", "Confirmed"):
            if st.button(f"Cancel Order {order['order_id']}", key=f"cancel_{order['order_id']}", type="secondary"):
                cancel_order(order["order_id"])
                st.warning(f"Order {order['order_id']} has been cancelled.", icon=":material/cancel:")
                st.rerun()
