"""
Wishlist — Customer page for managing saved products.
"""
import streamlit as st
from authentication import check_auth, require_role
from database import get_connection
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — Wishlist", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Wishlist")

CUSTOMER_ID = "CUST00001"

# ──────────────────────────────────────────────
# Page Header
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("favorite", size="2rem", color="#DC3545")}
    <h1 style="color:#1B2A4A;margin:0;">My Wishlist</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Load wishlist items
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT w.id, w.product_id, p.name, p.price, p.mrp, p.discount_pct,
           p.vendor_id, v.business_name as vendor_name, p.status as product_status
    FROM wishlist w
    JOIN products p ON w.product_id = p.product_id
    JOIN vendors v ON p.vendor_id = v.vendor_id
    WHERE w.customer_id = ?
    ORDER BY w.added_at DESC
""", (CUSTOMER_ID,))
items = [dict(r) for r in cursor.fetchall()]
conn.close()

if not items:
    st.markdown(f"""
    <div style="text-align:center;padding:3rem;background:#F8F9FA;border-radius:12px;border:2px dashed #E2E8F0;">
        {render_html_icon("favorite_border", size="4rem", color="#A0AEC0")}
        <h3 style="color:#6C757D;margin-top:1rem;">Your wishlist is empty</h3>
        <p style="color:#A0AEC0;">Save products you like while browsing the shop.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Browse Shop", type="primary"):
        st.switch_page("pages/25_Shop.py")
    st.stop()

st.markdown(f'<div class="section-header">{render_html_icon("favorite", size="18px")} Saved Items ({len(items)})</div>', unsafe_allow_html=True)

cols_per_row = 3
for row_start in range(0, len(items), cols_per_row):
    row_items = items[row_start:row_start + cols_per_row]
    cols = st.columns(cols_per_row)
    for idx, item in enumerate(row_items):
        with cols[idx]:
            discount_html = ""
            if item.get("discount_pct", 0) > 0:
                discount_html = f'<span style="background:#E8F5E9;color:#2E7D32;padding:2px 6px;border-radius:4px;font-size:0.7rem;font-weight:700;">{item["discount_pct"]:.0f}% OFF</span>'

            st.markdown(f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:1.25rem;margin-bottom:0.5rem;">
                <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
                    <span style="font-size:0.7rem;color:#6C757D;">by {item['vendor_name']}</span>
                    {discount_html}
                </div>
                <h4 style="color:#1B2A4A;margin:0.5rem 0;">{item['name']}</h4>
                <div style="display:flex;align-items:baseline;gap:8px;">
                    <span style="font-size:1.1rem;font-weight:700;color:#1B2A4A;">\u20b9{item['price']:,.0f}</span>
                    {"<span style='font-size:0.85rem;color:#A0AEC0;text-decoration:line-through;'>\u20b9" + f"{item['mrp']:,.0f}</span>" if item.get('mrp') and item['mrp'] > item['price'] else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)

            b1, b2 = st.columns(2)
            with b1:
                if st.button("Move to Cart", key=f"w2c_{item['id']}", use_container_width=True, type="primary"):
                    conn = get_connection()
                    c = conn.cursor()
                    # Add to cart
                    c.execute("SELECT id FROM cart WHERE customer_id = ? AND product_id = ?",
                              (CUSTOMER_ID, item["product_id"]))
                    if not c.fetchone():
                        c.execute("INSERT INTO cart (customer_id, product_id, quantity) VALUES (?, ?, 1)",
                                  (CUSTOMER_ID, item["product_id"]))
                    # Remove from wishlist
                    c.execute("DELETE FROM wishlist WHERE id = ?", (item["id"],))
                    conn.commit()
                    conn.close()
                    st.toast(f"Moved **{item['name']}** to cart!", icon=":material/shopping_cart:")
                    st.rerun()
            with b2:
                if st.button("Remove", key=f"wrem_{item['id']}", use_container_width=True):
                    conn = get_connection()
                    conn.cursor().execute("DELETE FROM wishlist WHERE id = ?", (item["id"],))
                    conn.commit()
                    conn.close()
                    st.rerun()
