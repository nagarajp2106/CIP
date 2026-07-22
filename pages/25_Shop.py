"""
Shop — Customer-facing product browsing with category filters,
search, price range, and add-to-cart/wishlist functionality.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from utils.marketplace import (
    search_products, get_all_categories, get_product_stock,
    get_category_tree,
)
from database import get_connection
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — Shop", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Shop")

# ──────────────────────────────────────────────
# Page Header
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("shopping_bag", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Shop</h1>
</div>
<p style="color:#6C757D;margin-top:-0.5rem;">Browse products from verified marketplace vendors.</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Filters Sidebar (using columns)
# ──────────────────────────────────────────────
filter_col, products_col = st.columns([1, 3])

with filter_col:
    st.markdown(f'<div class="section-header">{render_html_icon("filter_list", size="18px")} Filters</div>', unsafe_allow_html=True)

    search_query = st.text_input("Search Products", placeholder="Laptop, shoes...", key="shop_search")

    categories = get_all_categories(active_only=True)
    top_cats = [c for c in categories if c["parent_id"] is None]
    cat_options = ["All Categories"] + [c["name"] for c in top_cats]
    selected_cat = st.selectbox("Category", cat_options, key="shop_cat")

    price_range = st.slider("Price Range", 0, 200000, (0, 200000), step=500, key="shop_price")

    min_rating = st.select_slider("Min Rating", options=[0, 1, 2, 3, 4, 5], value=0, key="shop_rating")

# Resolve category filter
cat_id_filter = None
if selected_cat != "All Categories":
    for c in top_cats:
        if c["name"] == selected_cat:
            cat_id_filter = c["category_id"]
            break

# Fetch products
products = search_products(
    query_text=search_query if search_query else None,
    min_price=price_range[0] if price_range[0] > 0 else None,
    max_price=price_range[1] if price_range[1] < 200000 else None,
    category_id=cat_id_filter,
    min_rating=min_rating if min_rating > 0 else None,
)

with products_col:
    st.markdown(f'<div class="section-header">{render_html_icon("grid_view", size="18px")} Products ({len(products)} found)</div>', unsafe_allow_html=True)

    if not products:
        st.info("No products match your filters. Try adjusting your search criteria.", icon=":material/search_off:")
    else:
        # Display products in a 3-column grid
        cols_per_row = 3
        for row_start in range(0, len(products), cols_per_row):
            row_products = products[row_start:row_start + cols_per_row]
            cols = st.columns(cols_per_row)

            for idx, prod in enumerate(row_products):
                with cols[idx]:
                    stock = get_product_stock(prod["product_id"])
                    stock_badge = f'<span style="color:#28A745;font-size:0.75rem;font-weight:600;">In Stock ({stock})</span>' if stock > 0 else '<span style="color:#DC3545;font-size:0.75rem;font-weight:600;">Out of Stock</span>'

                    discount_html = ""
                    if prod.get("discount_pct", 0) > 0:
                        discount_html = f'<span style="background:#E8F5E9;color:#2E7D32;padding:2px 6px;border-radius:4px;font-size:0.7rem;font-weight:700;">{prod["discount_pct"]:.0f}% OFF</span>'

                    stars = "".join(["★" if i < int(prod.get("rating_avg", 0)) else "☆" for i in range(5)])

                    st.markdown(f"""
                    <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;padding:1.25rem;margin-bottom:1rem;transition:all 0.2s ease;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.5rem;">
                            <span style="font-size:0.7rem;color:#6C757D;background:#F1F5F9;padding:2px 8px;border-radius:4px;">{prod.get("category_name", "")}</span>
                            {discount_html}
                        </div>
                        <h4 style="color:#1B2A4A;margin:0.5rem 0 0.25rem 0;font-size:1rem;line-height:1.3;">{prod["name"]}</h4>
                        <p style="color:#6C757D;font-size:0.8rem;margin:0 0 0.5rem 0;line-height:1.4;min-height:36px;">{(prod.get("description", "") or "")[:80]}...</p>
                        <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:0.4rem;">
                            <span style="font-size:1.2rem;font-weight:700;color:#1B2A4A;">\u20b9{prod["price"]:,.0f}</span>
                            {"<span style='font-size:0.85rem;color:#A0AEC0;text-decoration:line-through;'>\u20b9" + f"{prod.get('mrp', 0):,.0f}</span>" if prod.get("mrp") and prod["mrp"] > prod["price"] else ""}
                        </div>
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="color:#FFB800;font-size:0.9rem;">{stars}</span>
                            {stock_badge}
                        </div>
                        <div style="font-size:0.75rem;color:#A0AEC0;margin-top:0.4rem;">by {prod.get("vendor_name", "Unknown")}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Action buttons (only for customers)
                    if user["role"] == "customer" and stock > 0:
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("Add to Cart", key=f"cart_{prod['product_id']}", use_container_width=True, type="primary"):
                                conn = get_connection()
                                cursor = conn.cursor()
                                # Check if already in cart
                                cursor.execute("SELECT id, quantity FROM cart WHERE customer_id = ? AND product_id = ?",
                                             ("CUST00001", prod["product_id"]))
                                existing = cursor.fetchone()
                                if existing:
                                    cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE id = ?", (existing[0],))
                                else:
                                    cursor.execute("INSERT INTO cart (customer_id, product_id, quantity) VALUES (?, ?, 1)",
                                                 ("CUST00001", prod["product_id"]))
                                conn.commit()
                                conn.close()
                                st.toast(f"Added **{prod['name']}** to cart!", icon=":material/shopping_cart:")
                        with btn_col2:
                            if st.button("Wishlist", key=f"wish_{prod['product_id']}", use_container_width=True):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("SELECT id FROM wishlist WHERE customer_id = ? AND product_id = ?",
                                             ("CUST00001", prod["product_id"]))
                                if not cursor.fetchone():
                                    cursor.execute("INSERT INTO wishlist (customer_id, product_id) VALUES (?, ?)",
                                                 ("CUST00001", prod["product_id"]))
                                    conn.commit()
                                    st.toast(f"Added **{prod['name']}** to wishlist!", icon=":material/favorite:")
                                else:
                                    st.toast("Already in wishlist.", icon=":material/info:")
                                conn.close()
