"""
Order Processing Utilities — create, update, cancel orders,
manage order items, and generate invoices.
"""
import datetime
import sqlite3
from database import get_connection


def create_order(customer_id, cart_items, shipping_address, shipping_city,
                 shipping_state, shipping_pincode, payment_method, notes=""):
    """
    Create a new order from cart items.
    Deducts inventory, creates order + order_items + payment records.

    Args:
        customer_id: Customer's ID
        cart_items: list of dicts with product_id, vendor_id, quantity, unit_price
        shipping_address/city/state/pincode: shipping details
        payment_method: e.g. 'UPI', 'Credit Card'
        notes: optional order notes

    Returns:
        order_id on success, None on failure
    """
    if not cart_items:
        return None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Calculate totals
        subtotal = sum(item["quantity"] * item["unit_price"] for item in cart_items)
        tax_rate = 0.18  # 18% GST
        tax_amount = round(subtotal * tax_rate, 2)
        shipping_amount = 0 if subtotal >= 999 else 49.00  # Free shipping over 999
        net_amount = round(subtotal + tax_amount + shipping_amount, 2)

        # Generate order ID
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        order_id = f"ORD{count + 1:06d}"

        now = datetime.datetime.now().isoformat(timespec="seconds")

        # Insert order
        cursor.execute("""
            INSERT INTO orders (order_id, customer_id, total_amount, tax_amount,
                shipping_amount, discount_amount, net_amount, status,
                shipping_address, shipping_city, shipping_state, shipping_pincode,
                notes, placed_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Placed', ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, customer_id, subtotal, tax_amount, shipping_amount,
              0, net_amount, shipping_address, shipping_city, shipping_state,
              shipping_pincode, notes, now, now))

        # Insert order items
        for item in cart_items:
            total_price = round(item["quantity"] * item["unit_price"], 2)
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, vendor_id, quantity,
                    unit_price, total_price, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Placed')
            """, (order_id, item["product_id"], item["vendor_id"],
                  item["quantity"], item["unit_price"], total_price))

            # Deduct inventory
            cursor.execute("""
                UPDATE inventory SET quantity = quantity - ?, reserved = reserved + ?
                WHERE product_id = ?
            """, (item["quantity"], item["quantity"], item["product_id"]))

        # Create payment record
        cursor.execute("SELECT COUNT(*) FROM payments")
        pay_count = cursor.fetchone()[0]
        payment_id = f"PAY{pay_count + 1:06d}"

        cursor.execute("""
            INSERT INTO payments (payment_id, order_id, amount, method, status, created_at)
            VALUES (?, ?, ?, ?, 'Pending', ?)
        """, (payment_id, order_id, net_amount, payment_method, now))

        # Clear customer's cart
        cursor.execute("DELETE FROM cart WHERE customer_id = ?", (customer_id,))

        # Create commission entries
        vendor_totals = {}
        for item in cart_items:
            vid = item["vendor_id"]
            vendor_totals[vid] = vendor_totals.get(vid, 0) + item["quantity"] * item["unit_price"]

        for vid, amount in vendor_totals.items():
            cursor.execute("SELECT commission_rate FROM vendors WHERE vendor_id = ?", (vid,))
            row = cursor.fetchone()
            rate = row[0] if row else 10.0
            commission = round(amount * rate / 100, 2)
            cursor.execute("""
                INSERT INTO commission_ledger (vendor_id, order_id, order_amount,
                    commission_rate, commission_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'Pending', ?)
            """, (vid, order_id, amount, rate, commission, now))

        conn.commit()
        return order_id

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_customer_orders(customer_id):
    """Return all orders for a customer, most recent first."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM orders WHERE customer_id = ?
        ORDER BY placed_at DESC
    """, (customer_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_order_details(order_id):
    """Return order with items, payment, and shipment info."""
    conn = get_connection()
    cursor = conn.cursor()

    # Order
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    order = cursor.fetchone()
    if not order:
        conn.close()
        return None
    order = dict(order)

    # Items
    cursor.execute("""
        SELECT oi.*, p.name as product_name, v.business_name as vendor_name
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        JOIN vendors v ON oi.vendor_id = v.vendor_id
        WHERE oi.order_id = ?
    """, (order_id,))
    order["items"] = [dict(r) for r in cursor.fetchall()]

    # Payment
    cursor.execute("SELECT * FROM payments WHERE order_id = ?", (order_id,))
    pay = cursor.fetchone()
    order["payment"] = dict(pay) if pay else None

    # Shipment
    cursor.execute("SELECT * FROM shipments WHERE order_id = ?", (order_id,))
    ship = cursor.fetchone()
    order["shipment"] = dict(ship) if ship else None

    conn.close()
    return order


def get_all_orders(status=None, vendor_id=None):
    """Return orders, optionally filtered by status or vendor."""
    conn = get_connection()
    cursor = conn.cursor()

    if vendor_id:
        # Get orders that contain items from this vendor
        sql = """
            SELECT DISTINCT o.*
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE oi.vendor_id = ?
        """
        params = [vendor_id]
        if status:
            sql += " AND o.status = ?"
            params.append(status)
        sql += " ORDER BY o.placed_at DESC"
        cursor.execute(sql, params)
    else:
        sql = "SELECT * FROM orders"
        params = []
        if status:
            sql += " WHERE status = ?"
            params.append(status)
        sql += " ORDER BY placed_at DESC"
        cursor.execute(sql, params)

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def update_order_status(order_id, new_status):
    """Update order status with timestamp."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE orders SET status = ?, updated_at = datetime('now')
        WHERE order_id = ?
    """, (new_status, order_id))

    # Also update order items
    cursor.execute("""
        UPDATE order_items SET status = ?
        WHERE order_id = ?
    """, (new_status, order_id))

    conn.commit()
    conn.close()


def cancel_order(order_id):
    """Cancel an order — restore inventory and mark payment for refund."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get order items
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    items = [dict(r) for r in cursor.fetchall()]

    # Restore inventory
    for item in items:
        cursor.execute("""
            UPDATE inventory SET quantity = quantity + ?, reserved = MAX(0, reserved - ?)
            WHERE product_id = ?
        """, (item["quantity"], item["quantity"], item["product_id"]))

    # Update statuses
    cursor.execute("UPDATE orders SET status = 'Cancelled', updated_at = datetime('now') WHERE order_id = ?", (order_id,))
    cursor.execute("UPDATE order_items SET status = 'Cancelled' WHERE order_id = ?", (order_id,))
    cursor.execute("UPDATE payments SET status = 'Refund Initiated' WHERE order_id = ?", (order_id,))
    cursor.execute("UPDATE commission_ledger SET status = 'Cancelled' WHERE order_id = ?", (order_id,))

    conn.commit()
    conn.close()
