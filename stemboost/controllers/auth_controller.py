from stemboost.services.data_service import DataService


class AuthController:
    """Handles login, registration, and session management."""

    def __init__(self, data_service):
        self.ds = data_service
        self.current_user = None

    def login(self, username, password):
        """Authenticate and set current_user. Returns the user or None."""
        user = self.ds.authenticate(username, password)
        if user:
            self.current_user = user
        return user

    def register(self, username, email, password, name, role, **kwargs):
        """Create a new account. Returns user_id or raises on duplicate."""
        user_id = self.ds.create_user(
            username=username, email=email, password=password,
            name=name, role=role, **kwargs)
        return user_id

    def logout(self):
        self.current_user = None
