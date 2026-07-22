"""
Vendor Management — Admin page for managing vendor registrations,
approvals, commission rates, and profiles.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from utils.marketplace import (
    get_all_vendors, get_vendor_by_id, update_vendor_status,
    update_vendor_commission, update_vendor_profile,
)
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — Vendor Management", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Vendor Management")

# ──────────────────────────────────────────────
# Page Header
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("storefront", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Vendor Management</h1>
</div>
<p style="color:#6C757D;margin-top:-0.5rem;">Approve, suspend, and manage marketplace vendors.</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Filters
# ──────────────────────────────────────────────
col_filter1, col_filter2, _ = st.columns([2, 2, 6])

with col_filter1:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Active", "Pending", "Suspended"],
        key="vendor_status_filter",
    )

with col_filter2:
    search_text = st.text_input("Search Vendor", placeholder="Name, email...", key="vendor_search")

# Load data
filter_val = None if status_filter == "All" else status_filter
vendors = get_all_vendors(status_filter=filter_val)

if search_text:
    search_lower = search_text.lower()
    vendors = [v for v in vendors if
               search_lower in v["business_name"].lower() or
               search_lower in (v["email"] or "").lower() or
               search_lower in (v["owner_name"] or "").lower()]

# ──────────────────────────────────────────────
# KPI Cards
# ──────────────────────────────────────────────
all_vendors = get_all_vendors()
active = sum(1 for v in all_vendors if v["status"] == "Active")
pending = sum(1 for v in all_vendors if v["status"] == "Pending")
suspended = sum(1 for v in all_vendors if v["status"] == "Suspended")

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class="kpi-card blue animate-in">
        <div class="kpi-icon" style="color:var(--secondary);">{render_html_icon("storefront", size="2.5rem")}</div>
        <div class="kpi-value">{len(all_vendors)}</div>
        <div class="kpi-label">Total Vendors</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card green animate-in">
        <div class="kpi-icon" style="color:var(--success);">{render_html_icon("check_circle", size="2.5rem")}</div>
        <div class="kpi-value">{active}</div>
        <div class="kpi-label">Active</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class="kpi-card gold animate-in">
        <div class="kpi-icon" style="color:var(--accent);">{render_html_icon("hourglass_top", size="2.5rem")}</div>
        <div class="kpi-value">{pending}</div>
        <div class="kpi-label">Pending Approval</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:#DC3545;">
        <div class="kpi-icon" style="color:#DC3545;">{render_html_icon("block", size="2.5rem")}</div>
        <div class="kpi-value">{suspended}</div>
        <div class="kpi-label">Suspended</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Vendor Table
# ──────────────────────────────────────────────
if not vendors:
    st.info("No vendors found matching your filters.", icon=":material/info:")
else:
    st.markdown(f'<div class="section-header">{render_html_icon("list", size="20px")} Vendor List ({len(vendors)} records)</div>', unsafe_allow_html=True)

    # Display as dataframe
    df = pd.DataFrame(vendors)
    display_cols = ["vendor_id", "business_name", "owner_name", "email", "phone",
                    "city", "state", "commission_rate", "status"]
    display_cols = [c for c in display_cols if c in df.columns]
    df_display = df[display_cols].copy()
    df_display.columns = [c.replace("_", " ").title() for c in display_cols]

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ──────────────────────────────────────────────
    # Bulk Actions
    # ──────────────────────────────────────────────
    st.markdown(f'<div class="section-header">{render_html_icon("bolt", size="20px")} Quick Actions</div>', unsafe_allow_html=True)

    action_col1, action_col2 = st.columns(2)

    with action_col1:
        st.markdown("**Approve Pending Vendors**")
        pending_vendors = [v for v in vendors if v["status"] == "Pending"]
        if pending_vendors:
            selected_pending = st.multiselect(
                "Select vendors to approve",
                options=[f"{v['vendor_id']} — {v['business_name']}" for v in pending_vendors],
                key="approve_select",
            )
            if st.button("Approve Selected", type="primary", key="btn_approve"):
                for sel in selected_pending:
                    vid = sel.split(" — ")[0]
                    update_vendor_status(vid, "Active")
                st.success(f"Approved {len(selected_pending)} vendor(s)!", icon=":material/check:")
                st.rerun()
        else:
            st.caption("No pending vendors.")

    with action_col2:
        st.markdown("**Suspend Vendors**")
        active_vendors = [v for v in vendors if v["status"] == "Active"]
        if active_vendors:
            selected_suspend = st.multiselect(
                "Select vendors to suspend",
                options=[f"{v['vendor_id']} — {v['business_name']}" for v in active_vendors],
                key="suspend_select",
            )
            if st.button("Suspend Selected", type="secondary", key="btn_suspend"):
                for sel in selected_suspend:
                    vid = sel.split(" — ")[0]
                    update_vendor_status(vid, "Suspended")
                st.warning(f"Suspended {len(selected_suspend)} vendor(s).", icon=":material/warning:")
                st.rerun()
        else:
            st.caption("No active vendors to suspend.")

    st.markdown("---")

    # ──────────────────────────────────────────────
    # Vendor Detail Editor
    # ──────────────────────────────────────────────
    st.markdown(f'<div class="section-header">{render_html_icon("edit", size="20px")} Edit Vendor</div>', unsafe_allow_html=True)

    selected_vendor_id = st.selectbox(
        "Select Vendor",
        options=[f"{v['vendor_id']} — {v['business_name']}" for v in vendors],
        key="edit_vendor_select",
    )

    if selected_vendor_id:
        vid = selected_vendor_id.split(" — ")[0]
        vendor = get_vendor_by_id(vid)

        if vendor:
            with st.form("edit_vendor_form"):
                e1, e2 = st.columns(2)
                with e1:
                    biz_name = st.text_input("Business Name", value=vendor["business_name"])
                    owner = st.text_input("Owner Name", value=vendor["owner_name"])
                    email = st.text_input("Email", value=vendor.get("email", ""))
                    phone = st.text_input("Phone", value=vendor.get("phone", ""))
                with e2:
                    gst = st.text_input("GST Number", value=vendor.get("gst_number", ""))
                    address = st.text_input("Address", value=vendor.get("address", ""))
                    city = st.text_input("City", value=vendor.get("city", ""))
                    state = st.text_input("State", value=vendor.get("state", ""))

                c1, c2 = st.columns(2)
                with c1:
                    commission = st.number_input(
                        "Commission Rate (%)",
                        min_value=0.0, max_value=50.0,
                        value=float(vendor["commission_rate"]),
                        step=0.5,
                    )
                with c2:
                    new_status = st.selectbox(
                        "Status",
                        ["Active", "Pending", "Suspended"],
                        index=["Active", "Pending", "Suspended"].index(vendor["status"]),
                    )

                submitted = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                if submitted:
                    update_vendor_profile(
                        vid,
                        business_name=biz_name, owner_name=owner,
                        email=email, phone=phone, gst_number=gst,
                        address=address, city=city, state=state,
                    )
                    update_vendor_commission(vid, commission)
                    update_vendor_status(vid, new_status)
                    st.success("Vendor updated successfully!", icon=":material/check:")
                    st.rerun()
