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
from stemboost.views.view_context import ViewContext
from stemboost.data.seed_data import seed


class StemboostApp:
    """Main application controller. Owns the Tk root, services, and
    coordinates navigation between views."""

    # Registry: maps role names to view classes (Open/Closed Principle).
    # Adding a new role = adding one entry here, no show_dashboard changes.
    _dashboard_registry = {
        "educator": EducatorView,
        "mentor": MentorView,
        "learner": LearnerView,
    }

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("STEMBOOST")
        self.root.geometry("1920x1200")
        self.root.minsize(800, 600)

        # Services
        self.ds = DataService()
        self.ds.connect()
        self.tts = TTSFacade.get_instance()
        self.tts.attach_to_root(self.root)
        self.accessibility = AccessibilityService()

        # Seed on first run (if users table is empty)
        self._seed_if_empty()

        # Controllers
        self.auth = AuthController(self.ds)
        self.educator_ctrl = EducatorController(self.ds)
        self.mentor_ctrl = MentorController(self.ds)
        self.learner_ctrl = LearnerController(self.ds)

        # ViewContext: decouples views from this concrete class
        self.ctx = ViewContext(
            tts=self.tts,
            accessibility=self.accessibility,
            auth=self.auth,
            educator_ctrl=self.educator_ctrl,
            mentor_ctrl=self.mentor_ctrl,
            learner_ctrl=self.learner_ctrl,
            root=self.root,
            show_login=self.show_login,
            show_dashboard=self.show_dashboard,
            reset_demo_data=self.reset_demo_data,
        )

        # Container for swappable views
        self._current_view = None
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        # Keyboard navigation: Escape goes back to login
        self.root.bind("<Escape>", lambda e: self.show_login())

        # F1 Helpdesk: announce current location and navigation hints.
        # Listbox has a class-level <Key> binding (type-ahead search) that
        # returns "break" and swallows all key events before bind_all sees
        # them.  A more-specific class binding overrides <Key> for a given
        # event, and by not returning "break" it lets the event propagate
        # up the widget hierarchy where our handlers live.
        self.root.bind_class("Listbox", "<F1>", lambda e: None)
        self.root.bind_all("<F1>", lambda e: self._announce_help())

        # Start with login
        self.show_login()

    def _seed_if_empty(self):
        if not self.ds.has_users():
            seed(self.ds)

    def reset_demo_data(self):
        """Drop and recreate all tables, then re-seed."""
        self.ds.reset_database()
        seed(self.ds)
        self.auth.logout()
        self.show_login()

    def show_login(self):
        self.auth.logout()
        self._switch_view(LoginView(self.container, self.ctx))

    def show_dashboard(self, user):
        """Route to the appropriate dashboard via the role registry."""
        view_class = self._dashboard_registry.get(user.role)
        if view_class is None:
            self.show_login()
            return

        # Apply learner's accessibility preferences
        if user.role == "learner":
            self.accessibility.update_from_prefs(user.accessibility_prefs)
            self.tts.enabled = self.accessibility.audio_enabled

        view = view_class(self.container, self.ctx, user)
        self._switch_view(view)

        # Apply accessibility theme after view is packed (learners only)
        if user.role == "learner":
            self.root.after(100,
                            lambda: self.accessibility.apply_theme(self.root))

    def _announce_help(self):
        """F1 Helpdesk: announce the current page and navigation hints via TTS."""
        if self._current_view and hasattr(self._current_view, 'get_help_text'):
            help_text = self._current_view.get_help_text()
        else:
            help_text = (
                "Welcome to STEMBOOST. "
                "Press Tab to move between controls. "
                "Press Enter to activate buttons. "
                "Press Escape to return to the login screen."
            )
        if self.tts:
            self.tts.stop()
            self.tts.speak(help_text)

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
