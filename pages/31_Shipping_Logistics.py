"""
Shipping & Logistics — Shipment management for Admin/Vendor.
"""
import streamlit as st
import pandas as pd
import datetime
from authentication import check_auth, require_role
from database import get_connection
from utils.marketplace import get_vendor_by_user_id
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON, SHIPMENT_STATUSES

st.set_page_config(page_title=f"{APP_NAME} — Shipping", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Shipping & Logistics")

role = user["role"]
vendor_id = None
if role == "vendor":
    vendor = get_vendor_by_user_id(user["user_id"])
    if vendor:
        vendor_id = vendor["vendor_id"]

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("local_shipping", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Shipping & Logistics</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# Load shipments
conn = get_connection()
cursor = conn.cursor()
if vendor_id:
    cursor.execute("""
        SELECT DISTINCT s.*, o.customer_id, o.net_amount
        FROM shipments s
        JOIN orders o ON s.order_id = o.order_id
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE oi.vendor_id = ?
        ORDER BY s.created_at DESC
    """, (vendor_id,))
else:
    cursor.execute("""
        SELECT s.*, o.customer_id, o.net_amount
        FROM shipments s
        JOIN orders o ON s.order_id = o.order_id
        ORDER BY s.created_at DESC
    """)
shipments = [dict(r) for r in cursor.fetchall()]

# Get confirmed orders without shipments (for creating new shipments)
if vendor_id:
    cursor.execute("""
        SELECT DISTINCT o.order_id, o.customer_id, o.net_amount
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        LEFT JOIN shipments s ON o.order_id = s.order_id
        WHERE oi.vendor_id = ? AND o.status IN ('Confirmed', 'Processing') AND s.shipment_id IS NULL
    """, (vendor_id,))
else:
    cursor.execute("""
        SELECT o.order_id, o.customer_id, o.net_amount
        FROM orders o
        LEFT JOIN shipments s ON o.order_id = s.order_id
        WHERE o.status IN ('Confirmed', 'Processing') AND s.shipment_id IS NULL
    """)
unshipped = [dict(r) for r in cursor.fetchall()]
conn.close()

# KPIs
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f'<div class="kpi-card blue animate-in"><div class="kpi-value">{len(shipments)}</div><div class="kpi-label">Total Shipments</div></div>', unsafe_allow_html=True)
with k2:
    in_transit = sum(1 for s in shipments if s["status"] in ("Shipped", "In Transit"))
    st.markdown(f'<div class="kpi-card gold animate-in"><div class="kpi-value">{in_transit}</div><div class="kpi-label">In Transit</div></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card green animate-in"><div class="kpi-value">{len(unshipped)}</div><div class="kpi-label">Awaiting Shipment</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Create Shipment
if unshipped:
    st.markdown(f'<div class="section-header">{render_html_icon("add_circle", size="18px")} Create Shipment</div>', unsafe_allow_html=True)
    with st.form("create_shipment"):
        sel = st.selectbox("Order", [f"{o['order_id']} — \u20b9{o['net_amount']:,.2f}" for o in unshipped])
        c1, c2 = st.columns(2)
        with c1:
            carrier = st.text_input("Carrier", value="BlueDart", key="ship_carrier")
            tracking = st.text_input("Tracking Number", key="ship_tracking")
        with c2:
            est_delivery = st.date_input("Est. Delivery", value=datetime.date.today() + datetime.timedelta(days=5), key="ship_est")

        if st.form_submit_button("Create Shipment", type="primary", use_container_width=True):
            oid = sel.split(" — ")[0]
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM shipments")
            cnt = c.fetchone()[0]
            sid = f"SHP{cnt+1:06d}"
            now = datetime.datetime.now().isoformat(timespec="seconds")
            c.execute("""
                INSERT INTO shipments (shipment_id, order_id, carrier, tracking_number, status, estimated_delivery, shipped_at, created_at)
                VALUES (?, ?, ?, ?, 'Packed', ?, ?, ?)
            """, (sid, oid, carrier, tracking, est_delivery.isoformat(), now, now))
            c.execute("UPDATE orders SET status = 'Shipped', updated_at = ? WHERE order_id = ?", (now, oid))
            conn.commit()
            conn.close()
            st.success(f"Shipment {sid} created for order {oid}!", icon=":material/check:")
            st.rerun()

st.markdown("---")

# Shipments Table
if shipments:
    st.markdown(f'<div class="section-header">{render_html_icon("list_alt", size="18px")} Shipments</div>', unsafe_allow_html=True)
    df = pd.DataFrame(shipments)
    cols = ["shipment_id", "order_id", "carrier", "tracking_number", "status", "estimated_delivery", "shipped_at"]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

    # Update shipment status
    st.markdown(f'<div class="section-header">{render_html_icon("update", size="18px")} Update Status</div>', unsafe_allow_html=True)
    sel_ship = st.selectbox("Select Shipment", [f"{s['shipment_id']} — {s['order_id']} — {s['status']}" for s in shipments], key="update_ship")
    if sel_ship:
        sid = sel_ship.split(" — ")[0]
        current = next((s for s in shipments if s["shipment_id"] == sid), None)
        if current:
            new_stat = st.selectbox("New Status", SHIPMENT_STATUSES,
                                    index=SHIPMENT_STATUSES.index(current["status"]) if current["status"] in SHIPMENT_STATUSES else 0,
                                    key="new_ship_status")
            if st.button("Update", type="primary", key="btn_update_ship"):
                conn = get_connection()
                c = conn.cursor()
                now = datetime.datetime.now().isoformat(timespec="seconds")
                c.execute("UPDATE shipments SET status = ? WHERE shipment_id = ?", (new_stat, sid))
                if new_stat == "Delivered":
                    c.execute("UPDATE shipments SET delivered_at = ? WHERE shipment_id = ?", (now, sid))
                    c.execute("UPDATE orders SET status = 'Delivered', updated_at = ? WHERE order_id = ?", (now, current["order_id"]))
                conn.commit()
                conn.close()
                st.success(f"Shipment {sid} updated to {new_stat}!", icon=":material/check:")
                st.rerun()
else:
    st.info("No shipments yet.", icon=":material/info:")
