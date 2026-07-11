"""
Customer Management Page — Search, profile view, edit, delete, and history.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.database_utils import get_paginated_data, update_record, delete_record
from utils.visualization import kpi_card
from utils.auth import log_activity

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Customer Management")

st.markdown("# 👤 Customer Management")
st.markdown("Search, view, and manage customer profiles")
st.markdown("---")

conn = get_connection()

# ── Filters ──
fc1, fc2, fc3, fc4 = st.columns(4)
with fc1:
    search = st.text_input("🔍 Search", placeholder="Name, ID, or email...")
with fc2:
    regions = ["All"] + pd.read_sql("SELECT DISTINCT region FROM customers ORDER BY region", conn)["region"].tolist()
    region_filter = st.selectbox("Region", regions)
with fc3:
    branches = ["All"] + pd.read_sql("SELECT DISTINCT branch FROM customers ORDER BY branch", conn)["branch"].tolist()
    branch_filter = st.selectbox("Branch", branches)
with fc4:
    risk_levels = ["All", "Low", "Medium", "High"]
    risk_filter = st.selectbox("Risk Level", risk_levels)

# Build filters dict
filters = {}
if region_filter != "All":
    filters["region"] = region_filter
if branch_filter != "All":
    filters["branch"] = branch_filter
if risk_filter != "All":
    filters["risk_level"] = risk_filter

# Pagination
if "cust_page" not in st.session_state:
    st.session_state["cust_page"] = 1

df, total = get_paginated_data(
    "customers",
    page=st.session_state["cust_page"],
    page_size=20,
    filters=filters,
    search=search,
    search_columns=["customer_id", "name", "email", "phone"],
    order_by="name"
)

conn.close()

# ── Summary Stats ──
s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown(kpi_card("Results Found", f"{total:,}", "👥", color="blue"), unsafe_allow_html=True)
with s2:
    avg_income = df["income"].mean() if not df.empty else 0
    st.markdown(kpi_card("Avg Income", f"${avg_income:,.0f}", "💵", color="green"), unsafe_allow_html=True)
with s3:
    avg_balance = df["balance"].mean() if not df.empty else 0
    st.markdown(kpi_card("Avg Balance", f"${avg_balance:,.0f}", "🏦", color="gold"), unsafe_allow_html=True)
with s4:
    avg_cs = df["credit_score"].mean() if not df.empty else 0
    st.markdown(kpi_card("Avg Credit Score", f"{avg_cs:.0f}", "📊", color="teal"), unsafe_allow_html=True)

st.markdown("---")

# ── Customer List ──
    if df.empty:
        st.info("No customers found matching your criteria.")
    else:
        table_html = """
    <table class="styled-table">
        <thead>
            <tr>
                <th>Customer ID</th>
                <th>Name & Demographics</th>
                <th>Occupation</th>
                <th>Location</th>
                <th>Financials</th>
                <th>Credit Score</th>
                <th>Risk Level</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
    """
    for _, row in df.iterrows():
        risk_val = row.get("risk_level", "Low")
        risk_class = "success" if risk_val == "Low" else "warning" if risk_val == "Medium" else "danger"
        
        status_val = "Active" if row.get("is_active") else "Inactive"
        status_class = "success" if row.get("is_active") else "danger"
        
        table_html += f"""
            <tr>
                <td><code>{row['customer_id']}</code></td>
                <td><b>{row['name']}</b><br><span style="font-size:0.75rem; color:#64748B;">{row['gender']}, Age {row['age']}</span></td>
                <td>{row['occupation']}</td>
                <td>{row['region']}<br><span style="font-size:0.75rem; color:#64748B;">{row['branch']}</span></td>
                <td>Bal: <b>${row['balance']:,.2f}</b><br><span style="font-size:0.75rem; color:#64748B;">Inc: ${row['income']:,.0f}</span></td>
                <td>{row['credit_score']:.0f}</td>
                <td><span class="status-pill {risk_class}">{risk_val}</span></td>
                <td><span class="status-pill {status_class}">{status_val}</span></td>
            </tr>
        """
    table_html += "</tbody></table>"
    st.markdown(table_html, unsafe_allow_html=True)

    # Pagination
    total_pages = max(1, (total + 20 - 1) // 20)
    pc1, pc2, pc3 = st.columns([1, 2, 1])
    with pc1:
        if st.button("◀️ Previous", disabled=st.session_state["cust_page"] <= 1, key="cp"):
            st.session_state["cust_page"] -= 1
            st.rerun()
    with pc2:
        st.markdown(f"<div style='text-align:center;'>Page {st.session_state['cust_page']} of {total_pages}</div>", unsafe_allow_html=True)
    with pc3:
        if st.button("Next ▶️", disabled=st.session_state["cust_page"] >= total_pages, key="cn"):
            st.session_state["cust_page"] += 1
            st.rerun()

    # ── Customer Profile Detail ──
    st.markdown("---")
    st.markdown("### 📋 Customer Profile")

    selected_id = st.selectbox(
        "Select Customer",
        df["customer_id"].tolist(),
        format_func=lambda x: f"{x} — {df[df['customer_id']==x]['name'].values[0]}" if len(df[df['customer_id']==x]) > 0 else x
    )

    if selected_id:
        cust = df[df["customer_id"] == selected_id].iloc[0]

        # Profile cards
        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown(f"""
            <div class="kpi-card blue">
                <h4 style="color:#1B2A4A; margin:0;">👤 {cust['name']}</h4>
                <p style="margin:0.25rem 0; color:#6C757D;">ID: {cust['customer_id']}</p>
                <p style="margin:0; color:#6C757D;">Gender: {cust.get('gender', 'N/A')} · Age: {cust.get('age', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        with p2:
            risk_color = {"Low": "#28A745", "Medium": "#FFC107", "High": "#DC3545"}.get(cust.get('risk_level', 'Low'), '#6C757D')
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color: {risk_color};">
                <p style="margin:0;"><strong>Income:</strong> ${cust.get('income', 0):,.0f}</p>
                <p style="margin:0.25rem 0;"><strong>Balance:</strong> ${cust.get('balance', 0):,.2f}</p>
                <p style="margin:0;"><strong>Credit Score:</strong> {cust.get('credit_score', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        with p3:
            st.markdown(f"""
            <div class="kpi-card gold">
                <p style="margin:0;"><strong>Region:</strong> {cust.get('region', 'N/A')}</p>
                <p style="margin:0.25rem 0;"><strong>Branch:</strong> {cust.get('branch', 'N/A')}</p>
                <p style="margin:0;"><strong>Occupation:</strong> {cust.get('occupation', 'N/A')}</p>
                <p style="margin:0.25rem 0;"><strong>Customer Since:</strong> {cust.get('customer_since', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        # Customer History
        with st.expander("📜 Transaction History"):
            conn = get_connection()
            txn_df = pd.read_sql(
                "SELECT * FROM transactions WHERE customer_id = ? ORDER BY date DESC LIMIT 50",
                conn, params=[selected_id]
            )
            conn.close()
            if not txn_df.empty:
                st.dataframe(txn_df, use_container_width=True)
            else:
                st.info("No transactions found.")

        with st.expander("🏦 Loan History"):
            conn = get_connection()
            loan_df = pd.read_sql(
                "SELECT * FROM loans WHERE customer_id = ? ORDER BY applied_date DESC",
                conn, params=[selected_id]
            )
            conn.close()
            if not loan_df.empty:
                st.dataframe(loan_df, use_container_width=True)
            else:
                st.info("No loans found.")

        # Edit / Delete
        with st.expander("✏️ Edit Customer"):
            with st.form("edit_customer_form"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    new_income = st.number_input("Income", value=float(cust.get('income', 0)))
                    new_region = st.text_input("Region", value=cust.get('region', ''))
                with ec2:
                    new_balance = st.number_input("Balance", value=float(cust.get('balance', 0)))
                    new_branch = st.text_input("Branch", value=cust.get('branch', ''))

                if st.form_submit_button("💾 Save Changes", type="primary"):
                    update_record("customers", "customer_id", selected_id, {
                        "income": new_income, "balance": new_balance,
                        "region": new_region, "branch": new_branch
                    })
                    st.success("✅ Customer updated!")
                    log_activity(user["user_id"], user["username"], "UPDATE_CUSTOMER", f"Updated {selected_id}")
                    st.rerun()

        with st.expander("🗑️ Delete Customer"):
            st.warning(f"⚠️ This will permanently delete customer **{cust['name']}** ({selected_id})")
            if st.checkbox("I confirm deletion", key="confirm_cust_delete"):
                if st.button("🗑️ Delete", type="primary"):
                    delete_record("customers", "customer_id", selected_id)
                    st.success("✅ Customer deleted!")
                    log_activity(user["user_id"], user["username"], "DELETE_CUSTOMER", f"Deleted {selected_id}")
                    st.rerun()
