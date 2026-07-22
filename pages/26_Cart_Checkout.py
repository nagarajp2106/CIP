"""
Cart & Checkout — Customer page for viewing cart, adjusting quantities,
and completing checkout with shipping and payment details.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from database import get_connection
from utils.orders import create_order
from utils.payments import process_payment
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON, PAYMENT_METHODS

st.set_page_config(page_title=f"{APP_NAME} — Cart & Checkout", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Cart & Checkout")

CUSTOMER_ID = "CUST00001"  # Linked to demo customer user

# ──────────────────────────────────────────────
# Page Header
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("shopping_cart", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Cart & Checkout</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Load Cart Items
# ──────────────────────────────────────────────
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT c.id, c.product_id, c.quantity, p.name, p.price, p.mrp,
           p.vendor_id, v.business_name as vendor_name, p.image_url
    FROM cart c
    JOIN products p ON c.product_id = p.product_id
    JOIN vendors v ON p.vendor_id = v.vendor_id
    WHERE c.customer_id = ?
    ORDER BY c.added_at DESC
""", (CUSTOMER_ID,))
cart_items = [dict(r) for r in cursor.fetchall()]
conn.close()

if not cart_items:
    st.markdown(f"""
    <div style="text-align:center;padding:3rem;background:#F8F9FA;border-radius:12px;border:2px dashed #E2E8F0;">
        {render_html_icon("shopping_cart", size="4rem", color="#A0AEC0")}
        <h3 style="color:#6C757D;margin-top:1rem;">Your cart is empty</h3>
        <p style="color:#A0AEC0;">Browse products and add items to your cart.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Browse Shop", type="primary", key="go_shop"):
        st.switch_page("pages/25_Shop.py")
    st.stop()

# ──────────────────────────────────────────────
# Cart Items Display
# ──────────────────────────────────────────────
cart_col, summary_col = st.columns([2, 1])

with cart_col:
    st.markdown(f'<div class="section-header">{render_html_icon("list", size="18px")} Cart Items ({len(cart_items)})</div>', unsafe_allow_html=True)

    for item in cart_items:
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        with c1:
            st.markdown(f"""
            <div style="padding:0.5rem 0;">
                <strong style="color:#1B2A4A;">{item['name']}</strong><br/>
                <span style="color:#6C757D;font-size:0.8rem;">by {item['vendor_name']}</span>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="padding:0.5rem 0;">
                <span style="font-weight:700;color:#1B2A4A;">\u20b9{item['price']:,.0f}</span>
                {"<br/><span style='color:#A0AEC0;font-size:0.8rem;text-decoration:line-through;'>\u20b9" + f"{item['mrp']:,.0f}</span>" if item.get('mrp') and item['mrp'] > item['price'] else ""}
            </div>
            """, unsafe_allow_html=True)
        with c3:
            new_qty = st.number_input(
                "Qty", min_value=1, max_value=10,
                value=item["quantity"],
                key=f"qty_{item['id']}",
                label_visibility="collapsed",
            )
            if new_qty != item["quantity"]:
                conn = get_connection()
                conn.cursor().execute("UPDATE cart SET quantity = ? WHERE id = ?", (new_qty, item["id"]))
                conn.commit()
                conn.close()
                st.rerun()
        with c4:
            if st.button("X", key=f"remove_{item['id']}", type="secondary"):
                conn = get_connection()
                conn.cursor().execute("DELETE FROM cart WHERE id = ?", (item["id"],))
                conn.commit()
                conn.close()
                st.rerun()

        st.markdown('<hr style="margin:0.25rem 0;border-color:#F1F5F9;">', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Order Summary
# ──────────────────────────────────────────────
subtotal = sum(i["price"] * i["quantity"] for i in cart_items)
tax = round(subtotal * 0.18, 2)
shipping = 0 if subtotal >= 999 else 49.00
total = round(subtotal + tax + shipping, 2)

with summary_col:
    st.markdown(f"""
    <div style="background:#F8F9FA;border-radius:12px;padding:1.5rem;border:1px solid #E2E8F0;">
        <h3 style="color:#1B2A4A;margin:0 0 1rem 0;">Order Summary</h3>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
            <span style="color:#6C757D;">Subtotal ({sum(i['quantity'] for i in cart_items)} items)</span>
            <span style="color:#1B2A4A;font-weight:600;">\u20b9{subtotal:,.2f}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
            <span style="color:#6C757D;">GST (18%)</span>
            <span style="color:#1B2A4A;">\u20b9{tax:,.2f}</span>
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.5rem;">
            <span style="color:#6C757D;">Shipping</span>
            <span style="color:{'#28A745' if shipping == 0 else '#1B2A4A'};">{'FREE' if shipping == 0 else f'\u20b9{shipping:,.2f}'}</span>
        </div>
        <hr style="border-color:#E2E8F0;"/>
        <div style="display:flex;justify-content:space-between;">
            <span style="font-weight:700;color:#1B2A4A;font-size:1.1rem;">Total</span>
            <span style="font-weight:700;color:#1B2A4A;font-size:1.1rem;">\u20b9{total:,.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Checkout Form
# ──────────────────────────────────────────────
st.markdown(f'<div class="section-header">{render_html_icon("local_shipping", size="20px")} Shipping & Payment</div>', unsafe_allow_html=True)

with st.form("checkout_form"):
    s1, s2 = st.columns(2)
    with s1:
        st.markdown("**Shipping Address**")
        ship_address = st.text_input("Address", value="123 Main Street", key="ship_addr")
        ship_city = st.text_input("City", value="Bangalore", key="ship_city")
    with s2:
        st.markdown("**&nbsp;**")
        ship_state = st.text_input("State", value="Karnataka", key="ship_state")
        ship_pincode = st.text_input("Pincode", value="560001", key="ship_pin")

    st.markdown("**Payment Method**")
    payment_method = st.selectbox("Choose", PAYMENT_METHODS, key="pay_method")
    notes = st.text_area("Order Notes (optional)", height=60, key="order_notes")

    place_order = st.form_submit_button("Place Order", type="primary", use_container_width=True)

    if place_order:
        if not ship_address or not ship_city or not ship_state or not ship_pincode:
            st.error("Please fill in all shipping details.", icon=":material/error:")
        else:
            # Prepare cart items for order creation
            order_items = [
                {
                    "product_id": item["product_id"],
                    "vendor_id": item["vendor_id"],
                    "quantity": item["quantity"],
                    "unit_price": item["price"],
                }
                for item in cart_items
            ]

            with st.spinner("Processing your order..."):
                order_id = create_order(
                    customer_id=CUSTOMER_ID,
                    cart_items=order_items,
                    shipping_address=ship_address,
                    shipping_city=ship_city,
                    shipping_state=ship_state,
                    shipping_pincode=ship_pincode,
                    payment_method=payment_method,
                    notes=notes,
                )

            if order_id:
                # Process payment
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT payment_id FROM payments WHERE order_id = ?", (order_id,))
                pay_row = cursor.fetchone()
                conn.close()

                if pay_row:
                    result = process_payment(pay_row[0], simulate_success=True)
                    if result["status"] == "success":
                        st.success(f"Order **{order_id}** placed successfully! {result['message']}", icon=":material/check_circle:")
                        st.balloons()
                    else:
                        st.warning(f"Order placed but payment pending: {result['message']}", icon=":material/warning:")
                else:
                    st.success(f"Order **{order_id}** placed!", icon=":material/check_circle:")
                st.rerun()
            else:
                st.error("Failed to create order. Please try again.", icon=":material/error:")
