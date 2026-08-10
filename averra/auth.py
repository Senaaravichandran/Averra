"""Authentication boundary ready for credentials supplied at deployment."""

from functools import wraps

from flask import current_app, jsonify, request, session
from werkzeug.security import check_password_hash


def configured() -> bool:
    return bool(current_app.config.get("ADMIN_EMAIL") and current_app.config.get("ADMIN_PASSWORD_HASH"))


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_app.config.get("AUTH_REQUIRED"):
            return view(*args, **kwargs)
        if session.get("admin_authenticated"):
            return view(*args, **kwargs)
        return jsonify({"error": "Authentication required.", "code": "AUTH_REQUIRED"}), 401
    return wrapped


def login(email: str, password: str) -> bool:
    expected_email = current_app.config.get("ADMIN_EMAIL", "")
    password_hash = current_app.config.get("ADMIN_PASSWORD_HASH", "")
    if expected_email and password_hash and email.casefold() == expected_email.casefold() and check_password_hash(password_hash, password):
        session["admin_authenticated"] = True
        session["admin_email"] = expected_email
        return True
    return False

