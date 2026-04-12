import tkinter as tk
from tkinter import ttk, messagebox

from stemboost.views.widgets import (AccessibleButton, AccessibleLabel,
                                     AccessibleListbox, clear_frame)
from stemboost.services.observer import ProgressObserver
from stemboost.models.constants import STEM_FIELDS, CAREER_PATHS


class LearnerProgressObserver(ProgressObserver):
    """Observer that updates the learner view when progress changes."""

    def __init__(self, view):
        self.view = view

    def on_progress_update(self, learner_id, assignment_id, completed, total):
        self.view._refresh_progress_display()


class LearnerView(tk.Frame):
    """Learner dashboard: view assignments, consume content, track progress."""

    def __init__(self, parent, ctx, user):
        super().__init__(parent)
        self.ctx = ctx
        self.tts = ctx.tts
        self.user = user
        self.ctrl = ctx.learner_ctrl

        # Register as observer for progress updates
        self._observer = LearnerProgressObserver(self)
        self.ctrl.progress_subject.attach(self._observer)

        # Initialize state attributes (set properly by event handlers later)
        self._current_assignment = None
        self._assignments = []
        self._courses = []
        self._opp_list = []
        self._tab_help = {}  # tab widget id -> help text for F1

        self._build()

    def _build(self):
        clear_frame(self)

        # Header
        header = tk.Frame(self)
        header.pack(fill="x", padx=10, pady=5)
        AccessibleLabel(header, text=f"Learner: {self.user.name}",
                        font=("Arial", 16, "bold")).pack(side="left")
        AccessibleButton(header, tts=self.tts, text="Logout",
                         command=self._logout).pack(side="right")
        AccessibleButton(header, tts=self.tts, text="Settings",
                         command=self._show_settings).pack(side="right", padx=5)

        # Navigation help banner
        help_text = (
            "Navigation: Press Tab to move between controls. "
            "Press Enter to activate the selected item. "
            "Use Arrow keys to browse lists. "
            "Press Escape to close dialogs or return to login."
        )
        help_label = AccessibleLabel(
            self, tts=self.tts, text=help_text,
            wraplength=900, justify="left",
            font=("Arial", 10, "italic"), fg="#555555")
        help_label.pack(fill="x", padx=10, pady=(0, 5))

        # Notebook tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self._build_assignments_tab(self.notebook)
        self._build_progress_tab(self.notebook)
        self._build_careers_tab(self.notebook)
        self._build_opportunities_tab(self.notebook)

        # Announce tab changes via TTS
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        if self.tts:
            self.tts.speak(
                f"Welcome, {self.user.name}. Your learner dashboard is ready. "
                "Here is how to navigate: "
                "Press Tab to move between controls and Shift Tab to go back. "
                "Press Enter to activate the selected item. "
                "Use the arrow keys to browse items in a list. "
                "Press Escape to close a dialog or return to the login screen. "
                "You have four tabs: My Assignments, My Progress, "
                "STEM Careers, and Opportunities.")

    def _on_tab_change(self, event):
        """Announce the active tab via TTS when the user switches tabs."""
        if self.tts:
            tab_name = self.notebook.tab(self.notebook.select(), "text")
            self.tts.speak(f"Tab: {tab_name}")

    def _logout(self):
        self.ctrl.progress_subject.detach(self._observer)
        self.ctx.show_login()

    # ------------------------------------------------------------------ #
    # Tab 1: My Assignments
    # ------------------------------------------------------------------ #
    def _build_assignments_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="My Assignments")
        self._tab_help[str(tab)] = (
            "On the left is a list of your assigned learning paths. "
            "Use the arrow keys to select a path, then press Enter to load its courses. "
            "On the right is the list of courses in the selected path. "
            "Select a course and press Enter or Tab to the Open Course button. "
            "Press Tab to move between the lists and buttons. "
            "You have four tabs: My Assignments, My Progress, STEM Careers, and Opportunities. "
            "Press Escape to return to the login screen. "
            "Press F1 at any time to hear this help again."
        )

        left = tk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        AccessibleLabel(left, text="Assigned Paths",
                        font=("Arial", 12, "bold")).pack()
        self.assign_listbox = AccessibleListbox(left, tts=self.tts,
                                                height=8, width=40)
        self.assign_listbox.pack(fill="both", expand=True, pady=5)
        self.assign_listbox.bind("<<ListboxSelect>>",
                                 self._on_assignment_select)
        self.assign_listbox.bind("<Return>",
                                 self._on_assignment_select)

        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        AccessibleLabel(right, text="Courses",
                        font=("Arial", 12, "bold")).pack()
        self.course_listbox = AccessibleListbox(right, tts=self.tts,
                                                height=8, width=40)
        self.course_listbox.pack(fill="both", expand=True, pady=5)

        self.course_listbox.bind("<Return>",
                                 lambda e: self._open_course())

        AccessibleButton(right, tts=self.tts, text="Open Course",
                         command=self._open_course).pack(pady=5)

        self._refresh_assignments()

    def _refresh_assignments(self):
        self.assign_listbox.delete(0, tk.END)
        self._assignments = self.ctrl.get_my_assignments(self.user.user_id)
        for a in self._assignments:
            path = self.ctrl.get_path_info(a.path_id)
            completed, total = self.ctrl.get_progress(a.assignment_id)
            name = path.title if path else f"Path {a.path_id}"
            self.assign_listbox.insert(
                tk.END, f"{name} ({completed}/{total} completed)")

    def _on_assignment_select(self, event):
        sel = self.assign_listbox.curselection()
        if not sel:
            return
        self._current_assignment = self._assignments[sel[0]]
        self.course_listbox.delete(0, tk.END)
        self._courses = self.ctrl.get_courses_for_assignment(
            self._current_assignment)
        for c in self._courses:
            done = self.ctrl.is_course_completed(
                self.user.user_id, self._current_assignment.assignment_id,
                c.course_id)
            status = " [COMPLETED]" if done else ""
            self.course_listbox.insert(tk.END, f"{c.title}{status}")

    def _open_course(self):
        sel = self.course_listbox.curselection()
        if not sel:
            messagebox.showinfo("Select", "Select a course first.")
            return
        course = self._courses[sel[0]]
        already_done = self.ctrl.is_course_completed(
            self.user.user_id, self._current_assignment.assignment_id,
            course.course_id)
        self._show_course_content(course, already_done)

    def _show_course_content(self, course, already_done):
        """Open a window to consume course content via TTS."""
        contents = self.ctrl.get_contents(course.course_id)

        dlg = tk.Toplevel(self)
        dlg.title(f"Course: {course.title}")
        dlg.geometry("600x500")
        dlg.grab_set()
        self.ctx.accessibility.apply_theme(dlg)

        AccessibleLabel(dlg, text=course.title,
                        font=("Arial", 14, "bold")).pack(padx=10, pady=5)
        AccessibleLabel(dlg, text=course.description,
                        wraplength=550).pack(padx=10, pady=5)

        # Content display area
        content_frame = tk.Frame(dlg)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        text_widget = tk.Text(content_frame, wrap="word", state="disabled",
                              font=("Arial", 12))
        scrollbar = tk.Scrollbar(content_frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)

        # Combine all content
        full_text = ""
        for content in contents:
            full_text += f"\n{content.title}\n{'=' * len(content.title)}\n"
            full_text += f"{content.text_body}\n"

        text_widget.configure(state="normal")
        text_widget.insert("1.0", full_text)
        text_widget.configure(state="disabled")

        # Buttons
        btn_frame = tk.Frame(dlg)
        btn_frame.pack(fill="x", padx=10, pady=10)

        AccessibleButton(btn_frame, tts=self.tts, text="Read Aloud",
                         command=lambda: self.tts.speak(full_text) if self.tts else None
                         ).pack(side="left", padx=5)

        AccessibleButton(btn_frame, tts=self.tts, text="Stop Reading",
                         command=lambda: self.tts.stop() if self.tts else None
                         ).pack(side="left", padx=5)

        if not already_done:
            def mark_done():
                completed, total = self.ctrl.mark_course_complete(
                    self.user.user_id,
                    self._current_assignment.assignment_id,
                    course.course_id)
                if self.tts:
                    self.tts.speak(
                        f"Course marked complete. You have completed "
                        f"{completed} out of {total} courses.")
                messagebox.showinfo("Complete",
                                    f"Course complete! {completed}/{total} "
                                    "courses consumed.")
                dlg.destroy()
                self._on_assignment_select(None)
                self._refresh_assignments()
                self._refresh_progress_display()

            AccessibleButton(btn_frame, tts=self.tts, text="Mark Complete",
                             command=mark_done).pack(side="right", padx=5)
        else:
            AccessibleLabel(btn_frame, text="Already Completed",
                            fg="green", font=("Arial", 11, "bold")).pack(
                                side="right", padx=5)

        AccessibleButton(btn_frame, tts=self.tts, text="Close",
                         command=dlg.destroy).pack(side="right", padx=5)

        # Keyboard navigation for dialog
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        # Auto-read via TTS
        if self.tts and contents:
            self.tts.speak(f"Opening course: {course.title}. "
                           f"{contents[0].text_body}")

    # ------------------------------------------------------------------ #
    # Tab 2: My Progress
    # ------------------------------------------------------------------ #
    def _build_progress_tab(self, notebook):
        self.progress_tab = tk.Frame(notebook)
        notebook.add(self.progress_tab, text="My Progress")
        self._tab_help[str(self.progress_tab)] = (
            "This tab shows your progress across all assigned learning paths. "
            "Each path displays how many courses you have completed. "
            "Press Tab to move between items. "
            "Switch to other tabs using Tab to reach the tab bar, then use arrow keys. "
            "Press Escape to return to the login screen."
        )
        self._refresh_progress_display()

    def _refresh_progress_display(self):
        clear_frame(self.progress_tab)
        AccessibleLabel(self.progress_tab, text="Your Progress",
                        font=("Arial", 14, "bold")).pack(padx=10, pady=10)

        assignments = self.ctrl.get_my_assignments(self.user.user_id)
        if not assignments:
            AccessibleLabel(self.progress_tab,
                            text="No assignments yet.").pack(padx=10)
            return

        for a in assignments:
            path = self.ctrl.get_path_info(a.path_id)
            completed, total = self.ctrl.get_progress(a.assignment_id)
            name = path.title if path else f"Path {a.path_id}"

            row = tk.Frame(self.progress_tab)
            row.pack(fill="x", padx=10, pady=5)

            AccessibleLabel(row, text=f"{name}:",
                            font=("Arial", 11, "bold")).pack(side="left")
            AccessibleLabel(
                row,
                text=f"  {completed} out of {total} courses consumed").pack(
                    side="left")

            bar = ttk.Progressbar(row, length=200, maximum=max(total, 1),
                                  value=completed)
            bar.pack(side="left", padx=10)

            if completed == total and total > 0:
                AccessibleLabel(row, text="PATH COMPLETE",
                                fg="green",
                                font=("Arial", 10, "bold")).pack(side="left")

    # ------------------------------------------------------------------ #
    # Tab 3: STEM Careers
    # ------------------------------------------------------------------ #
    def _build_careers_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="STEM Careers")
        self._tab_help[str(tab)] = (
            "On the left is a list of STEM career fields. "
            "Use arrow keys to browse careers, and press Enter to select one. "
            "The career details appear on the right. "
            "Tab to the Read Aloud button to hear the career information. "
            "Press Escape to return to the login screen."
        )

        left = tk.Frame(tab)
        left.pack(side="left", fill="y", padx=5, pady=5)

        AccessibleLabel(left, text="Career Fields",
                        font=("Arial", 12, "bold")).pack()
        self.career_listbox = AccessibleListbox(left, tts=self.tts,
                                                height=12, width=25)
        self.career_listbox.pack(fill="y", expand=True, pady=5)
        self.career_listbox.bind("<<ListboxSelect>>", self._on_career_select)
        self.career_listbox.bind("<Return>", self._on_career_select)

        for field in CAREER_PATHS:
            self.career_listbox.insert(tk.END, field)

        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        AccessibleLabel(right, text="Career Information",
                        font=("Arial", 12, "bold")).pack()
        self.career_text = tk.Text(right, wrap="word", state="disabled",
                                   font=("Arial", 12), height=10)
        self.career_text.pack(fill="both", expand=True, pady=5)

        btn_frame = tk.Frame(right)
        btn_frame.pack(pady=5)
        AccessibleButton(btn_frame, tts=self.tts, text="Read Aloud",
                         command=self._read_career_aloud).pack(side="left",
                                                                padx=5)

    def _on_career_select(self, event):
        sel = self.career_listbox.curselection()
        if not sel:
            return
        field = self.career_listbox.get(sel[0])
        info = CAREER_PATHS.get(field, "No information available.")
        self.career_text.configure(state="normal")
        self.career_text.delete("1.0", tk.END)
        self.career_text.insert("1.0", info)
        self.career_text.configure(state="disabled")

    def _read_career_aloud(self):
        text = self.career_text.get("1.0", tk.END).strip()
        if self.tts and text:
            self.tts.speak(text)

    # ------------------------------------------------------------------ #
    # Tab 4: Opportunities
    # ------------------------------------------------------------------ #
    def _build_opportunities_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="Opportunities")
        self._tab_help[str(tab)] = (
            "This tab lists available internship and academic opportunities. "
            "Use arrow keys to browse the list. "
            "Select an opportunity to see its description below. "
            "Tab to the Read Aloud button to hear the details. "
            "Press Escape to return to the login screen."
        )

        self.opp_listbox = AccessibleListbox(tab, tts=self.tts,
                                             height=8, width=60)
        self.opp_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.opp_listbox.bind("<<ListboxSelect>>", self._on_opp_select)
        self.opp_listbox.bind("<Return>", self._on_opp_select)

        self.opp_detail = AccessibleLabel(tab, text="", wraplength=500,
                                          justify="left")
        self.opp_detail.pack(padx=10, pady=5, anchor="w")

        AccessibleButton(tab, tts=self.tts, text="Read Aloud",
                         command=self._read_opp_aloud).pack(pady=5)

        opps = self.ctrl.get_opportunities()
        for o in opps:
            self.opp_listbox.insert(tk.END,
                                    f"[{o.opp_type.upper()}] {o.title}")
        self._opp_list = opps

    def _on_opp_select(self, event):
        sel = self.opp_listbox.curselection()
        if not sel:
            return
        opp = self._opp_list[sel[0]]
        self.opp_detail.configure(text=opp.description)

    def _read_opp_aloud(self):
        text = self.opp_detail.cget("text")
        if self.tts and text:
            self.tts.speak(text)

    # ------------------------------------------------------------------ #
    # Settings
    # ------------------------------------------------------------------ #
    def get_help_text(self):
        """Return F1 help text describing the current location and navigation."""
        try:
            tab_id = self.notebook.select()
            tab_name = self.notebook.tab(tab_id, "text")
        except Exception:
            tab_id, tab_name = None, "unknown"

        base = f"You are on the Learner Dashboard, {tab_name} tab. "
        return base + self._tab_help.get(tab_id, (
            "Press Tab to move between controls. "
            "Press Escape to return to the login screen."
        ))

    def _show_settings(self):
        dlg = tk.Toplevel(self)
        dlg.title("Accessibility Settings")
        dlg.grab_set()
        self.ctx.accessibility.apply_theme(dlg)

        prefs = self.user.accessibility_prefs

        audio_var = tk.BooleanVar(value=prefs.get("audio", True))
        contrast_var = tk.BooleanVar(value=prefs.get("high_contrast", False))
        large_var = tk.BooleanVar(value=prefs.get("large_text", False))

        tk.Checkbutton(dlg, text="Audio (TTS)",
                       variable=audio_var).pack(anchor="w", padx=20, pady=5)
        tk.Checkbutton(dlg, text="High Contrast",
                       variable=contrast_var).pack(anchor="w", padx=20, pady=5)
        tk.Checkbutton(dlg, text="Large Text",
                       variable=large_var).pack(anchor="w", padx=20, pady=5)

        AccessibleLabel(dlg, text="STEM Interests:",
                        font=("Arial", 11, "bold")).pack(
                            anchor="w", padx=20, pady=(10, 5))
        interest_vars = {}
        for field in STEM_FIELDS:
            var = tk.BooleanVar(value=(field in self.user.stem_interests))
            tk.Checkbutton(dlg, text=field,
                           variable=var).pack(anchor="w", padx=30)
            interest_vars[field] = var

        def save():
            new_prefs = {
                "audio": audio_var.get(),
                "high_contrast": contrast_var.get(),
                "large_text": large_var.get(),
            }
            self.ctrl.update_accessibility_prefs(self.user.user_id, new_prefs)
            self.user.accessibility_prefs = new_prefs

            new_interests = [f for f, v in interest_vars.items() if v.get()]
            self.ctrl.update_stem_interests(self.user.user_id, new_interests)
            self.user.stem_interests = new_interests

            # Apply accessibility changes
            self.ctx.accessibility.update_from_prefs(new_prefs)
            self.tts.enabled = self.ctx.accessibility.audio_enabled
            self.ctx.accessibility.apply_theme(self.ctx.root)

            dlg.destroy()
            if self.tts:
                self.tts.speak("Settings saved.")

        AccessibleButton(dlg, tts=self.tts, text="Save",
                         command=save).pack(pady=10)
