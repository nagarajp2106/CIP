"""
Category Management — Admin page for managing product categories
with hierarchical parent-child support.
"""
import streamlit as st
import pandas as pd
from authentication import check_auth, require_role
from utils.marketplace import (
    get_all_categories, get_category_tree, create_category,
    update_category, get_next_category_id,
)
from utils.icons import render_html_icon
from database import get_connection
from config import APP_NAME, APP_ICON

st.set_page_config(page_title=f"{APP_NAME} — Category Management", page_icon=APP_ICON, layout="wide")

user = check_auth()
if not user:
    st.switch_page("app.py")
require_role("Category Management")

# ──────────────────────────────────────────────
# Page Header
# ──────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    {render_html_icon("category", size="2rem", color="#1B2A4A")}
    <h1 style="color:#1B2A4A;margin:0;">Category Management</h1>
</div>
<p style="color:#6C757D;margin-top:-0.5rem;">Manage product categories and subcategories.</p>
""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────
# Category Tree View
# ──────────────────────────────────────────────
categories = get_all_categories()
tree = get_category_tree()

# Count products per category
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT category_id, COUNT(*) as cnt FROM products GROUP BY category_id")
product_counts = {r[0]: r[1] for r in cursor.fetchall()}
conn.close()

st.markdown(f'<div class="section-header">{render_html_icon("account_tree", size="20px")} Category Tree</div>', unsafe_allow_html=True)

if tree:
    for cat_id, cat in tree.items():
        count = product_counts.get(cat_id, 0)
        icon = cat.get("icon", "category")
        status_badge = "Active" if cat.get("is_active", 1) else "Inactive"
        badge_color = "#28A745" if status_badge == "Active" else "#DC3545"

        st.markdown(f"""
        <div style="padding:0.75rem 1rem;background:#F8F9FA;border-radius:8px;border-left:4px solid var(--secondary);margin-bottom:0.5rem;display:flex;justify-content:space-between;align-items:center;">
            <div style="display:flex;align-items:center;gap:8px;">
                {render_html_icon(icon, size="20px", color="#1B2A4A")}
                <strong style="color:#1B2A4A;">{cat['name']}</strong>
                <span style="color:#6C757D;font-size:0.85rem;">({cat_id})</span>
                <span style="background:{badge_color};color:white;padding:2px 8px;border-radius:10px;font-size:0.7rem;font-weight:600;">{status_badge}</span>
            </div>
            <span style="color:#6C757D;font-size:0.85rem;">{count} products</span>
        </div>
        """, unsafe_allow_html=True)

        for child in cat.get("children", []):
            child_count = product_counts.get(child["category_id"], 0)
            child_icon = child.get("icon", "subdirectory_arrow_right")
            st.markdown(f"""
            <div style="padding:0.5rem 1rem 0.5rem 2.5rem;background:#FFFFFF;border-radius:6px;border-left:2px solid #E2E8F0;margin-bottom:0.3rem;margin-left:1.5rem;display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:8px;">
                    {render_html_icon(child_icon, size="16px", color="#6C757D")}
                    <span style="color:#1B2A4A;">{child['name']}</span>
                    <span style="color:#A0AEC0;font-size:0.8rem;">({child['category_id']})</span>
                </div>
                <span style="color:#6C757D;font-size:0.8rem;">{child_count} products</span>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No categories found. Add some below.", icon=":material/info:")

st.markdown("---")

# ──────────────────────────────────────────────
# Add Category
# ──────────────────────────────────────────────
tab_add, tab_edit = st.tabs([
    f"{render_html_icon('add_circle', size='16px')} Add Category",
    f"{render_html_icon('edit', size='16px')} Edit Category",
])

with tab_add:
    with st.form("add_category_form"):
        st.markdown("**New Category**")
        c1, c2 = st.columns(2)
        with c1:
            cat_name = st.text_input("Category Name", key="add_cat_name")
            parent_options = ["None (Top Level)"] + [f"{c['category_id']} — {c['name']}" for c in categories if c["parent_id"] is None]
            parent_sel = st.selectbox("Parent Category", parent_options, key="add_cat_parent")
        with c2:
            cat_desc = st.text_input("Description", key="add_cat_desc")
            cat_icon = st.text_input("Icon Name (Material)", value="category", key="add_cat_icon")

        submitted = st.form_submit_button("Create Category", type="primary", use_container_width=True)
        if submitted:
            if not cat_name:
                st.error("Category name is required.", icon=":material/error:")
            else:
                parent_id = None
                if parent_sel != "None (Top Level)":
                    parent_id = parent_sel.split(" — ")[0]
                new_id = get_next_category_id()
                create_category(new_id, cat_name, parent_id, cat_desc, cat_icon)
                st.success(f"Category **{cat_name}** created! (ID: {new_id})", icon=":material/check:")
                st.rerun()

with tab_edit:
    if categories:
        edit_cat = st.selectbox(
            "Select Category",
            options=[f"{c['category_id']} — {c['name']}" for c in categories],
            key="edit_cat_select",
        )
        if edit_cat:
            cid = edit_cat.split(" — ")[0]
            cat_data = next((c for c in categories if c["category_id"] == cid), None)
            if cat_data:
                with st.form("edit_category_form"):
                    e1, e2 = st.columns(2)
                    with e1:
                        e_name = st.text_input("Name", value=cat_data["name"], key="edit_cat_name")
                        e_desc = st.text_input("Description", value=cat_data.get("description", ""), key="edit_cat_desc")
                    with e2:
                        e_icon = st.text_input("Icon", value=cat_data.get("icon", "category"), key="edit_cat_icon")
                        e_active = st.selectbox(
                            "Status", ["Active", "Inactive"],
                            index=0 if cat_data.get("is_active", 1) else 1,
                            key="edit_cat_status",
                        )

                    save = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
                    if save:
                        update_category(
                            cid, name=e_name, description=e_desc,
                            icon=e_icon, is_active=1 if e_active == "Active" else 0,
                        )
                        st.success("Category updated!", icon=":material/check:")
                        st.rerun()
    else:
        st.info("No categories to edit.", icon=":material/info:")

# ──────────────────────────────────────────────
# All Categories Table
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(f'<div class="section-header">{render_html_icon("table_chart", size="20px")} All Categories</div>', unsafe_allow_html=True)

if categories:
    df = pd.DataFrame(categories)
    cols = ["category_id", "name", "parent_id", "description", "icon", "is_active"]
    cols = [c for c in cols if c in df.columns]
    df_show = df[cols].copy()
    df_show["is_active"] = df_show["is_active"].map({1: "Active", 0: "Inactive"})
    df_show.columns = [c.replace("_", " ").title() for c in cols]
    st.dataframe(df_show, use_container_width=True, hide_index=True)
