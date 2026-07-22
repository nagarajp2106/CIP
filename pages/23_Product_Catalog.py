"""
Product Catalog — Vendor page for managing their own products.
Admin sees all products.
"""
import streamlit as st
import pandas as pd
import os
from authentication import check_auth, require_role
from utils.marketplace import (
    get_all_products, get_product_by_id, create_product, update_product,
    delete_product, get_next_product_id, get_all_categories,
    get_vendor_by_user_id, get_product_stock,
)
from utils.icons import render_html_icon
from config import APP_NAME, APP_ICON, UPLOAD_DIR

st.set_page_config(page_title=f"{APP_NAME} — Product Catalog", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Product Catalog")

# Determine vendor context
role = user["role"]
vendor = None
vendor_id_filter = None
if role == "vendor":
    vendor = get_vendor_by_user_id(user["user_id"])
    if not vendor:
        st.error("Your vendor profile is not set up. Contact an administrator.", icon=":material/error:")
        st.stop()
    if vendor["status"] != "Active":
        st.warning(f"Your vendor account is **{vendor['status']}**. You cannot manage products until approved.", icon=":material/warning:")
        st.stop()
    vendor_id_filter = vendor["vendor_id"]

# ──────────────────────────────────────────────
# Page Header
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("inventory_2", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Product Catalog</h1>
</div>
<p style="color:#6C757D;margin-top:-0.5rem;">
    {"Manage your product listings." if role == "vendor" else "View and manage all marketplace products."}
</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Filters
# ──────────────────────────────────────────────
categories = get_all_categories(active_only=True)
cat_options = {c["category_id"]: c["name"] for c in categories}

f1, f2, f3 = st.columns([2, 2, 6])
with f1:
    cat_filter = st.selectbox("Category", ["All"] + list(cat_options.values()), key="prod_cat_filter")
with f2:
    status_filter = st.selectbox("Status", ["All", "Active", "Draft", "Discontinued"], key="prod_status_filter")

# Resolve category_id from name
cat_id = None
if cat_filter != "All":
    for cid, cname in cat_options.items():
        if cname == cat_filter:
            cat_id = cid
            break

status_val = None if status_filter == "All" else status_filter

products = get_all_products(
    vendor_id=vendor_id_filter,
    category_id=cat_id,
    status=status_val,
)

# ──────────────────────────────────────────────
# KPI Cards
# ──────────────────────────────────────────────
all_prods = get_all_products(vendor_id=vendor_id_filter)
active_count = sum(1 for p in all_prods if p["status"] == "Active")
draft_count = sum(1 for p in all_prods if p["status"] == "Draft")

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(f"""
    <div class="kpi-card blue animate-in">
        <div class="kpi-icon" style="color:var(--secondary);">{render_html_icon("inventory_2", size="2.5rem")}</div>
        <div class="kpi-value">{len(all_prods)}</div>
        <div class="kpi-label">Total Products</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card green animate-in">
        <div class="kpi-icon" style="color:var(--success);">{render_html_icon("check_circle", size="2.5rem")}</div>
        <div class="kpi-value">{active_count}</div>
        <div class="kpi-label">Active</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class="kpi-card gold animate-in">
        <div class="kpi-icon" style="color:var(--accent);">{render_html_icon("edit_note", size="2.5rem")}</div>
        <div class="kpi-value">{draft_count}</div>
        <div class="kpi-label">Draft</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Product Table
# ──────────────────────────────────────────────
if not products:
    st.info("No products found.", icon=":material/info:")
else:
    st.markdown(f'<div class="section-header">{render_html_icon("list", size="20px")} Products ({len(products)})</div>', unsafe_allow_html=True)

    df = pd.DataFrame(products)
    cols = ["product_id", "name", "vendor_name", "category_name", "price", "mrp",
            "discount_pct", "status", "rating_avg"]
    cols = [c for c in cols if c in df.columns]
    df_show = df[cols].copy()
    df_show.columns = [c.replace("_", " ").title() for c in cols]
    st.dataframe(df_show, use_container_width=True, hide_index=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Add / Edit Product (Vendor or Admin)
# ──────────────────────────────────────────────
tab_add, tab_edit = st.tabs([
    f"{render_html_icon('add_circle', size='16px')} Add Product",
    f"{render_html_icon('edit', size='16px')} Edit Product",
])

with tab_add:
    with st.form("add_product_form"):
        st.markdown("**New Product**")
        a1, a2 = st.columns(2)
        with a1:
            prod_name = st.text_input("Product Name", key="add_name")
            prod_desc = st.text_area("Description", key="add_desc", height=100)
            prod_cat = st.selectbox("Category", list(cat_options.values()), key="add_cat")
        with a2:
            prod_price = st.number_input("Selling Price", min_value=0.01, value=999.0, step=1.0, key="add_price")
            prod_mrp = st.number_input("MRP", min_value=0.01, value=1299.0, step=1.0, key="add_mrp")
            prod_sku = st.text_input("SKU", key="add_sku")
            prod_status = st.selectbox("Status", ["Active", "Draft"], key="add_status")

        submitted = st.form_submit_button("Add Product", type="primary", use_container_width=True)
        if submitted:
            if not prod_name:
                st.error("Product name is required.", icon=":material/error:")
            else:
                cat_id_sel = None
                for cid, cname in cat_options.items():
                    if cname == prod_cat:
                        cat_id_sel = cid
                        break
                discount = round((prod_mrp - prod_price) / prod_mrp * 100, 1) if prod_mrp > 0 else 0
                vid = vendor_id_filter if vendor_id_filter else "VND00001"
                new_pid = get_next_product_id()
                create_product(
                    product_id=new_pid, vendor_id=vid, category_id=cat_id_sel,
                    name=prod_name, description=prod_desc, price=prod_price,
                    mrp=prod_mrp, discount_pct=discount, sku=prod_sku,
                    status=prod_status,
                )
                st.success(f"Product **{prod_name}** added! (ID: {new_pid})", icon=":material/check:")
                st.rerun()

with tab_edit:
    if products:
        edit_select = st.selectbox(
            "Select Product",
            options=[f"{p['product_id']} — {p['name']}" for p in products],
            key="edit_prod_select",
        )
        if edit_select:
            pid = edit_select.split(" — ")[0]
            prod = get_product_by_id(pid)
            if prod:
                with st.form("edit_product_form"):
                    e1, e2 = st.columns(2)
                    with e1:
                        e_name = st.text_input("Name", value=prod["name"], key="edit_name")
                        e_desc = st.text_area("Description", value=prod.get("description", ""), key="edit_desc", height=100)
                        current_cat_names = list(cat_options.values())
                        current_cat_idx = 0
                        if prod.get("category_name") in current_cat_names:
                            current_cat_idx = current_cat_names.index(prod["category_name"])
                        e_cat = st.selectbox("Category", current_cat_names, index=current_cat_idx, key="edit_cat")
                    with e2:
                        e_price = st.number_input("Selling Price", min_value=0.01, value=float(prod["price"]), step=1.0, key="edit_price")
                        e_mrp = st.number_input("MRP", min_value=0.01, value=float(prod.get("mrp") or prod["price"]), step=1.0, key="edit_mrp")
                        e_sku = st.text_input("SKU", value=prod.get("sku", ""), key="edit_sku")
                        e_status = st.selectbox(
                            "Status", ["Active", "Draft", "Discontinued"],
                            index=["Active", "Draft", "Discontinued"].index(prod["status"]) if prod["status"] in ["Active", "Draft", "Discontinued"] else 0,
                            key="edit_status",
                        )

                    col_save, col_delete = st.columns(2)
                    with col_save:
                        save_btn = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                    with col_delete:
                        del_btn = st.form_submit_button("Discontinue Product", use_container_width=True)

                    if save_btn:
                        cat_id_ed = None
                        for cid, cname in cat_options.items():
                            if cname == e_cat:
                                cat_id_ed = cid
                                break
                        discount = round((e_mrp - e_price) / e_mrp * 100, 1) if e_mrp > 0 else 0
                        update_product(
                            pid, name=e_name, description=e_desc, category_id=cat_id_ed,
                            price=e_price, mrp=e_mrp, discount_pct=discount,
                            sku=e_sku, status=e_status,
                        )
                        st.success("Product updated!", icon=":material/check:")
                        st.rerun()

                    if del_btn:
                        delete_product(pid)
                        st.warning(f"Product {pid} marked as Discontinued.", icon=":material/warning:")
                        st.rerun()
    else:
        st.info("No products available to edit.", icon=":material/info:")
