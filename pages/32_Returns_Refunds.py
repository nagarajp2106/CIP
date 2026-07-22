"""
Returns & Refunds — Manage return requests and process refunds.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.payments import initiate_refund, approve_refund
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — Returns & Refunds", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Returns & Refunds")

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("assignment_return", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Returns & Refunds</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

role = user["role"]

# Load refunds
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT r.*, o.customer_id, o.net_amount as order_total, p.method as payment_method
    FROM refunds r
    JOIN orders o ON r.order_id = o.order_id
    JOIN payments p ON r.payment_id = p.payment_id
    ORDER BY r.created_at DESC
""")
refunds = [dict(r) for r in cursor.fetchall()]
conn.close()

# KPIs
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f'<div class="kpi-card blue animate-in"><div class="kpi-value">{len(refunds)}</div><div class="kpi-label">Total Refunds</div></div>', unsafe_allow_html=True)
with k2:
    pending = sum(1 for r in refunds if r["status"] == "Requested")
    st.markdown(f'<div class="kpi-card gold animate-in"><div class="kpi-value">{pending}</div><div class="kpi-label">Pending Approval</div></div>', unsafe_allow_html=True)
with k3:
    total_refunded = sum(r["amount"] for r in refunds if r["status"] == "Approved")
    st.markdown(f'<div class="kpi-card green animate-in"><div class="kpi-value">\u20b9{total_refunded:,.0f}</div><div class="kpi-label">Total Refunded</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Initiate refund (customer or admin)
if role in ("customer", "admin"):
    st.markdown(f'<div class="section-header">{render_html_icon("add_circle", size="18px")} Request Refund</div>', unsafe_allow_html=True)

    conn = get_connection()
    cursor = conn.cursor()
    if role == "customer":
        cursor.execute("SELECT order_id, net_amount, status FROM orders WHERE customer_id = 'CUST00001' AND status = 'Delivered'")
    else:
        cursor.execute("SELECT order_id, net_amount, status FROM orders WHERE status = 'Delivered'")
    eligible_orders = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if eligible_orders:
        with st.form("refund_form"):
            sel = st.selectbox("Order", [f"{o['order_id']} — \u20b9{o['net_amount']:,.2f}" for o in eligible_orders])
            reason = st.text_area("Reason for refund", height=80)
            if st.form_submit_button("Submit Refund Request", type="primary", use_container_width=True):
                oid = sel.split(" — ")[0]
                rid = initiate_refund(oid, reason=reason or "No reason provided")
                if rid:
                    st.success(f"Refund request {rid} submitted!", icon=":material/check:")
                    st.rerun()
                else:
                    st.error("Could not initiate refund. Check if payment exists.", icon=":material/error:")
    else:
        st.caption("No delivered orders eligible for refund.")

st.markdown("---")

# Refunds Table
if refunds:
    st.markdown(f'<div class="section-header">{render_html_icon("list_alt", size="18px")} Refund Requests</div>', unsafe_allow_html=True)
    df = pd.DataFrame(refunds)
    cols = ["refund_id", "order_id", "amount", "reason", "status", "created_at"]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

    # Admin approve/reject
    if role in ("admin", "vendor"):
        pending_refunds = [r for r in refunds if r["status"] == "Requested"]
        if pending_refunds:
            st.markdown(f'<div class="section-header">{render_html_icon("approval", size="18px")} Approve Refunds</div>', unsafe_allow_html=True)
            for ref in pending_refunds:
                with st.container():
                    st.markdown(f"**{ref['refund_id']}** — Order {ref['order_id']} — \u20b9{ref['amount']:,.2f}")
                    st.caption(f"Reason: {ref.get('reason', 'N/A')}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Approve", key=f"approve_{ref['refund_id']}", type="primary"):
                            approve_refund(ref["refund_id"])
                            st.success(f"Refund {ref['refund_id']} approved!", icon=":material/check:")
                            st.rerun()
                    with c2:
                        if st.button("Reject", key=f"reject_{ref['refund_id']}"):
                            conn = get_connection()
                            conn.cursor().execute("UPDATE refunds SET status = 'Rejected' WHERE refund_id = ?", (ref["refund_id"],))
                            conn.commit()
                            conn.close()
                            st.warning("Refund rejected.", icon=":material/warning:")
                            st.rerun()
else:
    st.info("No refund requests.", icon=":material/info:")
