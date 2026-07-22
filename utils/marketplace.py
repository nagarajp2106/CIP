"""
Marketplace Utilities — shared helper functions for vendor, product,
category, and inventory operations.
"""
import sqlite3
import datetime
from database import get_connection


# ──────────────────────────────────────────────
# Vendor Helpers
# ──────────────────────────────────────────────

def get_all_vendors(status_filter=None):
    """Return all vendors, optionally filtered by status."""
    conn = get_connection()
    query = "SELECT * FROM vendors"
    params = []
    if status_filter:
        query += " WHERE status = ?"
        params.append(status_filter)
    query += " ORDER BY created_at DESC"
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_vendor_by_id(vendor_id):
    """Return a single vendor dict by vendor_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendors WHERE vendor_id = ?", (vendor_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_vendor_by_user_id(user_id):
    """Return the vendor record linked to the given users.id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vendors WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_vendor_status(vendor_id, new_status):
    """Update vendor status (Active / Suspended / Pending)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE vendors SET status = ?, updated_at = datetime('now')
        WHERE vendor_id = ?
    """, (new_status, vendor_id))
    conn.commit()
    conn.close()


def update_vendor_commission(vendor_id, rate):
    """Update vendor commission rate."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE vendors SET commission_rate = ?, updated_at = datetime('now')
        WHERE vendor_id = ?
    """, (rate, vendor_id))
    conn.commit()
    conn.close()


def update_vendor_profile(vendor_id, **kwargs):
    """Update vendor profile fields. Accepts any column as keyword arg."""
    if not kwargs:
        return
    allowed = {
        "business_name", "owner_name", "email", "phone",
        "gst_number", "address", "city", "state",
    }
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    fields["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [vendor_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE vendors SET {set_clause} WHERE vendor_id = ?", values)
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# Category Helpers
# ──────────────────────────────────────────────

def get_all_categories(active_only=False):
    """Return all categories as a list of dicts."""
    conn = get_connection()
    query = "SELECT * FROM categories"
    if active_only:
        query += " WHERE is_active = 1"
    query += " ORDER BY name"
    cursor = conn.cursor()
    cursor.execute(query)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_category_tree():
    """Return categories grouped as a parent → children dict."""
    cats = get_all_categories(active_only=True)
    tree = {}
    children_map = {}
    for c in cats:
        if c["parent_id"] is None:
            tree[c["category_id"]] = {**c, "children": []}
        else:
            children_map.setdefault(c["parent_id"], []).append(c)
    for pid, kids in children_map.items():
        if pid in tree:
            tree[pid]["children"] = kids
    return tree


def create_category(category_id, name, parent_id=None, description="", icon="category"):
    """Insert a new category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO categories (category_id, name, parent_id, description, icon)
        VALUES (?, ?, ?, ?, ?)
    """, (category_id, name, parent_id, description, icon))
    conn.commit()
    conn.close()


def update_category(category_id, **kwargs):
    """Update category fields."""
    allowed = {"name", "parent_id", "description", "icon", "is_active"}
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [category_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE categories SET {set_clause} WHERE category_id = ?", values)
    conn.commit()
    conn.close()


def get_next_category_id():
    """Generate the next sequential category ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category_id FROM categories ORDER BY category_id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        num = int(row[0].replace("CAT", "")) + 1
    else:
        num = 1
    return f"CAT{num:03d}"


# ──────────────────────────────────────────────
# Product Helpers
# ──────────────────────────────────────────────

def get_all_products(vendor_id=None, category_id=None, status=None, search=None):
    """Return products with optional filters."""
    conn = get_connection()
    query = """
        SELECT p.*, v.business_name as vendor_name, c.name as category_name
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE 1=1
    """
    params = []
    if vendor_id:
        query += " AND p.vendor_id = ?"
        params.append(vendor_id)
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if status:
        query += " AND p.status = ?"
        params.append(status)
    if search:
        query += " AND (p.name LIKE ? OR p.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY p.created_at DESC"
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_product_by_id(product_id):
    """Return a single product dict with vendor and category info."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, v.business_name as vendor_name, c.name as category_name
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE p.product_id = ?
    """, (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_product(product_id, vendor_id, category_id, name, description,
                   price, mrp=None, discount_pct=0, sku=None, image_url=None, status="Active"):
    """Insert a new product."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (product_id, vendor_id, category_id, name, description,
            price, mrp, discount_pct, sku, image_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (product_id, vendor_id, category_id, name, description,
          price, mrp, discount_pct, sku, image_url, status))
    conn.commit()
    conn.close()


def update_product(product_id, **kwargs):
    """Update product fields."""
    allowed = {
        "category_id", "name", "description", "price", "mrp",
        "discount_pct", "sku", "image_url", "status",
    }
    fields = {k: v for k, v in kwargs.items() if k in allowed}
    if not fields:
        return
    fields["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [product_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE products SET {set_clause} WHERE product_id = ?", values)
    conn.commit()
    conn.close()


def delete_product(product_id):
    """Soft-delete a product by setting status to Discontinued."""
    update_product(product_id, status="Discontinued")


def get_next_product_id():
    """Generate the next sequential product ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id FROM products ORDER BY product_id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        num = int(row[0].replace("PRD", "")) + 1
    else:
        num = 1
    return f"PRD{num:05d}"


# ──────────────────────────────────────────────
# Inventory Helpers
# ──────────────────────────────────────────────

def get_product_stock(product_id):
    """Return total available stock (quantity - reserved) for a product."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(SUM(quantity - reserved), 0) as available
        FROM inventory WHERE product_id = ?
    """, (product_id,))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_inventory_for_vendor(vendor_id):
    """Return inventory rows for all products belonging to a vendor."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*, p.name as product_name, p.sku, w.name as warehouse_name
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN warehouses w ON i.warehouse_id = w.warehouse_id
        WHERE p.vendor_id = ?
        ORDER BY p.name
    """, (vendor_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def update_inventory(product_id, warehouse_id, quantity=None, reserved=None, reorder_level=None):
    """Update inventory fields for a specific product-warehouse combo."""
    fields = {}
    if quantity is not None:
        fields["quantity"] = quantity
    if reserved is not None:
        fields["reserved"] = reserved
    if reorder_level is not None:
        fields["reorder_level"] = reorder_level
    if not fields:
        return
    fields["last_restocked"] = datetime.datetime.now().isoformat(timespec="seconds")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [product_id, warehouse_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE inventory SET {set_clause} WHERE product_id = ? AND warehouse_id = ?",
        values
    )
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# Commission Helpers
# ──────────────────────────────────────────────

def calculate_commission(order_amount, commission_rate):
    """Calculate the commission amount."""
    return round(order_amount * commission_rate / 100, 2)


def get_vendor_commissions(vendor_id):
    """Return commission ledger entries for a vendor."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM commission_ledger
        WHERE vendor_id = ?
        ORDER BY created_at DESC
    """, (vendor_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


# ──────────────────────────────────────────────
# Search
# ──────────────────────────────────────────────

def search_products(query_text, min_price=None, max_price=None,
                    category_id=None, min_rating=None):
    """Full-text product search with optional price/category/rating filters."""
    conn = get_connection()
    sql = """
        SELECT p.*, v.business_name as vendor_name, c.name as category_name
        FROM products p
        LEFT JOIN vendors v ON p.vendor_id = v.vendor_id
        LEFT JOIN categories c ON p.category_id = c.category_id
        WHERE p.status = 'Active'
          AND v.status = 'Active'
    """
    params = []
    if query_text:
        sql += " AND (p.name LIKE ? OR p.description LIKE ? OR c.name LIKE ?)"
        like = f"%{query_text}%"
        params.extend([like, like, like])
    if min_price is not None:
        sql += " AND p.price >= ?"
        params.append(min_price)
    if max_price is not None:
        sql += " AND p.price <= ?"
        params.append(max_price)
    if category_id:
        sql += " AND (p.category_id = ? OR c.parent_id = ?)"
        params.extend([category_id, category_id])
    if min_rating is not None:
        sql += " AND p.rating_avg >= ?"
        params.append(min_rating)
    sql += " ORDER BY p.rating_avg DESC, p.name"
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
