"""
Reviews & Ratings — Customer reviews and admin moderation.
"""
import streamlit as st
import pandas as pd
import datetime
from authentication import check_auth, require_role
from database import get_connection
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — Reviews", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Reviews & Ratings")

role = user["role"]
CUSTOMER_ID = "CUST00001"

st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("rate_review", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Reviews & Ratings</h1>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# Load reviews
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT r.*, p.name as product_name, c.name as customer_name
    FROM reviews r
    JOIN products p ON r.product_id = p.product_id
    LEFT JOIN customers c ON r.customer_id = c.customer_id
    ORDER BY r.created_at DESC
""")
reviews = [dict(r) for r in cursor.fetchall()]
conn.close()

# KPIs
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f'<div class="kpi-card blue animate-in"><div class="kpi-value">{len(reviews)}</div><div class="kpi-label">Total Reviews</div></div>', unsafe_allow_html=True)
with k2:
    avg = sum(r["rating"] for r in reviews) / len(reviews) if reviews else 0
    st.markdown(f'<div class="kpi-card gold animate-in"><div class="kpi-value">{avg:.1f}</div><div class="kpi-label">Avg Rating</div></div>', unsafe_allow_html=True)
with k3:
    pending = sum(1 for r in reviews if not r["is_approved"])
    st.markdown(f'<div class="kpi-card green animate-in"><div class="kpi-value">{pending}</div><div class="kpi-label">Pending Moderation</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Customer: Write a review
if role == "customer":
    st.markdown(f'<div class="section-header">{render_html_icon("edit", size="18px")} Write a Review</div>', unsafe_allow_html=True)

    # Get products the customer has ordered
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT p.product_id, p.name
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE o.customer_id = ? AND o.status = 'Delivered'
    """, (CUSTOMER_ID,))
    reviewable = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if reviewable:
        with st.form("review_form"):
            sel_prod = st.selectbox("Product", [f"{p['product_id']} — {p['name']}" for p in reviewable])
            rating = st.select_slider("Rating", options=[1, 2, 3, 4, 5], value=5)
            title = st.text_input("Review Title", placeholder="Great product!")
            comment = st.text_area("Your Review", height=100)
            if st.form_submit_button("Submit Review", type="primary", use_container_width=True):
                pid = sel_prod.split(" — ")[0]
                conn = get_connection()
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM reviews")
                cnt = c.fetchone()[0]
                rid = f"REV{cnt+1:06d}"
                c.execute("""
                    INSERT INTO reviews (review_id, product_id, customer_id, rating, title, comment, is_approved)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (rid, pid, CUSTOMER_ID, rating, title, comment))
                conn.commit()
                conn.close()
                st.success("Review submitted! It will appear after moderation.", icon=":material/check:")
                st.rerun()
    else:
        st.caption("No delivered orders to review. Shop and get products delivered first!")

st.markdown("---")

# Display reviews
st.markdown(f'<div class="section-header">{render_html_icon("reviews", size="18px")} All Reviews</div>', unsafe_allow_html=True)

if not reviews:
    st.info("No reviews yet.", icon=":material/info:")
else:
    for rev in reviews:
        stars = "".join(["<span style='color:#FFB800;'>&#9733;</span>" if i < rev["rating"] else "<span style='color:#E2E8F0;'>&#9733;</span>" for i in range(5)])
        approved_badge = '<span style="background:#E8F5E9;color:#2E7D32;padding:2px 8px;border-radius:10px;font-size:0.7rem;">Approved</span>' if rev["is_approved"] else '<span style="background:#FFF3E0;color:#E65100;padding:2px 8px;border-radius:10px;font-size:0.7rem;">Pending</span>'

        st.markdown(f"""
        <div style="background:#F8F9FA;border-radius:8px;padding:1rem;margin-bottom:0.75rem;border-left:4px solid {'#28A745' if rev['is_approved'] else '#FFC107'};">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem;">
                <div>
                    <strong style="color:#1B2A4A;">{rev.get('product_name', rev['product_id'])}</strong>
                    <span style="color:#6C757D;font-size:0.8rem;margin-left:8px;">by {rev.get('customer_name', rev['customer_id'])}</span>
                </div>
                <div>{approved_badge}</div>
            </div>
            <div style="margin-bottom:0.3rem;">{stars}</div>
            {"<strong style='color:#1B2A4A;'>" + rev.get('title', '') + "</strong><br/>" if rev.get('title') else ""}
            <p style="color:#6C757D;font-size:0.9rem;margin:0.25rem 0 0 0;">{rev.get('comment', '')}</p>
        </div>
        """, unsafe_allow_html=True)

        # Admin moderation
        if role == "admin" and not rev["is_approved"]:
            c1, c2 = st.columns([1, 5])
            with c1:
                if st.button("Approve", key=f"app_rev_{rev['review_id']}", type="primary"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("UPDATE reviews SET is_approved = 1 WHERE review_id = ?", (rev["review_id"],))
                    # Update product rating
                    c.execute("SELECT AVG(rating) as avg_r, COUNT(*) as cnt FROM reviews WHERE product_id = ? AND is_approved = 1", (rev["product_id"],))
                    row = c.fetchone()
                    if row:
                        c.execute("UPDATE products SET rating_avg = ?, rating_count = ? WHERE product_id = ?",
                                  (row[0] or 0, row[1] or 0, rev["product_id"]))
                    conn.commit()
                    conn.close()
                    st.rerun()
