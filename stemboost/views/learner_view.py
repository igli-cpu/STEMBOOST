import tkinter as tk
from tkinter import ttk, messagebox

from stemboost.views.widgets import (AccessibleButton, AccessibleLabel,
                                     AccessibleListbox,
                                     AccessibleCheckbutton, clear_frame)
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
        # Controls how _on_tab_change announces the new tab: "full" speaks
        # the full help text, "brief" speaks only "Tab: {name}". Set to
        # "brief" just before programmatic .select() calls that represent
        # a quick label-cycle (Tab key), leaving the default "full" for
        # mouse clicks.
        self._pending_tab_announce = "full"

        self._build()

    def _build(self):
        clear_frame(self)

        # Header
        header = tk.Frame(self)
        header.pack(fill="x", padx=10, pady=5)
        AccessibleLabel(header, text=f"Learner: {self.user.name}",
                        font=("Arial", 16, "bold")).pack(side="left")
        self._logout_btn = AccessibleButton(header, tts=self.tts, text="Logout",
                                            command=self._logout)
        self._logout_btn.pack(side="right")
        AccessibleButton(header, tts=self.tts, text="Settings",
                         command=self._show_settings).pack(side="right", padx=5)
        self._help_btn = AccessibleButton(header, tts=self.tts, text="Help",
                                          command=self._announce_help)
        self._help_btn.pack(side="right", padx=5)

        # Suppress the first FocusIn on Logout so it doesn't clobber the
        # welcome speech when we programmatically set initial focus below.
        self._skip_initial_logout_focus = True
        original_logout_focus = self._logout_btn._on_focus

        def wrapped_logout_focus(event):
            if self._skip_initial_logout_focus:
                self._skip_initial_logout_focus = False
                return
            original_logout_focus(event)

        self._logout_btn.bind("<FocusIn>", wrapped_logout_focus)

        # Explicit Tab/Shift-Tab bindings on the boundary buttons so the
        # notebook is entered at the correct tab label for each direction.
        self._help_btn.bind("<Tab>", self._on_help_tab_forward)
        self._logout_btn.bind("<Shift-Tab>", self._on_logout_shift_tab_back)
        self._logout_btn.bind("<ISO_Left_Tab>", self._on_logout_shift_tab_back)

        # Navigation help banner
        help_text = (
            "Navigation: Press Tab or Shift+Tab to move between controls "
            "and cycle tab labels. "
            "Press Enter to activate a button, or to enter the content of "
            "the focused tab. "
            "Inside a list, press Tab or Down arrow to walk through items "
            "without selecting, and press Enter to select the current item. "
            "Press F1 or the Help button to repeat the current tab's "
            "description. "
            "Press Escape to step back: from inside a tab to its labels, "
            "or from the main view back to login."
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

        # Announce the tab label under the mouse when hovering, and the
        # currently-selected tab when the notebook itself gains focus.
        self._last_hovered_tab_idx = None
        self.notebook.bind("<Motion>", self._on_notebook_motion)
        self.notebook.bind("<Leave>", self._on_notebook_leave)
        self.notebook.bind("<FocusIn>", self._on_notebook_focus)

        # When focus is on the notebook itself, Tab/Shift-Tab cycle tab
        # labels (brief announcement) instead of entering tab content.
        # Enter is the explicit opt-in to move focus into the active tab.
        self.notebook.bind("<Tab>", self._on_notebook_tab)
        self.notebook.bind("<Shift-Tab>", self._on_notebook_shift_tab)
        self.notebook.bind("<ISO_Left_Tab>", self._on_notebook_shift_tab)
        self.notebook.bind("<Return>", self._on_notebook_enter)

        # Move initial focus to Logout so Tab cycling starts from a known
        # point outside the tab content. Scheduled via after_idle so it
        # happens after the view is fully mapped.
        self.after_idle(self._logout_btn.focus_set)

        if self.tts:
            self.tts.speak(
                f"Welcome, {self.user.name}. Your learner dashboard is ready. "
                "Here is how to navigate: "
                "Press Tab to move between controls and Shift Tab to go back. "
                "When focus is on the tab labels, Tab and Shift Tab cycle "
                "through them. Press Enter to enter the focused tab's content. "
                "Inside a list, press Tab or Down arrow to walk through "
                "items without selecting, and press Enter to select the "
                "current item. "
                "Press Escape to step back one level: from inside a tab's "
                "content, Escape returns you to the tab labels; from the "
                "tab labels or header buttons, Escape returns you to the "
                "login screen; and inside a dialog, Escape closes it. "
                "Press F1 at any time, or tab to the Help button in the top "
                "right, to hear a description of the current tab. "
                "You have four tabs: My Assignments, My Progress, "
                "STEM Careers, and Opportunities.")

    def _on_tab_change(self, event):
        """Announce the active tab when the selection changes."""
        mode = self._pending_tab_announce
        self._pending_tab_announce = "full"  # reset for next change
        if not self.tts:
            return
        tab_id = self.notebook.select()
        tab_name = self.notebook.tab(tab_id, "text")
        if mode == "brief":
            self.tts.speak(f"Tab: {tab_name}")
            return
        help_text = self._tab_help.get(tab_id, "")
        intro = f"Tab: {tab_name}. {help_text}".strip()
        if tab_name == "My Progress":
            self._refresh_progress_display(announce=True, prefix=intro + " ")
        else:
            self.tts.speak(intro)

    def _announce_help(self):
        """Speak the help text for the current tab. Shared by Help button and F1."""
        if not self.tts:
            return
        self.tts.stop()
        self.tts.speak(self.get_help_text())

    def _on_notebook_motion(self, event):
        """Announce the tab label currently under the mouse, once per tab."""
        if not self.tts:
            return
        try:
            elem = self.notebook.identify(event.x, event.y)
        except tk.TclError:
            return
        if "label" not in elem:
            self._last_hovered_tab_idx = None
            return
        try:
            idx = self.notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return
        if idx == self._last_hovered_tab_idx:
            return
        self._last_hovered_tab_idx = idx
        tab_name = self.notebook.tab(idx, "text")
        self.tts.speak(f"Tab: {tab_name}")

    def _on_notebook_leave(self, event):
        self._last_hovered_tab_idx = None

    def _on_notebook_focus(self, event):
        """Announce the currently selected tab when the notebook gains focus.

        Entry direction (forward vs backward) is handled by explicit Tab
        and Shift-Tab bindings on the Help and Logout buttons, which set
        the target tab before focus arrives here. So this handler only
        announces — it does not reset.
        """
        if not self.tts:
            return
        try:
            tab_id = self.notebook.select()
            tab_name = self.notebook.tab(tab_id, "text")
        except tk.TclError:
            return
        self.tts.speak(f"Tab: {tab_name}")

    def _on_notebook_tab(self, event):
        """Advance to the next tab label. At the last tab, exit the notebook
        forward so the user can tab back out to the header buttons."""
        # Tkinter's <Tab> pattern also matches Shift+Tab because unmentioned
        # modifiers are don't-cares. Route Shift+Tab to the other handler.
        if event.state & 0x1:
            return self._on_notebook_shift_tab(event)
        tabs = self.notebook.tabs()
        if not tabs:
            return "break"
        idx = list(tabs).index(self.notebook.select())
        if idx < len(tabs) - 1:
            self._pending_tab_announce = "brief"
            self.notebook.select(idx + 1)
        else:
            self._logout_btn.focus_set()
        return "break"

    def _on_notebook_shift_tab(self, event):
        """Step backward through tab labels. At the first tab, exit the
        notebook backward to the Help button."""
        tabs = self.notebook.tabs()
        if not tabs:
            return "break"
        idx = list(tabs).index(self.notebook.select())
        if idx > 0:
            self._pending_tab_announce = "brief"
            self.notebook.select(idx - 1)
        else:
            self._help_btn.focus_set()
        return "break"

    def _on_help_tab_forward(self, event):
        """Tab from the Help button: enter the notebook at tab 0.

        Must ignore Shift+Tab — otherwise the key repeat bounces between
        Help and the notebook forever, because the bare <Tab> pattern
        also matches Shift+Tab in Tkinter.
        """
        if event.state & 0x1:  # Shift held — let default traversal run
            return None
        tabs = self.notebook.tabs()
        if not tabs:
            return None
        self._pending_tab_announce = "brief"
        self.notebook.select(tabs[0])
        self.notebook.focus_set()
        return "break"

    def _on_logout_shift_tab_back(self, event):
        """Shift+Tab from the Logout button: enter the notebook at the last
        tab so the user can cycle backward through tab labels."""
        tabs = self.notebook.tabs()
        if not tabs:
            return None
        self._pending_tab_announce = "brief"
        self.notebook.select(tabs[-1])
        self.notebook.focus_set()
        return "break"

    def _on_notebook_enter(self, event):
        """Move focus into the first focusable widget of the active tab."""
        try:
            tab_id = self.notebook.select()
        except tk.TclError:
            return "break"
        tab_widget = None
        for child in self.notebook.winfo_children():
            if str(child) == tab_id:
                tab_widget = child
                break
        if tab_widget is None:
            return "break"
        first = self._first_focusable(tab_widget)
        if first is not None:
            first.focus_set()
            if self.tts:
                self.tts.speak(
                    "Entered tab. Press Escape to return to the tab labels.")
        elif self.tts:
            self.tts.speak("This tab has no focusable controls.")
        return "break"

    def _bind_escape_to_notebook(self, tab_frame):
        """Bind Escape on every focusable descendant of a tab frame so
        pressing Escape inside tab content returns focus to the notebook
        tab labels, rather than firing the root-level Escape that logs
        the user out to the login screen.
        """
        def handler(event):
            self.notebook.focus_set()
            return "break"

        def walk(widget):
            try:
                if str(widget.cget("takefocus")) in ("1", "True"):
                    widget.bind("<Escape>", handler)
            except tk.TclError:
                pass
            for child in widget.winfo_children():
                walk(child)

        walk(tab_frame)

    def _first_focusable(self, parent):
        for child in parent.winfo_children():
            try:
                tf = str(child.cget("takefocus"))
                if tf in ("1", "True"):
                    return child
            except tk.TclError:
                pass
            found = self._first_focusable(child)
            if found is not None:
                return found
        return None

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
            "Press Tab or Down arrow to walk through the paths, then press "
            "Enter to load the courses for the highlighted path. "
            "On the right is the list of courses. Press Tab or Down arrow "
            "to walk through the courses, then press Enter to open the "
            "highlighted course. "
            "Press Tab or Shift Tab on the notebook to cycle tab labels. "
            "You have four tabs: My Assignments, My Progress, STEM Careers, and Opportunities. "
            "Press Escape to go back: to the tab labels from inside the tab, or to the login screen from the tab labels. "
            "Press F1 at any time to hear this help again."
        )

        left = tk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        AccessibleLabel(left, text="Assigned Paths",
                        font=("Arial", 12, "bold")).pack()
        self.assign_listbox = AccessibleListbox(
            left, tts=self.tts,
            item_noun="Assigned Path",
            on_activate=self._on_assignment_select,
            height=8, width=40)
        self.assign_listbox.pack(fill="both", expand=True, pady=5)

        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        AccessibleLabel(right, text="Courses",
                        font=("Arial", 12, "bold")).pack()
        self.course_listbox = AccessibleListbox(
            right, tts=self.tts,
            item_noun="Course",
            on_activate=lambda e: self._open_course(),
            height=8, width=40)
        self.course_listbox.pack(fill="both", expand=True, pady=5)

        AccessibleButton(right, tts=self.tts, text="Open Course",
                         command=self._open_course).pack(pady=5)

        self._refresh_assignments()
        self._bind_escape_to_notebook(tab)

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

        # Remember the widget that opened the dialog so we can restore
        # focus to it after the dialog closes.
        previous_focus = self.focus_get()

        def close_and_restore():
            dlg.destroy()
            if previous_focus is not None:
                try:
                    previous_focus.focus_set()
                except tk.TclError:
                    pass

        dlg = tk.Toplevel(self)
        dlg.title(f"Course: {course.title}")
        dlg.geometry("600x500")
        dlg.grab_set()
        # Move keyboard focus into the dialog so <Escape> reaches the
        # dialog's binding instead of the previously-focused widget
        # (whose Escape would bubble up to root → logout).
        dlg.focus_set()
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
                close_and_restore()
                prev_idx = self.assign_listbox.curselection()
                self._refresh_assignments()
                if prev_idx:
                    self.assign_listbox.selection_set(prev_idx[0])
                    self._on_assignment_select(None)
                self._refresh_progress_display()

            AccessibleButton(btn_frame, tts=self.tts, text="Mark Complete",
                             command=mark_done).pack(side="right", padx=5)
        else:
            AccessibleLabel(btn_frame, text="Already Completed",
                            fg="green", font=("Arial", 11, "bold")).pack(
                                side="right", padx=5)

        AccessibleButton(btn_frame, tts=self.tts, text="Close",
                         command=close_and_restore).pack(side="right", padx=5)

        def on_escape(event):
            close_and_restore()
            return "break"
        dlg.bind("<Escape>", on_escape)

        # Auto-read via TTS: speak every content unit, not just the first.
        if self.tts and contents:
            body = ". ".join(
                f"{c.title}. {c.text_body}" for c in contents)
            status = ("You have already completed this course. "
                      if already_done else "")
            buttons = ("Read Aloud, Stop Reading, and Close"
                       if already_done
                       else "Read Aloud, Stop Reading, Mark Complete, "
                            "and Close")
            self.tts.speak(
                f"Opening course: {course.title}. "
                f"{status}"
                f"This course has {len(contents)} content "
                f"{'unit' if len(contents) == 1 else 'units'}. {body} "
                f"Tab through the {buttons} buttons to continue.")

    # ------------------------------------------------------------------ #
    # Tab 2: My Progress
    # ------------------------------------------------------------------ #
    def _build_progress_tab(self, notebook):
        self.progress_tab = tk.Frame(notebook)
        notebook.add(self.progress_tab, text="My Progress")
        self._tab_help[str(self.progress_tab)] = (
            "This tab shows your progress across all assigned learning paths. "
            "Each path displays how many courses you have completed. "
            "Press Tab or Down arrow to walk through paths and hear each path's progress. "
            "Tab to the Read Aloud button to hear the full progress summary, "
            "or the Stop Reading button to interrupt playback. "
            "Press Tab or Shift Tab on the notebook to cycle tab labels. "
            "Press Escape to go back: to the tab labels from inside the tab, or to the login screen from the tab labels."
        )
        self._progress_summary = ""
        self._refresh_progress_display()

    def _build_progress_speech(self, assignments):
        """Return (full_summary, per_row_texts) for the given assignments.

        `full_summary` is the spoken summary across all assignments.
        `per_row_texts[i]` is what to announce when row i receives focus.
        Kept separate from rendering so tests can verify the speech text
        without constructing a Tk UI.
        """
        if not assignments:
            return "You have no assignments yet.", []

        per_row = []
        speech_parts = []
        for a in assignments:
            path = self.ctrl.get_path_info(a.path_id)
            completed, total = self.ctrl.get_progress(a.assignment_id)
            name = path.title if path else f"Path {a.path_id}"

            if completed == total and total > 0:
                row_text = (
                    f"{name}: path complete. "
                    f"All {total} courses consumed.")
            else:
                percent = int((completed / total) * 100) if total > 0 else 0
                row_text = (
                    f"{name}: {completed} out of {total} courses consumed, "
                    f"{percent} percent complete.")
            per_row.append(row_text)
            speech_parts.append(row_text)

        summary = (f"You have {len(assignments)} assigned "
                   f"{'path' if len(assignments) == 1 else 'paths'}. ")
        summary += " ".join(speech_parts)
        return summary, per_row

    def _read_progress_aloud(self):
        """Speak the cached progress summary from the top."""
        if self.tts and self._progress_summary:
            self.tts.stop()
            self.tts.speak(self._progress_summary)

    def _stop_progress_reading(self):
        if self.tts:
            self.tts.stop()

    def _refresh_progress_display(self, announce=False, prefix=""):
        clear_frame(self.progress_tab)
        AccessibleLabel(self.progress_tab, text="Your Progress",
                        font=("Arial", 14, "bold")).pack(padx=10, pady=10)

        assignments = self.ctrl.get_my_assignments(self.user.user_id)
        summary, per_row_texts = self._build_progress_speech(assignments)
        self._progress_summary = summary

        if not assignments:
            AccessibleLabel(self.progress_tab,
                            text="No assignments yet.").pack(padx=10)
            if announce and self.tts:
                self.tts.speak(f"{prefix}{summary}")
            return

        for a, row_text in zip(assignments, per_row_texts):
            path = self.ctrl.get_path_info(a.path_id)
            completed, total = self.ctrl.get_progress(a.assignment_id)
            name = path.title if path else f"Path {a.path_id}"

            row = tk.Frame(self.progress_tab)
            row.pack(fill="x", padx=10, pady=5)

            # Focusable label announces the full row's progress on focus so
            # keyboard users can Tab through paths and hear each status.
            AccessibleLabel(row, tts=self.tts, announce=True,
                            text=row_text, justify="left",
                            font=("Arial", 11, "bold")).pack(side="left")

            bar = ttk.Progressbar(row, length=200, maximum=max(total, 1),
                                  value=completed)
            bar.pack(side="left", padx=10)

            if completed == total and total > 0:
                AccessibleLabel(row, text="PATH COMPLETE",
                                fg="green",
                                font=("Arial", 10, "bold")).pack(side="left")

        # Read Aloud / Stop Reading controls — mirrors the pattern used by
        # the Careers and Opportunities tabs so TTS is available on demand.
        btn_frame = tk.Frame(self.progress_tab)
        btn_frame.pack(pady=10)
        AccessibleButton(btn_frame, tts=self.tts, text="Read Aloud",
                         command=self._read_progress_aloud).pack(
                             side="left", padx=5)
        AccessibleButton(btn_frame, tts=self.tts, text="Stop Reading",
                         command=self._stop_progress_reading).pack(
                             side="left", padx=5)

        # Re-bind Escape since we've rebuilt the tab's subtree.
        self._bind_escape_to_notebook(self.progress_tab)

        if announce and self.tts:
            self.tts.speak(f"{prefix}{summary}")

    # ------------------------------------------------------------------ #
    # Tab 3: STEM Careers
    # ------------------------------------------------------------------ #
    def _build_careers_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="STEM Careers")
        self._tab_help[str(tab)] = (
            "On the left is a list of STEM career fields. "
            "Press Tab or Down arrow to walk through the careers, then "
            "press Enter to load the highlighted career's details on the "
            "right. "
            "Tab to the Read Aloud button to hear the career information. "
            "Press Tab or Shift Tab on the notebook to cycle tab labels. "
            "Press Escape to go back: to the tab labels from inside the tab, or to the login screen from the tab labels."
        )

        left = tk.Frame(tab)
        left.pack(side="left", fill="y", padx=5, pady=5)

        AccessibleLabel(left, text="Career Fields",
                        font=("Arial", 12, "bold")).pack()
        self.career_listbox = AccessibleListbox(
            left, tts=self.tts,
            item_noun="Career Field",
            on_activate=self._on_career_select,
            height=12, width=25)
        self.career_listbox.pack(fill="y", expand=True, pady=5)

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

        self._bind_escape_to_notebook(tab)

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
        if self.tts:
            self.tts.speak(f"{field}. {info}")

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
            "Press Tab or Down arrow to walk through the list, then press "
            "Enter to load the highlighted opportunity's description below. "
            "Tab to the Read Aloud button to hear the details. "
            "Press Tab or Shift Tab on the notebook to cycle tab labels. "
            "Press Escape to go back: to the tab labels from inside the tab, or to the login screen from the tab labels."
        )

        self.opp_listbox = AccessibleListbox(
            tab, tts=self.tts,
            item_noun="Opportunity",
            on_activate=self._on_opp_select,
            height=8, width=60)
        self.opp_listbox.pack(fill="both", expand=True, padx=10, pady=10)

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

        self._bind_escape_to_notebook(tab)

    def _on_opp_select(self, event):
        sel = self.opp_listbox.curselection()
        if not sel:
            return
        opp = self._opp_list[sel[0]]
        self.opp_detail.configure(text=opp.description)
        if self.tts:
            self.tts.speak(f"{opp.title}. {opp.description}")

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
            "Press Escape to go back: to the tab labels from inside the tab, or to the login screen from the tab labels."
        ))

    def _show_settings(self):
        # Remember which widget had focus so we can restore it on close.
        previous_focus = self.focus_get()

        def close_and_restore():
            dlg.destroy()
            if previous_focus is not None:
                try:
                    previous_focus.focus_set()
                except tk.TclError:
                    pass

        dlg = tk.Toplevel(self)
        dlg.title("Accessibility Settings")
        dlg.grab_set()
        dlg.focus_set()
        self.ctx.accessibility.apply_theme(dlg)

        prefs = self.user.accessibility_prefs

        audio_var = tk.BooleanVar(value=prefs.get("audio", True))
        contrast_var = tk.BooleanVar(value=prefs.get("high_contrast", False))
        large_var = tk.BooleanVar(value=prefs.get("large_text", False))

        AccessibleCheckbutton(dlg, tts=self.tts, text="Audio (TTS)",
                              variable=audio_var).pack(
                                  anchor="w", padx=20, pady=5)
        AccessibleCheckbutton(dlg, tts=self.tts, text="High Contrast",
                              variable=contrast_var).pack(
                                  anchor="w", padx=20, pady=5)
        AccessibleCheckbutton(dlg, tts=self.tts, text="Large Text",
                              variable=large_var).pack(
                                  anchor="w", padx=20, pady=5)

        AccessibleLabel(dlg, text="STEM Interests:",
                        font=("Arial", 11, "bold")).pack(
                            anchor="w", padx=20, pady=(10, 5))
        interest_vars = {}
        for field in STEM_FIELDS:
            var = tk.BooleanVar(value=(field in self.user.stem_interests))
            AccessibleCheckbutton(dlg, tts=self.tts, text=field,
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

            self.ctx.accessibility.update_from_prefs(new_prefs)
            self.ctx.accessibility.apply_theme(self.ctx.root)

            # Queue the confirmation before flipping tts.enabled — the
            # utterance is buffered at the engine level so it still plays
            # even if the user just disabled audio.
            self.tts.enabled = True
            self.tts.speak("Settings saved.")
            self.tts.enabled = self.ctx.accessibility.audio_enabled

            close_and_restore()

        AccessibleButton(dlg, tts=self.tts, text="Save",
                         command=save).pack(pady=10)

        def on_escape(event):
            close_and_restore()
            return "break"
        dlg.bind("<Escape>", on_escape)

        # Announce the dialog's purpose and current state on open.
        if self.tts:
            def state(on):
                return "on" if on else "off"
            self.tts.speak(
                "Accessibility Settings dialog. "
                "Press Tab to move between options, Space to toggle the "
                "focused checkbox, and Tab to the Save button and press "
                "Enter to save. Press Escape to cancel. "
                f"Audio is currently {state(audio_var.get())}. "
                f"High Contrast is currently {state(contrast_var.get())}. "
                f"Large Text is currently {state(large_var.get())}. "
                "Below are checkboxes for your STEM interests.")
