"""
Notifications — Notification center for all users.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — Notifications", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Notifications")

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("notifications", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Notifications</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

user_id = user["user_id"]

# Load notifications
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT * FROM notifications WHERE user_id = ?
    ORDER BY created_at DESC
""", (user_id,))
notifications = [dict(r) for r in cursor.fetchall()]
conn.close()

# KPIs
unread = sum(1 for n in notifications if not n["is_read"])
k1, k2 = st.columns(2)
with k1:
    st.markdown(f'<div class="kpi-card blue animate-in"><div class="kpi-value">{len(notifications)}</div><div class="kpi-label">Total Notifications</div></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card gold animate-in"><div class="kpi-value">{unread}</div><div class="kpi-label">Unread</div></div>', unsafe_allow_html=True)

if unread > 0:
    if st.button("Mark All as Read", type="primary", key="mark_all_read"):
        conn = get_connection()
        conn.cursor().execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        st.rerun()

st.markdown("---")

TYPE_ICONS = {
    "info": ("info", "#2E86AB"),
    "success": ("check_circle", "#28A745"),
    "warning": ("warning", "#FFC107"),
    "error": ("error", "#DC3545"),
    "order": ("receipt_long", "#6F42C1"),
}

if not notifications:
    st.markdown(f"""
    <div style="text-align:center;padding:3rem;background:#F8F9FA;border-radius:12px;border:2px dashed #E2E8F0;">
        {render_html_icon("notifications_none", size="4rem", color="#A0AEC0")}
        <h3 style="color:#6C757D;margin-top:1rem;">All caught up!</h3>
        <p style="color:#A0AEC0;">No notifications at this time.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for notif in notifications:
        icon_name, icon_color = TYPE_ICONS.get(notif.get("type", "info"), ("info", "#2E86AB"))
        bg = "#FFFFFF" if notif["is_read"] else "#F0F7FF"
        border = "#E2E8F0" if notif["is_read"] else icon_color

        st.markdown(f"""
        <div style="background:{bg};border:1px solid {border};border-left:4px solid {icon_color};border-radius:8px;padding:1rem;margin-bottom:0.5rem;display:flex;align-items:flex-start;gap:12px;">
            <div>{render_html_icon(icon_name, size="24px", color=icon_color)}</div>
            <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong style="color:#1B2A4A;">{notif['title']}</strong>
                    <span style="color:#A0AEC0;font-size:0.75rem;">{notif['created_at']}</span>
                </div>
                <p style="color:#6C757D;font-size:0.9rem;margin:0.25rem 0 0 0;">{notif.get('message', '')}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not notif["is_read"]:
            if st.button("Mark as Read", key=f"read_{notif['id']}", type="secondary"):
                conn = get_connection()
                conn.cursor().execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notif["id"],))
                conn.commit()
                conn.close()
                st.rerun()
