"""STEMBOOST - Inclusive STEM Training Platform

Entry point for the application. Run with:
    python -m stemboost.main
"""

import tkinter as tk

from stemboost.services.data_service import DataService
from stemboost.services.tts_service import TTSFacade
from stemboost.services.accessibility_service import AccessibilityService
from stemboost.controllers.auth_controller import AuthController
from stemboost.controllers.educator_controller import EducatorController
from stemboost.controllers.mentor_controller import MentorController
from stemboost.controllers.learner_controller import LearnerController
from stemboost.views.login_view import LoginView
from stemboost.views.educator_view import EducatorView
from stemboost.views.mentor_view import MentorView
from stemboost.views.learner_view import LearnerView
from stemboost.data.seed_data import seed


class StemboostApp:
    """Main application controller. Owns the Tk root, services, and
    coordinates navigation between views."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("STEMBOOST")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)

        # Services
        self.ds = DataService()
        self.ds.connect()
        self.tts = TTSFacade.get_instance()
        self.accessibility = AccessibilityService()

        # Seed on first run (if users table is empty)
        self._seed_if_empty()

        # Controllers
        self.auth = AuthController(self.ds)
        self.educator_ctrl = EducatorController(self.ds)
        self.mentor_ctrl = MentorController(self.ds)
        self.learner_ctrl = LearnerController(self.ds)

        # Container for swappable views
        self._current_view = None
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        # Keyboard navigation: Escape goes back to login
        self.root.bind("<Escape>", lambda e: self.show_login())

        # Start with login
        self.show_login()

    def _seed_if_empty(self):
        c = self.ds.conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            seed(self.ds)

    def reset_demo_data(self):
        """Drop and recreate all tables, then re-seed."""
        self.ds.reset_database()
        seed(self.ds)
        self.auth.logout()
        self.show_login()

    def show_login(self):
        self.auth.logout()
        self._switch_view(LoginView(self.container, self))

    def show_dashboard(self, user):
        """Route to the appropriate dashboard based on user role."""
        if user.role == "educator":
            view = EducatorView(self.container, self, user)
        elif user.role == "mentor":
            view = MentorView(self.container, self, user)
        elif user.role == "learner":
            # Apply learner's accessibility preferences
            self.accessibility.update_from_prefs(user.accessibility_prefs)
            view = LearnerView(self.container, self, user)
        else:
            self.show_login()
            return
        self._switch_view(view)

        # Apply accessibility theme after view is packed
        if user.role == "learner":
            self.root.after(100,
                            lambda: self.accessibility.apply_theme(self.root))

    def _switch_view(self, new_view):
        if self._current_view is not None:
            self._current_view.destroy()
        self._current_view = new_view
        self._current_view.pack(fill="both", expand=True)

    def run(self):
        self.root.mainloop()
        self.ds.close()


def main():
    app = StemboostApp()
    app.run()


if __name__ == "__main__":
    main()
