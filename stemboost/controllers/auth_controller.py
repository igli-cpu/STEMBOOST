from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stemboost.services.interfaces import DataServiceProtocol


class AuthController:
    """Handles login, registration, and session management."""

    def __init__(self, data_service: DataServiceProtocol):
        self.ds = data_service
        self.current_user = None

    def login(self, username, password):
        """Authenticate and set current_user. Returns the user or None."""
        user = self.ds.authenticate(username, password)
        if user:
            self.current_user = user
        return user

    def register(self, username, email, password, name, role, **kwargs):
        """Create a new account. Returns user_id or raises on invalid input."""
        if not username or not username.strip():
            raise ValueError("Username is required.")
        if not name or not name.strip():
            raise ValueError("Name is required.")
        if not email or "@" not in email:
            raise ValueError("A valid email address is required.")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")
        if role not in ("educator", "mentor", "learner"):
            raise ValueError(f"Invalid role: {role!r}")

        user_id = self.ds.create_user(
            username=username, email=email, password=password,
            name=name, role=role, **kwargs)
        return user_id

    def logout(self):
        self.current_user = None
