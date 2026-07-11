"""
Authentication Module — Login UI and session management for Streamlit.
"""
import os
import streamlit as st
from jwt_handler import create_token, validate_token
from utils.auth import authenticate_user, log_activity
from config import PAGE_ACCESS, ROLES, DEMO_USERS, ASSETS_DIR


def login_page():
    """Render the login page with banking-themed UI and demo credentials panel."""
    # Hide sidebar when not logged in
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            '<div style="text-align: center; padding: 2.5rem 0 1rem 0;">'
            '<div style="font-size: 4.5rem; margin-bottom: 0.5rem; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.08));">🏦</div>'
            '<h1 style="color: #1B2A4A; margin-bottom: 0.25rem; font-size: 2rem; font-weight: 800;">AI Banking Insights</h1>'
            '<p style="color: #64748B; font-size: 1.05rem; font-weight: 500;">Customer Insights Platform v1.0</p>'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-top: 0; margin-bottom: 1.25rem; color: #1B2A4A; font-weight: 700;">🔐 Sign In</h4>', unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter your username", key="login_username")
        
        # Show password toggle and input
        show_pass = st.checkbox("👁️ Show password", key="show_pass")
        pass_type = "default" if show_pass else "password"
        password = st.text_input("Password", type=pass_type, placeholder="Enter your password", key="login_password")
        
        error_placeholder = st.empty()
        submitted = st.button("🔓 Login", use_container_width=True, type="primary", key="login_submit_btn")
        st.markdown('</div>', unsafe_allow_html=True)

        if submitted:
            if not username or not password:
                error_placeholder.markdown('<div class="login-inline-error">⚠️ Please enter both username and password.</div>', unsafe_allow_html=True)
            else:
                with st.spinner("🔒 Securing connection & authenticating..."):
                    import time
                    time.sleep(0.6) # Subtle visual loading state
                    user = authenticate_user(username, password)
                    if user:
                        token = create_token(
                            user_id=user["user_id"],
                            username=user["username"],
                            role=user["role"],
                            full_name=user["full_name"],
                        )
                        st.session_state["jwt_token"] = token
                        st.session_state["user"] = user
                        log_activity(user["user_id"], user["username"], "LOGIN", "User logged in successfully")
                        error_placeholder.markdown(f'<div class="login-inline-success">✅ Welcome back, {user["full_name"]}! Redirecting...</div>', unsafe_allow_html=True)
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        error_placeholder.markdown('<div class="login-inline-error">❌ Invalid username or password.</div>', unsafe_allow_html=True)

        # ── Demo Credentials Panel ──
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown('<h5 style="color: #1B2A4A; font-weight: 700; margin-bottom: 0.5rem;">🎯 Demo Login Credentials</h5>', unsafe_allow_html=True)
        st.markdown(
            '<style>'
            '.demo-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 10px; border-radius: 8px; overflow: hidden; border: 1px solid #E2E8F0; }'
            '.demo-table th { background: #1B2A4A; color: #FFFFFF; padding: 10px 14px; text-align: left; font-weight: 600; }'
            '.demo-table td { padding: 8px 14px; border-bottom: 1px solid #E2E8F0; color: #1B2A4A !important; background: #FFFFFF; }'
            '.demo-table code { background: #F1F5F9 !important; color: #1B2A4A !important; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; }'
            '.demo-table tr:hover td { background: #F8FAFC; }'
            '.role-pill { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }'
            '</style>',
            unsafe_allow_html=True
        )

        role_colors = {
            "admin": "background:#FFEBEE; color:#C62828;",
            "bank_manager": "background:#E8F5E9; color:#2E7D32;",
            "data_analyst": "background:#E0F7FA; color:#006064;",
        }

        table_rows = ""
        for u in DEMO_USERS:
            style_str = role_colors.get(u["role"], "background:#F1F5F9; color:#64748B;")
            role_label = ROLES.get(u["role"], u["role"])
            table_rows += f"<tr><td><code>{u['username']}</code></td><td><code>{u['password']}</code></td><td><span class=\"role-pill\" style=\"{style_str}\">{role_label}</span></td></tr>"

        st.markdown(
            f'<table class="demo-table"><thead><tr><th>Username</th><th>Password</th><th>Role</th></tr></thead><tbody>{table_rows}</tbody></table>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div style="margin-top: 1rem; padding: 0.75rem; background: #FFF3E0; border-radius: 8px; border-left: 4px solid #FF9800; font-size: 0.85rem; color: #E65100; font-weight: 500;">'
            '💡 <strong>Tip:</strong> Each role has different page access. Try logging in with different roles to see the difference.'
            '</div>',
            unsafe_allow_html=True
        )


def render_sidebar(current_page: str = "Home"):
    """Render the user profile and custom navigation in the sidebar (shared across all pages)."""
    user = st.session_state.get("user")
    if not user:
        return
        
    # Load custom CSS to apply styles (including hiding default navigation) on all pages
    css_path = os.path.join(ASSETS_DIR, "style.css")
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    with st.sidebar:
        # App branding header
        st.markdown(
            f'<div style="text-align: center; padding: 0.5rem 0;">'
            f'<div style="font-size: 2.2rem; margin-bottom: 0.2rem; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.15));">🏦</div>'
            f'<h3 class="sidebar-title" style="margin: 0; font-size: 1.15rem; font-weight: 700; letter-spacing: 0.5px;">AI Banking Insights</h3>'
            f'<p class="sidebar-subtitle" style="margin: 0.2rem 0; font-size: 0.8rem; font-weight: 500;">Customer Insights Platform</p>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown("---")
        
        # User details card
        st.markdown(
            f'<div class="sidebar-profile-card">'
            f'<p class="sidebar-profile-label">LOGGED IN AS</p>'
            f'<p class="sidebar-profile-name">{user["full_name"]}</p>'
            f'<div style="margin-top: 0.4rem;">{get_role_badge_html(user["role"])}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        # Custom Page Navigation Tree
        st.page_link("app.py", label="Home", icon="🏠")
        
        # 1. Dashboard
        is_dashboard_expanded = (current_page == "Dashboard")
        if user["role"] in PAGE_ACCESS.get("Dashboard", []):
            with st.expander("📊 Dashboard", expanded=is_dashboard_expanded):
                st.page_link("pages/1_Dashboard.py", label="Dashboard", icon="📊")
                
        # 2. Data Management
        data_mgmt_pages = [
            ("Data Upload", "pages/2_Data_Upload.py", "📤"),
            ("Data Preprocessing", "pages/3_Data_Preprocessing.py", "🛠️"),
            ("Database Manager", "pages/4_Database_Manager.py", "🗄️")
        ]
        is_data_expanded = (current_page in [p[0] for p in data_mgmt_pages])
        allowed_data_pages = [p for p in data_mgmt_pages if user["role"] in PAGE_ACCESS.get(p[0], [])]
        if allowed_data_pages:
            with st.expander("📂 Data Management", expanded=is_data_expanded):
                for label, path, icon in allowed_data_pages:
                    st.page_link(path, label=label, icon=icon)
                    
        # 3. Customer Management
        is_cust_expanded = (current_page == "Customer Management")
        if user["role"] in PAGE_ACCESS.get("Customer Management", []):
            with st.expander("👥 Customer Management", expanded=is_cust_expanded):
                st.page_link("pages/5_Customer_Management.py", label="Customer Management", icon="👥")
                
        # 4. Analytics
        analytics_pages = [
            ("Transaction Analytics", "pages/6_Transaction_Analytics.py", "💳"),
            ("Loan Analytics", "pages/7_Loan_Analytics.py", "🏦"),
            ("EDA", "pages/8_EDA.py", "📈")
        ]
        is_analytics_expanded = (current_page in [p[0] for p in analytics_pages])
        allowed_analytics_pages = [p for p in analytics_pages if user["role"] in PAGE_ACCESS.get(p[0], [])]
        if allowed_analytics_pages:
            with st.expander("📈 Analytics", expanded=is_analytics_expanded):
                for label, path, icon in allowed_analytics_pages:
                    st.page_link(path, label=label, icon=icon)
                    
        # 5. AI & Machine Learning
        ai_ml_pages = [
            ("Customer Segmentation", "pages/9_Customer_Segmentation.py", "🎯"),
            ("Churn Prediction", "pages/10_Churn_Prediction.py", "🔮"),
            ("CLV Prediction", "pages/13_CLV_Prediction.py", "💎"),
            ("Product Recommendation", "pages/15_Product_Recommendation.py", "💡"),
            ("Deposit Prediction", "pages/17_Deposit_Prediction.py", "💰"),
            ("AI Business Insights", "pages/18_AI_Business_Insights.py", "🤖")
        ]
        is_ai_expanded = (current_page in [p[0] for p in ai_ml_pages])
        allowed_ai_pages = [p for p in ai_ml_pages if user["role"] in PAGE_ACCESS.get(p[0], [])]
        if allowed_ai_pages:
            with st.expander("🤖 AI & Machine Learning", expanded=is_ai_expanded):
                for label, path, icon in allowed_ai_pages:
                    st.page_link(path, label=label, icon=icon)
                    
        # 6. Reports
        is_reports_expanded = (current_page == "Reports")
        if user["role"] in PAGE_ACCESS.get("Reports", []):
            with st.expander("📑 Reports", expanded=is_reports_expanded):
                st.page_link("pages/19_Reports.py", label="Reports", icon="📑")
                
        # 7. Administration
        admin_pages = [
            ("Admin", "pages/20_Admin.py", "🔑"),
            ("Settings", "pages/21_Settings.py", "⚙️")
        ]
        is_admin_expanded = (current_page in [p[0] for p in admin_pages])
        allowed_admin_pages = [p for p in admin_pages if user["role"] in PAGE_ACCESS.get(p[0], [])]
        if allowed_admin_pages:
            with st.expander("⚙️ Administration", expanded=is_admin_expanded):
                for label, path, icon in allowed_admin_pages:
                    st.page_link(path, label=label, icon=icon)
                    
        st.markdown("---")
        
        # Pinned Contact Us CTA
        st.markdown(
            f'<div class="sidebar-cta-card">'
            f'<div class="sidebar-cta-title">Need Assistance?</div>'
            f'<div class="sidebar-cta-text">Contact our dedicated support desk for priority assistance.</div>'
            f'<a class="sidebar-cta-btn" href="mailto:support@aibanking.com">Support Desk</a>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True, key="shared_sidebar_logout_btn"):
            logout()
            st.rerun()
        st.markdown("---")


def check_auth() -> dict | None:
    """
    Check if the current session is authenticated.
    Call this at the top of every page.

    Returns:
        User dict if authenticated, None otherwise (also calls st.stop())
    """
    token = st.session_state.get("jwt_token")
    if not token:
        return None

    payload = validate_token(token)
    if not payload:
        # Token expired or invalid
        st.session_state.pop("jwt_token", None)
        st.session_state.pop("user", None)
        return None

    return st.session_state.get("user")


def require_role(page_name: str):
    """
    Check if the current user has access to the specified page.
    Shows an access denied message and stops execution if unauthorized.

    Args:
        page_name: The page name key from PAGE_ACCESS config
    """
    user = st.session_state.get("user")
    if not user:
        st.error("🔒 Please log in to access this page.")
        st.stop()

    allowed_roles = PAGE_ACCESS.get(page_name, [])
    if user["role"] not in allowed_roles:
        render_sidebar(page_name)
        st.error("🚫 **Access Denied**")
        st.markdown(f"""
        <div style="padding: 1.5rem; background: #F8D7DA; border-radius: 8px; border-left: 4px solid #DC3545; margin-top: 1rem;">
            <p style="margin: 0; color: #721C24;">
                Your role <strong>({ROLES.get(user['role'], user['role'])})</strong> does not have permission to access <strong>{page_name}</strong>.
            </p>
            <p style="margin: 0.5rem 0 0 0; color: #721C24; font-size: 0.9rem;">
                Contact your administrator if you need access.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    render_sidebar(page_name)


def logout():
    """Clear session state and log the user out."""
    user = st.session_state.get("user")
    if user:
        log_activity(user.get("user_id", 0), user.get("username", ""), "LOGOUT", "User logged out")

    for key in ["jwt_token", "user"]:
        st.session_state.pop(key, None)


def get_role_badge_html(role: str) -> str:
    """Get an HTML badge for a user role."""
    role_colors = {
        "admin": "#DC3545",
        "bank_manager": "#2E86AB",
        "data_analyst": "#6F42C1",
    }
    color = role_colors.get(role, "#6C757D")
    label = ROLES.get(role, role)
    return f'<span style="display:inline-block;padding:3px 10px;border-radius:12px;background:{color};color:white;font-size:0.8rem;font-weight:600;">{label}</span>'
