"""
Database Manager Page — CRUD operations with search, filters, and pagination.
"""
import streamlit as st
from utils.icons import render_html_icon
import pandas as pd
from authentication import check_auth, require_role
from utils.database_utils import (
    get_paginated_data, insert_record, update_record, delete_record,
    get_table_stats, get_distinct_values
)
from utils.auth import log_activity

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Database Manager")

st.markdown(f"# {render_html_icon('database', size='30px')} Database Manager", unsafe_allow_html=True)
st.markdown("Manage banking database tables with full CRUD operations")
st.markdown("---")

# ── Table Selection ──
tables = {
    "customers": {"id_col": "customer_id", "search_cols": ["customer_id", "name", "email", "region", "branch"]},
    "accounts": {"id_col": "account_number", "search_cols": ["account_number", "customer_id", "account_type"]},
    "transactions": {"id_col": "transaction_id", "search_cols": ["transaction_id", "customer_id", "type", "channel"]},
    "loans": {"id_col": "loan_id", "search_cols": ["loan_id", "customer_id", "loan_type", "status"]},
    "cards": {"id_col": "card_number", "search_cols": ["card_number", "customer_id", "card_type"]},
}

selected_table = st.selectbox("Select Table", list(tables.keys()), format_func=lambda x: x.title())
table_config = tables[selected_table]

# ── Table Stats ──
stats = get_table_stats(selected_table)
s1, s2, s3 = st.columns(3)
with s1:
    st.metric("Total Records", f"{stats['row_count']:,}")
with s2:
    st.metric("Columns", stats["column_count"])
with s3:
    st.metric("Table", selected_table.title())

st.markdown("---")

# ── Tabs ──
tab_read, tab_create, tab_update, tab_delete = st.tabs([":material/menu_book: Browse", ":material/add: Create", ":material/edit: Update", ":material/delete: Delete"])

# ── Read Tab ──
with tab_read:
    # Search and filters
    fc1, fc2 = st.columns([2, 1])
    with fc1:
        search = st.text_input("Search", placeholder="Search across key columns...", key="db_search")
    with fc2:
        page_size = st.selectbox("Rows per page", [10, 20, 50, 100], index=1, key="db_page_size")

    # Pagination state
    if "db_page" not in st.session_state:
        st.session_state["db_page"] = 1

    df, total = get_paginated_data(
        selected_table,
        page=st.session_state["db_page"],
        page_size=page_size,
        search=search,
        search_columns=table_config["search_cols"],
    )

    total_pages = max(1, (total + page_size - 1) // page_size)

    st.dataframe(df, use_container_width=True, height=400)

    # Pagination controls
    pc1, pc2, pc3, pc4, pc5 = st.columns([1, 1, 2, 1, 1])
    with pc1:
        if st.button("⏮️ First", disabled=st.session_state["db_page"] <= 1):
            st.session_state["db_page"] = 1
            st.rerun()
    with pc2:
        if st.button("◀️ Prev", disabled=st.session_state["db_page"] <= 1):
            st.session_state["db_page"] -= 1
            st.rerun()
    with pc3:
        st.markdown(f"<div style='text-align:center;padding:0.5rem;'>Page {st.session_state['db_page']} of {total_pages} ({total} records)</div>", unsafe_allow_html=True)
    with pc4:
        if st.button("Next ▶️", disabled=st.session_state["db_page"] >= total_pages):
            st.session_state["db_page"] += 1
            st.rerun()
    with pc5:
        if st.button("Last ⏭️", disabled=st.session_state["db_page"] >= total_pages):
            st.session_state["db_page"] = total_pages
            st.rerun()

# ── Create Tab ──
with tab_create:
    st.markdown("### Add New Record")
    columns = stats["columns"]

    with st.form("create_form", clear_on_submit=True):
        new_record = {}
        cols = st.columns(2)
        for i, col_name in enumerate(columns):
            with cols[i % 2]:
                new_record[col_name] = st.text_input(col_name.replace("_", " ").title(), key=f"create_{col_name}")

        if st.form_submit_button("Add Record", icon=":material/add:", type="primary", use_container_width=True):
            # Remove empty values
            new_record = {k: v for k, v in new_record.items() if v}
            if new_record:
                if insert_record(selected_table, new_record):
                    st.success(f"Record added to {selected_table}")
                    log_activity(user["user_id"], user["username"], "CREATE", f"Added record to {selected_table}")
                    st.rerun()
                else:
                    st.error("Failed to add record (duplicate ID?)", icon=":material/cancel:")
            else:
                st.warning("Please fill in at least one field", icon=":material/warning:")

# ── Update Tab ──
with tab_update:
    st.markdown("### Update Record")
    record_id = st.text_input(f"Enter {table_config['id_col'].replace('_', ' ').title()}", key="update_id")

    if record_id:
        df_record, _ = get_paginated_data(
            selected_table, page=1, page_size=1,
            filters={table_config["id_col"]: record_id}
        )

        if df_record.empty:
            st.warning(f"No record found with {table_config['id_col']} = {record_id}")
        else:
            st.markdown("#### Current Values")
            st.dataframe(df_record, use_container_width=True)

            with st.form("update_form"):
                st.markdown("#### New Values")
                updates = {}
                cols = st.columns(2)
                for i, col_name in enumerate(df_record.columns):
                    if col_name != table_config["id_col"]:
                        with cols[i % 2]:
                            current_val = str(df_record.iloc[0][col_name]) if pd.notna(df_record.iloc[0][col_name]) else ""
                            updates[col_name] = st.text_input(
                                col_name.replace("_", " ").title(),
                                value=current_val,
                                key=f"update_{col_name}"
                            )

                if st.form_submit_button("Update Record", icon=":material/edit:", type="primary", use_container_width=True):
                    updates = {k: v for k, v in updates.items() if v}
                    if updates:
                        update_record(selected_table, table_config["id_col"], record_id, updates)
                        st.success(f"Record updated in {selected_table}")
                        log_activity(user["user_id"], user["username"], "UPDATE", f"Updated {record_id} in {selected_table}")
                        st.rerun()

# ── Delete Tab ──
with tab_delete:
    st.markdown("### Delete Record")
    st.warning("This action cannot be undone!", icon=":material/warning:")

    del_id = st.text_input(f"Enter {table_config['id_col'].replace('_', ' ').title()} to Delete", key="delete_id")

    if del_id:
        df_record, _ = get_paginated_data(
            selected_table, page=1, page_size=1,
            filters={table_config["id_col"]: del_id}
        )

        if df_record.empty:
            st.warning(f"No record found with {table_config['id_col']} = {del_id}")
        else:
            st.markdown("#### Record to Delete")
            st.dataframe(df_record, use_container_width=True)

            confirm = st.checkbox("I confirm I want to delete this record", key="confirm_delete")
            if confirm:
                if st.button("Delete Record", icon=":material/delete:", type="primary"):
                    delete_record(selected_table, table_config["id_col"], del_id)
                    st.success(f"Record deleted from {selected_table}")
                    log_activity(user["user_id"], user["username"], "DELETE", f"Deleted {del_id} from {selected_table}")
                    st.rerun()