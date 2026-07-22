"""
Notification Service — pure stubs (log-only) for email, SMS,
and in-app notifications.
"""
import logging
import datetime
from database import get_connection

logger = logging.getLogger(__name__)


def send_notification(user_id, title, message, notif_type="info"):
    """
    Insert a notification record into the notifications table.

    Args:
        user_id: The target user's ID
        title: Notification title
        message: Notification body
        notif_type: 'info', 'success', 'warning', 'error', 'order'
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (user_id, title, message, type)
        VALUES (?, ?, ?, ?)
    """, (user_id, title, message, notif_type))
    conn.commit()
    conn.close()
    logger.info(f"[NOTIFICATION] user_id={user_id} | {notif_type} | {title}")


def send_email_stub(to_email, subject, body):
    """
    Stub: Log email (does NOT actually send).
    Replace with real SMTP in production.
    """
    logger.info(f"[EMAIL STUB] To: {to_email} | Subject: {subject} | Body: {body[:100]}...")


def send_sms_stub(phone, message):
    """
    Stub: Log SMS (does NOT actually send).
    Replace with real SMS gateway in production.
    """
    logger.info(f"[SMS STUB] To: {phone} | Message: {message[:100]}...")


def notify_order_placed(user_id, order_id, amount):
    """Convenience: send order placed notification."""
    send_notification(
        user_id,
        "Order Placed Successfully",
        f"Your order {order_id} for \u20b9{amount:,.2f} has been placed.",
        "order",
    )


def notify_order_shipped(user_id, order_id, tracking_number=""):
    """Convenience: send order shipped notification."""
    msg = f"Your order {order_id} has been shipped."
    if tracking_number:
        msg += f" Tracking: {tracking_number}"
    send_notification(user_id, "Order Shipped", msg, "order")


def notify_vendor_approved(user_id, business_name):
    """Convenience: notify vendor their account was approved."""
    send_notification(
        user_id,
        "Vendor Account Approved",
        f"Congratulations! Your vendor account '{business_name}' has been approved.",
        "success",
    )


def notify_low_stock(user_id, product_name, quantity):
    """Convenience: low stock alert."""
    send_notification(
        user_id,
        "Low Stock Alert",
        f"{product_name} has only {quantity} units remaining.",
        "warning",
    )
