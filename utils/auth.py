"""
Authentication Utilities — User CRUD, password hashing, and audit logging.
"""
import bcrypt
import sqlite3
import datetime
from database import get_connection


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> dict | None:
    """
    Authenticate a user by username and password.

    Returns:
        User dict (id, username, full_name, role, email) or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, password_hash, full_name, role, email, is_active FROM users WHERE username = ?",
        (username,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None
    if not row["is_active"]:
        return None
    if not verify_password(password, row["password_hash"]):
        return None

    # Update last_login
    conn = get_connection()
    conn.execute(
        "UPDATE users SET last_login = ? WHERE id = ?",
        (datetime.datetime.now().isoformat(), row["id"])
    )
    conn.commit()
    conn.close()

    return {
        "user_id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
        "email": row["email"],
    }


def create_user(username: str, password: str, full_name: str, email: str, role: str) -> bool:
    """Create a new user. Returns True on success."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, email, role) VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(password), full_name, email, role)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def update_user(user_id: int, **kwargs) -> bool:
    """
    Update user fields. Pass only the fields to update.
    Supported fields: full_name, email, role, is_active.
    For password updates, use reset_password() instead.
    """
    allowed_fields = {"full_name", "email", "role", "is_active"}
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    if not updates:
        return False

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [user_id]

    conn = get_connection()
    conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


def reset_password(user_id: int, new_password: str) -> bool:
    """Reset a user's password."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user_id)
    )
    conn.commit()
    conn.close()
    return True


def delete_user(user_id: int) -> bool:
    """Delete a user (soft delete — sets is_active=0)."""
    conn = get_connection()
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True


def list_users() -> list[dict]:
    """List all users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, email, role, is_active, created_at, last_login FROM users ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_user_by_id(user_id: int) -> dict | None:
    """Get a single user by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, email, role, is_active, created_at, last_login FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def log_activity(user_id: int, username: str, action: str, details: str = ""):
    """Write an entry to the audit log."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_logs (user_id, username, action, details) VALUES (?, ?, ?, ?)",
        (user_id, username, action, details)
    )
    conn.commit()
    conn.close()


def get_audit_logs(limit: int = 100, offset: int = 0, search: str = "") -> tuple[list[dict], int]:
    """
    Retrieve audit logs with optional search and pagination.

    Returns:
        Tuple of (logs list, total count)
    """
    conn = get_connection()
    cursor = conn.cursor()

    where = ""
    params = []
    if search:
        where = "WHERE username LIKE ? OR action LIKE ? OR details LIKE ?"
        params = [f"%{search}%"] * 3

    cursor.execute(f"SELECT COUNT(*) FROM audit_logs {where}", params)
    total = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT * FROM audit_logs {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows], total
