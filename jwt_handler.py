"""
JWT Token Handler for Authentication
Handles creation, validation, and refresh of JWT tokens.
"""
import jwt
import datetime
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS


def create_token(user_id: int, username: str, role: str, full_name: str) -> str:
    """
    Create a JWT token with user claims.

    Args:
        user_id: Database user ID
        username: Login username
        role: User role string
        full_name: Display name

    Returns:
        Encoded JWT token string
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "full_name": full_name,
        "iat": datetime.datetime.utcnow(),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def validate_token(token: str) -> dict | None:
    """
    Validate a JWT token and return the decoded payload.

    Args:
        token: Encoded JWT token string

    Returns:
        Decoded payload dict or None if invalid/expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def refresh_token(token: str) -> str | None:
    """
    Refresh a JWT token if it's still valid (extends expiry).

    Args:
        token: Current valid JWT token

    Returns:
        New JWT token string or None if current token is invalid
    """
    payload = validate_token(token)
    if payload is None:
        return None
    return create_token(
        user_id=payload["user_id"],
        username=payload["username"],
        role=payload["role"],
        full_name=payload["full_name"],
    )
