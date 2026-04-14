import tkinter as tk
from tkinter import ttk, messagebox

from stemboost.views.widgets import (AccessibleButton, AccessibleLabel,
                                     AccessibleEntry,
                                     AccessibleCheckbutton, clear_frame)
from stemboost.models.constants import STEM_FIELDS


class LoginView(tk.Frame):
    """Login and registration screen."""

    def __init__(self, parent, ctx):
        super().__init__(parent)
        self.ctx = ctx
        self.tts = ctx.tts
        self._build_login_form()

    def _build_login_form(self):
        clear_frame(self)
        self.configure(padx=40, pady=40)

        AccessibleLabel(self, tts=self.tts, text="STEMBOOST",
                        font=("Arial", 24, "bold")).pack(pady=(0, 5))
        AccessibleLabel(self, tts=self.tts,
                        text="Inclusive STEM Training Platform",
                        font=("Arial", 12)).pack(pady=(0, 30))

        form = tk.Frame(self)
        form.pack()

        AccessibleLabel(form, text="Username:").grid(
            row=0, column=0, sticky="e", pady=5, padx=5)
        self.username_entry = AccessibleEntry(
            form, tts=self.tts, label_text="Username", width=30)
        self.username_entry.grid(row=0, column=1, pady=5)

        AccessibleLabel(form, text="Password:").grid(
            row=1, column=0, sticky="e", pady=5, padx=5)
        self.password_entry = AccessibleEntry(
            form, tts=self.tts, label_text="Password", width=30, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)

        AccessibleButton(btn_frame, tts=self.tts, text="Login",
                         command=self._on_login, width=15).pack(
                             side="left", padx=10)
        AccessibleButton(btn_frame, tts=self.tts, text="Register",
                         command=self._show_register, width=15).pack(
                             side="left", padx=10)

        AccessibleButton(self, tts=self.tts, text="Reset Demo Data",
                         command=self._on_reset,
                         fg="red").pack(pady=(20, 0))

        self.password_entry.bind("<Return>", lambda e: self._on_login())

        # Suppress the first FocusIn announcement on username_entry so
        # the welcome message plays uninterrupted. Subsequent FocusIns
        # (tab back to the username field) still announce normally.
        self._skip_initial_username_focus = True
        original_username_focus = self.username_entry._on_focus

        def wrapped_username_focus(event):
            if self._skip_initial_username_focus:
                self._skip_initial_username_focus = False
                return
            original_username_focus(event)

        self.username_entry.bind("<FocusIn>", wrapped_username_focus)
        self.username_entry.focus_set()

        if self.tts:
            self.tts.speak(
                "Welcome to STEMBOOST. Please enter your username "
                "and password to login, or press Tab to register. "
                "The username field is active.")

    def _on_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Missing Info",
                                   "Please enter username and password.")
            if self.tts:
                self.tts.speak("Please enter username and password.")
            return
        user = self.ctx.auth.login(username, password)
        if user:
            if self.tts:
                self.tts.speak(f"Welcome, {user.name}. Logged in as {user.role}.")
            self.ctx.show_dashboard(user)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            if self.tts:
                self.tts.speak("Login failed. Invalid username or password.")

    def _show_register(self):
        clear_frame(self)
        self.configure(padx=40, pady=20)

        AccessibleLabel(self, text="Register New Account",
                        font=("Arial", 18, "bold")).pack(pady=(0, 20))

        form = tk.Frame(self)
        form.pack()

        labels = ["Name:", "Username:", "Email:", "Password:"]
        self.reg_entries = {}
        for i, label in enumerate(labels):
            AccessibleLabel(form, text=label).grid(
                row=i, column=0, sticky="e", pady=4, padx=5)
            key = label.replace(":", "").lower()
            entry = AccessibleEntry(form, tts=self.tts, label_text=label,
                                    width=30,
                                    show="*" if key == "password" else "")
            entry.grid(row=i, column=1, pady=4)
            self.reg_entries[key] = entry

        row_offset = len(labels)

        AccessibleLabel(form, text="Role:").grid(
            row=row_offset, column=0, sticky="e", pady=4, padx=5)
        self.role_var = tk.StringVar(value="educator")
        role_combo = ttk.Combobox(form, textvariable=self.role_var,
                                  values=["educator", "mentor"],
                                  state="readonly", width=27)
        role_combo.grid(row=row_offset, column=1, pady=4)
        role_combo.bind("<<ComboboxSelected>>", self._on_role_change)

        # Learner-specific fields
        self.learner_frame = tk.Frame(form)
        self.learner_frame.grid(row=row_offset + 1, column=0, columnspan=2,
                                pady=10)
        self._build_learner_fields()

        # Educator-specific fields
        self.educator_frame = tk.Frame(form)
        self.educator_frame.grid(row=row_offset + 2, column=0, columnspan=2,
                                 pady=10)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=15)
        AccessibleButton(btn_frame, tts=self.tts, text="Create Account",
                         command=self._on_register, width=15).pack(
                             side="left", padx=10)
        AccessibleButton(btn_frame, tts=self.tts, text="Back to Login",
                         command=self._build_login_form, width=15).pack(
                             side="left", padx=10)

        self._on_role_change(None)
        if self.tts:
            self.tts.speak("Registration form. Enter your details and select "
                           "a role.")

    def _build_learner_fields(self):
        AccessibleLabel(self.learner_frame, text="Vision Type:").grid(
            row=0, column=0, sticky="e", padx=5)
        self.vision_var = tk.StringVar(value="blind")
        vision_combo = ttk.Combobox(
            self.learner_frame, textvariable=self.vision_var,
            values=["blind", "low_vision"], state="readonly", width=27)
        vision_combo.grid(row=0, column=1, pady=4)
        vision_combo.bind("<<ComboboxSelected>>",
                          self._on_vision_type_change)

        AccessibleLabel(self.learner_frame,
                        text="Accessibility:").grid(
            row=1, column=0, sticky="ne", padx=5)
        acc_frame = tk.Frame(self.learner_frame)
        acc_frame.grid(row=1, column=1, sticky="w")
        self.acc_audio = tk.BooleanVar(value=True)
        self.acc_contrast = tk.BooleanVar(value=False)
        self.acc_large = tk.BooleanVar(value=False)
        AccessibleCheckbutton(acc_frame, tts=self.tts, text="Audio (TTS)",
                              variable=self.acc_audio).pack(anchor="w")
        AccessibleCheckbutton(acc_frame, tts=self.tts, text="High Contrast",
                              variable=self.acc_contrast).pack(anchor="w")
        AccessibleCheckbutton(acc_frame, tts=self.tts, text="Large Text",
                              variable=self.acc_large).pack(anchor="w")

        AccessibleLabel(self.learner_frame,
                        text="STEM Interests:").grid(
            row=2, column=0, sticky="ne", padx=5)
        interest_frame = tk.Frame(self.learner_frame)
        interest_frame.grid(row=2, column=1, sticky="w")
        self.interest_vars = {}
        for field in STEM_FIELDS:
            var = tk.BooleanVar(value=False)
            AccessibleCheckbutton(interest_frame, tts=self.tts, text=field,
                                  variable=var).pack(anchor="w")
            self.interest_vars[field] = var

    def _on_vision_type_change(self, event):
        """Auto-preselect accessibility features based on vision type."""
        vision = self.vision_var.get()
        if vision == "blind":
            self.acc_audio.set(True)
            self.acc_contrast.set(False)
            self.acc_large.set(False)
        elif vision == "low_vision":
            self.acc_audio.set(False)
            self.acc_contrast.set(True)
            self.acc_large.set(True)

    def _on_role_change(self, event):
        role = self.role_var.get()
        if role == "learner":
            self.learner_frame.grid()
            self.educator_frame.grid_remove()
            self._build_educator_fields_if_needed()
        elif role == "educator":
            self.learner_frame.grid_remove()
            self.educator_frame.grid()
            self._build_educator_fields_if_needed()
        else:
            self.learner_frame.grid_remove()
            self.educator_frame.grid_remove()

    def _build_educator_fields_if_needed(self):
        if not self.educator_frame.winfo_children():
            AccessibleLabel(self.educator_frame,
                            text="Expertise Areas:").grid(
                row=0, column=0, sticky="ne", padx=5)
            exp_frame = tk.Frame(self.educator_frame)
            exp_frame.grid(row=0, column=1, sticky="w")
            self.expertise_vars = {}
            for field in STEM_FIELDS:
                var = tk.BooleanVar(value=False)
                AccessibleCheckbutton(exp_frame, tts=self.tts, text=field,
                                      variable=var).pack(anchor="w")
                self.expertise_vars[field] = var

    def _on_register(self):
        name = self.reg_entries["name"].get().strip()
        username = self.reg_entries["username"].get().strip()
        email = self.reg_entries["email"].get().strip()
        password = self.reg_entries["password"].get().strip()
        role = self.role_var.get()

        if not all([name, username, email, password]):
            messagebox.showwarning("Missing Info", "Please fill all fields.")
            if self.tts:
                self.tts.speak("Please fill all fields.")
            return

        kwargs = {}
        if role == "learner":
            kwargs["vision_type"] = self.vision_var.get()
            kwargs["accessibility_prefs"] = {
                "audio": self.acc_audio.get(),
                "high_contrast": self.acc_contrast.get(),
                "large_text": self.acc_large.get(),
            }
            kwargs["stem_interests"] = [
                f for f, v in self.interest_vars.items() if v.get()]
        elif role == "educator":
            kwargs["expertise_areas"] = [
                f for f, v in self.expertise_vars.items() if v.get()]

        try:
            self.ctx.auth.register(username, email, password, name, role,
                                   **kwargs)
            messagebox.showinfo("Success", "Account created. Please login.")
            if self.tts:
                self.tts.speak("Account created successfully. Please login.")
            self._build_login_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            if self.tts:
                self.tts.speak(f"Registration failed. {e}")

    def get_help_text(self):
        """Return F1 help text describing the current location and navigation."""
        # Check if we're on the registration form by looking for reg_entries
        if hasattr(self, 'reg_entries') and self.reg_entries:
            # Check if the registration form is currently visible
            try:
                if self.reg_entries["name"].winfo_ismapped():
                    return (
                        "You are on the Registration page. "
                        "Fill in your Name, Username, Email, and Password. "
                        "Then choose a role from the dropdown. "
                        "Press Tab to move between fields. "
                        "Press the Create Account button or Tab to it and press Enter. "
                        "Press the Back to Login button to return to the login screen. "
                        "Press Escape to return to login."
                    )
            except tk.TclError:
                pass
        return (
            "You are on the Login page. "
            "There are two text fields: Username and Password. "
            "Press Tab to move between the fields and buttons. "
            "Type your username, press Tab, type your password, "
            "then press Enter to log in. "
            "Or Tab to the Register button and press Enter to create a new account. "
            "Press Escape at any time to return to this login screen."
        )

    def _on_reset(self):
        if messagebox.askyesno("Reset", "Reset all data to initial demo state?"):
            self.ctx.reset_demo_data()
            if self.tts:
                self.tts.speak("Demo data has been reset.")
            messagebox.showinfo("Reset", "Demo data reset successfully.")
