"""
Admin Module — User management, audit logs, database backup, system stats.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role, get_role_badge_html
from database import get_connection, get_table_row_count, get_db_size
from utils.auth import (
    list_users, create_user, update_user, reset_password, delete_user,
    get_audit_logs, log_activity
)
from utils.database_utils import backup_database, get_table_stats
from utils.visualization import kpi_card
from config import ROLES

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Admin")

st.markdown("# ⚙️ Admin Panel")
st.markdown("System administration, user management, and monitoring")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Users", "📋 Audit Logs", "💾 Backup", "📊 Statistics", "🕐 Activity"])

# ── Tab 1: User Management ──
with tab1:
    st.markdown("### User Management")

    users = list_users()

    # Summary
    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(kpi_card("Total Users", f"{len(users)}", "👥", color="blue"), unsafe_allow_html=True)
    with s2:
        active = sum(1 for u in users if u.get("is_active"))
        st.markdown(kpi_card("Active Users", f"{active}", "✅", color="green"), unsafe_allow_html=True)
    with s3:
        roles_count = len(set(u["role"] for u in users))
        st.markdown(kpi_card("Roles Used", f"{roles_count}", "🏷️", color="gold"), unsafe_allow_html=True)

    st.markdown("---")

    # User list
    if users:
        user_df = pd.DataFrame(users)
        user_df["role_display"] = user_df["role"].map(ROLES)
        st.dataframe(user_df[["id", "username", "full_name", "email", "role_display", "is_active", "last_login"]],
                     use_container_width=True)

    # Create new user
    st.markdown("---")
    with st.expander("➕ Create New User"):
        with st.form("create_user_form", clear_on_submit=True):
            nc1, nc2 = st.columns(2)
            with nc1:
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
                new_email = st.text_input("Email")
            with nc2:
                new_fullname = st.text_input("Full Name")
                new_role = st.selectbox("Role", list(ROLES.keys()), format_func=lambda x: ROLES[x])

            if st.form_submit_button("➕ Create User", type="primary", use_container_width=True):
                if new_username and new_password and new_fullname:
                    if create_user(new_username, new_password, new_fullname, new_email, new_role):
                        st.success(f"✅ User '{new_username}' created!")
                        log_activity(user["user_id"], user["username"], "CREATE_USER", f"Created user {new_username}")
                        st.rerun()
                    else:
                        st.error("❌ Username already exists.")
                else:
                    st.warning("⚠️ Please fill in all required fields.")

    # Edit / Reset / Delete
    with st.expander("✏️ Edit User"):
        if users:
            edit_user = st.selectbox("Select User", users,
                format_func=lambda u: f"{u['username']} ({ROLES.get(u['role'], u['role'])})", key="edit_select")

            if edit_user:
                ec1, ec2 = st.columns(2)
                with ec1:
                    edit_name = st.text_input("Full Name", value=edit_user["full_name"], key="edit_name")
                    edit_email = st.text_input("Email", value=edit_user.get("email", ""), key="edit_email")
                with ec2:
                    edit_role = st.selectbox("Role", list(ROLES.keys()),
                        index=list(ROLES.keys()).index(edit_user["role"]) if edit_user["role"] in ROLES else 0,
                        format_func=lambda x: ROLES[x], key="edit_role")
                    edit_active = st.checkbox("Active", value=bool(edit_user["is_active"]), key="edit_active")

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾 Save Changes", type="primary", use_container_width=True):
                        update_user(edit_user["id"], full_name=edit_name, email=edit_email,
                                   role=edit_role, is_active=1 if edit_active else 0)
                        st.success("✅ User updated!")
                        log_activity(user["user_id"], user["username"], "UPDATE_USER", f"Updated {edit_user['username']}")
                        st.rerun()
                with bc2:
                    new_pw = st.text_input("New Password", type="password", key="reset_pw")
                    if st.button("🔑 Reset Password", use_container_width=True):
                        if new_pw:
                            reset_password(edit_user["id"], new_pw)
                            st.success("✅ Password reset!")
                            log_activity(user["user_id"], user["username"], "RESET_PASSWORD", f"Reset password for {edit_user['username']}")

    with st.expander("🗑️ Delete User"):
        if users:
            del_user = st.selectbox("Select User to Deactivate", users,
                format_func=lambda u: f"{u['username']} ({ROLES.get(u['role'], u['role'])})", key="del_select")
            if del_user:
                st.warning(f"⚠️ This will deactivate user **{del_user['username']}**")
                if st.checkbox("I confirm deactivation", key="confirm_del_user"):
                    if st.button("🗑️ Deactivate User", type="primary"):
                        delete_user(del_user["id"])
                        st.success("✅ User deactivated!")
                        log_activity(user["user_id"], user["username"], "DELETE_USER", f"Deactivated {del_user['username']}")
                        st.rerun()

# ── Tab 2: Audit Logs ──
with tab2:
    st.markdown("### Audit Logs")

    search = st.text_input("🔍 Search logs", placeholder="Search by username, action, or details...")

    if "audit_page" not in st.session_state:
        st.session_state["audit_page"] = 0

    logs, total = get_audit_logs(limit=50, offset=st.session_state["audit_page"] * 50, search=search)

    if logs:
        logs_df = pd.DataFrame(logs)
        st.dataframe(logs_df[["timestamp", "username", "action", "details"]],
                     use_container_width=True, height=400)

        p1, p2, p3 = st.columns([1, 2, 1])
        with p1:
            if st.button("◀️ Previous", disabled=st.session_state["audit_page"] <= 0, key="al_prev"):
                st.session_state["audit_page"] -= 1
                st.rerun()
        with p2:
            st.markdown(f"<div style='text-align:center;'>Page {st.session_state['audit_page']+1} ({total} total)</div>", unsafe_allow_html=True)
        with p3:
            if st.button("Next ▶️", disabled=(st.session_state["audit_page"]+1)*50 >= total, key="al_next"):
                st.session_state["audit_page"] += 1
                st.rerun()
    else:
        st.info("No audit logs found.")

# ── Tab 3: Database Backup ──
with tab3:
    st.markdown("### Database Backup")
    st.markdown(f"**Database Size:** {get_db_size()}")

    if st.button("💾 Create Backup", type="primary", use_container_width=True):
        with st.spinner("Creating backup..."):
            backup_path = backup_database()
            st.success(f"✅ Backup created: `{backup_path}`")
            log_activity(user["user_id"], user["username"], "DATABASE_BACKUP", f"Backup created at {backup_path}")

            with open(backup_path, "rb") as f:
                st.download_button("📥 Download Backup", f, "banking_backup.db", "application/octet-stream")

# ── Tab 4: System Statistics ──
with tab4:
    st.markdown("### System Statistics")

    tables = ["customers", "accounts", "transactions", "loans", "cards", "users", "audit_logs"]
    stats_data = []
    for table in tables:
        stats = get_table_stats(table)
        stats_data.append({
            "Table": table.title(),
            "Rows": f"{stats['row_count']:,}",
            "Columns": stats["column_count"]
        })

    stats_df = pd.DataFrame(stats_data)
    st.dataframe(stats_df, use_container_width=True)

    st.markdown(f"**Database Size:** {get_db_size()}")

# ── Tab 5: Activity Logs ──
with tab5:
    st.markdown("### Recent Activity")
    logs, _ = get_audit_logs(limit=20)
    if logs:
        for log in logs:
            icon = {"LOGIN": "🔑", "LOGOUT": "🚪", "CREATE_USER": "➕", "UPDATE_USER": "✏️",
                    "DELETE_USER": "🗑️", "DATA_UPLOAD": "📤", "REPORT_GENERATED": "📑",
                    "DATABASE_BACKUP": "💾"}.get(log["action"], "📝")

            st.markdown(f"""
            <div style="padding: 0.5rem 1rem; margin: 0.25rem 0; background: #F8F9FA; border-radius: 6px; border-left: 3px solid #2E86AB;">
                <span style="font-size: 1.1rem;">{icon}</span>
                <strong>{log['username']}</strong> · {log['action']} · <span style="color:#6C757D;">{log['timestamp']}</span>
                {f" · {log['details']}" if log.get('details') else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent activity.")
