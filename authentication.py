"""
Authentication Module — Login UI and session management for Streamlit.
"""
import os
import streamlit as st
from jwt_handler import create_token, validate_token
from utils.auth import authenticate_user, log_activity
from config import PAGE_ACCESS, ROLES, DEMO_USERS, ASSETS_DIR


def login_page():
    """Render the split-screen login page with left hero panel and centered right form."""
    # Hide sidebar and default header components, configure full bleed split-screen
    st.markdown(
        """<style>
[data-testid="stSidebar"] {
    display: none !important;
}
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

.stApp {
    background-color: #F8FAFC !important;
}

/* Layout Grid Container */
div[data-testid="stHorizontalBlock"] {
    background: #FFFFFF !important;
    border-radius: 16px !important;
    box-shadow: 0 10px 40px rgba(27, 42, 74, 0.08) !important;
    overflow: hidden !important;
    border: 1px solid #E2E8F0 !important;
    gap: 0px !important;
    max-width: 1000px !important;
    margin: 4% auto !important;
}

/* Left Column (Branded Indigo Hero) */
div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:nth-of-type(1) {
    background-color: #3D3DE0 !important;
    background: #3D3DE0 !important;
    padding: 3.5rem 3rem !important;
    color: #FFFFFF !important;
    min-height: 590px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
    position: relative !important;
    overflow: hidden !important;
}

div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:nth-of-type(1) * {
    color: #FFFFFF !important;
}

/* Right Column (Centered Login Form) */
div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:nth-of-type(2) {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    padding: 3.5rem 3rem !important;
    min-height: 590px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}

/* Responsive styling for Mobile */
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"] {
        margin: 1rem !important;
        border-radius: 16px !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:nth-of-type(1) {
        display: none !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stColumn"]:nth-of-type(2) {
        border-radius: 16px !important;
        border-left: 1px solid #E2E8F0 !important;
        padding: 2.25rem !important;
    }
}
</style>""",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([55, 45])
    
    with col1:
        # Left Hero Panel Content
        st.markdown(
            """<div style="height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
<div>
<!-- 8-pointed SVG asterisk logo -->
<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom: 2rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));">
<line x1="12" y1="2" x2="12" y2="22"></line>
<line x1="2" y1="12" x2="22" y2="12"></line>
<line x1="4.93" y1="4.93" x2="19.07" y2="19.07"></line>
<line x1="4.93" y1="19.07" x2="19.07" y2="4.93"></line>
</svg>
<div style="font-size: 0.85rem; font-weight: 750; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.85; margin-bottom: 2rem;">
AI Banking Customer Insights
</div>
<h1 style="color: #FFFFFF; font-size: 2.1rem; font-weight: 800; line-height: 1.25; margin-bottom: 1.25rem;">
Welcome to AI Banking Customer Insights
</h1>
<p style="color: rgba(255, 255, 255, 0.85); font-size: 1.05rem; line-height: 1.5; max-width: 360px;">
Unlock deep retail banking customer insights with predictive ML pipelines, CLV forecasting, and risk analysis.
</p>
</div>

<!-- Background decorative lines -->
<div class="left-bg-lines">
<svg width="100%" height="100%" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
<circle cx="160" cy="160" r="100" stroke="rgba(255,255,255,0.06)" stroke-width="1.5"/>
<circle cx="160" cy="160" r="130" stroke="rgba(255,255,255,0.04)" stroke-width="1.5"/>
<circle cx="160" cy="160" r="160" stroke="rgba(255,255,255,0.02)" stroke-width="1.5"/>
</svg>
</div>

<!-- Footer copyright -->
<div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.55); font-weight: 500; margin-top: 3rem;">
© 2026 AI Banking Customer Insights. All rights reserved.
</div>
</div>""",
            unsafe_allow_html=True
        )

    with col2:
        # Right Form Panel Content
        st.markdown(
            """<div style="margin-bottom: 1.5rem;">
<h2 style="color: #1B2A4A; font-weight: 800; font-size: 1.75rem; margin: 0 0 0.25rem 0;">Welcome Back!</h2>
<p style="color: #64748B; font-size: 0.95rem; margin: 0;">Sign in to access your dashboard.</p>
</div>""",
            unsafe_allow_html=True
        )
        
        # Username input + error block
        username = st.text_input("Username", placeholder="Enter your username", key="login_username")
        username_error = st.empty()
        
        # Password input + error block
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
        password_error = st.empty()
        
        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
        
        # Dark navy submit button
        st.markdown('<div class="login-btn-dark">', unsafe_allow_html=True)
        submitted = st.button("Login Now", use_container_width=True, key="login_submit_btn")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Form submission validation and authentication logic
        if submitted:
            has_error = False
            username_error.empty()
            password_error.empty()
            
            if not username:
                username_error.markdown('<div style="color: #C62828; font-size: 0.85rem; margin-top: 4px; margin-bottom: 8px; font-weight: 600;">⚠️ Username is required.</div>', unsafe_allow_html=True)
                has_error = True
            if not password:
                password_error.markdown('<div style="color: #C62828; font-size: 0.85rem; margin-top: 4px; margin-bottom: 8px; font-weight: 600;">⚠️ Password is required.</div>', unsafe_allow_html=True)
                has_error = True
                
            if not has_error:
                with st.spinner("Logging in..."):
                    import time
                    time.sleep(0.5)
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
                        st.rerun()
                    else:
                        password_error.markdown('<div style="color: #C62828; font-size: 0.85rem; margin-top: 4px; margin-bottom: 8px; font-weight: 600;">❌ Invalid username or password.</div>', unsafe_allow_html=True)

        # Demo Credentials Panel inside minimal card expander
        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)
        with st.expander("🎯 View Demo Credentials", expanded=False):
            st.markdown(
                """<style>
.demo-card-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #F1F5F9;
    padding: 8px 0;
}
.demo-card-item:last-child {
    border-bottom: none;
}
.demo-role-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}
</style>
<div style="background: #FFFFFF; padding: 4px; font-size: 0.85rem;">
    <div style="margin-bottom: 8px; font-weight: 600; color: #64748B;">Test credentials with pre-configured roles:</div>
    <div class="demo-card-item">
        <span>👤 <code>admin</code> (admin123)</span>
        <span class="demo-role-badge" style="background:#FFEBEE; color:#C62828;">Admin</span>
    </div>
    <div class="demo-card-item">
        <span>👤 <code>manager</code> (manager123)</span>
        <span class="demo-role-badge" style="background:#E8F5E9; color:#2E7D32;">Manager</span>
    </div>
    <div class="demo-card-item">
        <span>👤 <code>analyst</code> (analyst123)</span>
        <span class="demo-role-badge" style="background:#E0F7FA; color:#006064;">Analyst</span>
    </div>
</div>""",
                unsafe_allow_html=True
            )
            st.markdown(
                '<div style="margin-top: 8px; padding: 0.75rem; background: #FFF3E0; border-radius: 8px; border-left: 4px solid #FF9800; font-size: 0.82rem; color: #E65100; font-weight: 500;">'
                '💡 <strong>Tip:</strong> Log in with different roles to test different page permissions.'
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
