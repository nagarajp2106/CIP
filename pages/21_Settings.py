"""
Settings Page — Theme, configuration, and preferences.
"""
import streamlit as st
from authentication import check_auth, require_role
from database import get_db_size
from config import APP_NAME, APP_VERSION, DATABASE_PATH, JWT_EXPIRY_HOURS, ROLES

# ── Auth ──
user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Settings")

st.markdown(f"# {render_html_icon('settings', size='30px')} Settings", unsafe_allow_html=True)
st.markdown("Platform configuration and preferences")
st.markdown("---")

tab1, tab2, tab3, tab4, tab5 = st.tabs([":material/palette: Theme", ":material/account_balance: General", ":material/lock: Security", ":material/upload_file: Export", ":material/notifications: Notifications"])

# ── Theme ──
with tab1:
    st.markdown("### Theme Settings")

    theme = st.radio("Color Theme", ["Light", "Dark", "Banking (Navy/Gold)"],
                     index=0, key="theme_select")

    if theme == "Dark":
        st.markdown("""
        <style>
            .stApp { background-color: #0D1B2A; color: #E0E6ED; }
            .kpi-card { background: #1B2A4A; }
            .kpi-card .kpi-value { color: #E0E6ED; }
        </style>
        """, unsafe_allow_html=True)
        st.info("Dark theme applied for this session.", icon=":material/dark_mode:")
    elif theme == "Banking (Navy/Gold)":
        st.info("Default banking theme is active.", icon=":material/account_balance:")
    else:
        st.info("Light theme is active.", icon=":material/light_mode:")

    st.markdown("---")
    st.markdown("### Display Options")
    show_animations = st.checkbox("Enable animations", value=True, key="anim")
    compact_mode = st.checkbox("Compact mode", value=False, key="compact")
    default_page_size = st.selectbox("Default table page size", [10, 20, 50, 100], index=1, key="page_size_setting")

    if st.button("Save Display Preferences", icon=":material/save:", type="primary"):
        st.session_state["display_prefs"] = {
            "animations": show_animations,
            "compact": compact_mode,
            "page_size": default_page_size
        }
        st.success("Display preferences saved!", icon=":material/check_circle:")

# ── General ──
with tab2:
    st.markdown("### Application Info")

    info_data = {
        "Application": APP_NAME,
        "Version": APP_VERSION,
        "Platform": "Streamlit Web Application",
        "Database": "SQLite",
        "Database Path": DATABASE_PATH,
        "Database Size": get_db_size(),
    }

    for key, value in info_data.items():
        st.markdown(f"**{key}:** {value}")

    st.markdown("---")
    st.markdown("### User Profile")
    st.markdown(f"**Name:** {user['full_name']}")
    st.markdown(f"**Username:** {user['username']}")
    st.markdown(f"**Role:** {ROLES.get(user['role'], user['role'])}")
    st.markdown(f"**Email:** {user.get('email', 'N/A')}")

# ── Security ──
with tab3:
    st.markdown("### Security Settings")

    if user["role"] == "admin":
        st.markdown(f"**JWT Token Expiry:** {JWT_EXPIRY_HOURS} hours")
        st.markdown("**Password Hashing:** bcrypt with salt")
        st.markdown("**Access Control:** Role-Based (6 roles)")

        st.markdown("---")
        st.markdown("### Role Permissions")

        from config import PAGE_ACCESS
from utils.icons import render_html_icon
        role_matrix = {}
        for page, roles in PAGE_ACCESS.items():
            for role in roles:
                if role not in role_matrix:
                    role_matrix[role] = []
                role_matrix[role].append(page)

        selected_role = st.selectbox("View Permissions for", list(ROLES.keys()),
                                     format_func=lambda x: ROLES[x], key="perm_role")
        if selected_role in role_matrix:
            pages = role_matrix[selected_role]
            st.markdown(f"**{ROLES[selected_role]}** has access to **{len(pages)}** pages:")
            for page in sorted(pages):
                st.markdown(f"- {render_html_icon('check_circle', size='16px', color='var(--success)')} {page}", unsafe_allow_html=True)
    else:
        st.info("Security settings are only visible to administrators.", icon=":material/lock:")

# ── Export ──
with tab4:
    st.markdown("### Export Preferences")

    default_format = st.selectbox("Default Export Format", ["Excel (.xlsx)", "PDF (.pdf)"], key="export_fmt")
    include_metadata = st.checkbox("Include metadata sheet in Excel exports", value=True, key="inc_meta")
    max_pdf_rows = st.number_input("Max rows in PDF reports", value=100, min_value=50, max_value=500, key="pdf_rows")

    if st.button("Save Export Preferences", icon=":material/save:", type="primary"):
        st.session_state["export_prefs"] = {
            "format": default_format,
            "include_metadata": include_metadata,
            "max_pdf_rows": max_pdf_rows
        }
        st.success("Export preferences saved!", icon=":material/check_circle:")

# ── Notifications ──
with tab5:
    st.markdown("### Notification Preferences")

    churn_threshold = st.slider("Churn Alert Threshold (%)", 5, 50, 20, step=5, key="churn_thresh")
    balance_alert = st.number_input("Low Balance Alert ($)", value=1000, min_value=0, step=100, key="bal_alert")

    notify_email = st.checkbox("Email notifications (coming soon)", value=False, disabled=True, key="email_notif")

    if st.button("Save Notification Preferences", icon=":material/save:", type="primary"):
        st.session_state["notification_prefs"] = {
            "churn_threshold": churn_threshold,
            "balance_alert": balance_alert,
        }
        st.success("Notification preferences saved!", icon=":material/check_circle:")