"""
Mock Payment Gateway — simulates UPI, Credit Card, Debit Card,
Net Banking, and Wallet payments with randomized success/failure.
"""
import random
import datetime
import string
from database import get_connection


def process_payment(payment_id, simulate_success=None):
    """
    Process a pending payment. Simulates gateway with ~90% success rate.

    Args:
        payment_id: The payment record ID
        simulate_success: Override for testing (True/False/None for random)

    Returns:
        dict with status, transaction_ref, message
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
    payment = cursor.fetchone()

    if not payment:
        conn.close()
        return {"status": "error", "message": "Payment not found"}

    payment = dict(payment)

    if payment["status"] not in ("Pending",):
        conn.close()
        return {"status": "error", "message": f"Payment already {payment['status']}"}

    # Simulate payment processing
    if simulate_success is None:
        success = random.random() < 0.9  # 90% success rate
    else:
        success = simulate_success

    now = datetime.datetime.now().isoformat(timespec="seconds")

    if success:
        # Generate a mock transaction reference
        ref = "TXN" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
        cursor.execute("""
            UPDATE payments SET status = 'Completed', transaction_ref = ?, paid_at = ?
            WHERE payment_id = ?
        """, (ref, now, payment_id))

        # Update order status to Confirmed
        cursor.execute("""
            UPDATE orders SET status = 'Confirmed', updated_at = ?
            WHERE order_id = ?
        """, (now, payment["order_id"]))

        conn.commit()
        conn.close()
        return {
            "status": "success",
            "transaction_ref": ref,
            "message": f"Payment of {payment['amount']:.2f} processed successfully via {payment['method']}",
        }
    else:
        cursor.execute("""
            UPDATE payments SET status = 'Failed' WHERE payment_id = ?
        """, (payment_id,))
        conn.commit()
        conn.close()
        return {
            "status": "failed",
            "transaction_ref": None,
            "message": "Payment declined by gateway. Please try again.",
        }


def get_payment_status(payment_id):
    """Get the current status of a payment."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_payment_by_order(order_id):
    """Get payment record for an order."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def initiate_refund(order_id, amount=None, reason="Customer requested refund"):
    """
    Create a refund record linked to the order's payment.

    Returns:
        refund_id on success, None on failure
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get payment
    cursor.execute("SELECT * FROM payments WHERE order_id = ? AND status = 'Completed'", (order_id,))
    payment = cursor.fetchone()
    if not payment:
        conn.close()
        return None

    payment = dict(payment)
    refund_amount = amount if amount else payment["amount"]

    # Generate refund ID
    cursor.execute("SELECT COUNT(*) FROM refunds")
    count = cursor.fetchone()[0]
    refund_id = f"RFD{count + 1:06d}"

    now = datetime.datetime.now().isoformat(timespec="seconds")

    cursor.execute("""
        INSERT INTO refunds (refund_id, order_id, payment_id, amount, reason, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'Requested', ?)
    """, (refund_id, order_id, payment["payment_id"], refund_amount, reason, now))

    # Update payment status
    cursor.execute("UPDATE payments SET status = 'Refund Initiated' WHERE payment_id = ?", (payment["payment_id"],))

    conn.commit()
    conn.close()
    return refund_id


def approve_refund(refund_id):
    """Approve a refund request."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    cursor.execute("""
        UPDATE refunds SET status = 'Approved', approved_at = ?
        WHERE refund_id = ?
    """, (now, refund_id))

    # Update payment
    cursor.execute("SELECT payment_id FROM refunds WHERE refund_id = ?", (refund_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE payments SET status = 'Refunded' WHERE payment_id = ?", (row[0],))

    conn.commit()
    conn.close()
