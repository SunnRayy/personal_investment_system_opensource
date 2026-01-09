import os
import hashlib
import secrets
from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id):
        self.id = id


def _hash_password(password: str, salt: str) -> str:
    """Hash password with salt using SHA-256."""
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def verify_user(username: str, password: str) -> bool:
    """
    Verify user credentials against environment variables.

    Set these environment variables:
        WEB_ADMIN_USER: Admin username (default: admin)
        WEB_ADMIN_PASS: Admin password (REQUIRED - no default for security)

    For development, you can set these in your .env file.
    """
    expected_user = os.environ.get('WEB_ADMIN_USER', 'admin')
    expected_pass = os.environ.get('WEB_ADMIN_PASS')

    if not expected_pass:
        # No password configured - reject all logins for security
        import logging
        logging.warning("WEB_ADMIN_PASS not set. Web login disabled for security.")
        return False

    return username == expected_user and password == expected_pass


def load_user(user_id: str) -> User | None:
    """Load user by ID."""
    # Allow demo user in demo mode
    from src.web_app.system_state import is_demo_mode
    if user_id == 'demo' and is_demo_mode():
        return User(user_id)

    expected_user = os.environ.get('WEB_ADMIN_USER', 'admin')
    if user_id == expected_user:
        return User(user_id)
    return None
