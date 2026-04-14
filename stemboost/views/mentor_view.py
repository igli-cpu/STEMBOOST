import tkinter as tk
from tkinter import ttk, messagebox

from stemboost.views.widgets import (AccessibleButton, AccessibleLabel,
                                     AccessibleEntry, AccessibleText,
                                     AccessibleListbox, clear_frame)
from stemboost.models.constants import STEM_FIELDS


class MentorView(tk.Frame):
    """Mentor dashboard: browse content, assign paths, monitor progress,
    register learners, and post opportunities."""

    def __init__(self, parent, ctx, user):
        super().__init__(parent)
        self.ctx = ctx
        self.tts = ctx.tts
        self.user = user
        self.ctrl = ctx.mentor_ctrl
        self._paths = []
        self._learners = []
        self._browse_courses = []
        self._opportunities = []
        self._tab_help = {}  # tab widget id -> help text for F1
        self._build()

    def _build(self):
        clear_frame(self)

        # Header
        header = tk.Frame(self)
        header.pack(fill="x", padx=10, pady=5)
        AccessibleLabel(header, text=f"Mentor: {self.user.name}",
                        font=("Arial", 16, "bold")).pack(side="left")
        AccessibleButton(header, tts=self.tts, text="Logout",
                         command=self.ctx.show_login).pack(side="right")

        # Notebook tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self._build_browse_tab(self.notebook)
        self._build_learners_tab(self.notebook)
        self._build_opportunities_tab(self.notebook)

        # Announce tab changes via TTS
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        # Ctrl+Tab / Ctrl+Shift+Tab cycle through notebook tabs from anywhere
        # inside the notebook (including from within listboxes).
        self.notebook.bind("<Control-Tab>", self._ctrl_tab_next)
        self.notebook.bind("<Control-Shift-Tab>", self._ctrl_tab_prev)

        if self.tts:
            self.tts.speak("Mentor dashboard. Browse content, manage learners, "
                           "or post opportunities.")

    def _on_tab_change(self, event):
        """Announce the active tab via TTS when the user switches tabs."""
        if self.tts:
            tab_id = self.notebook.select()
            tab_name = self.notebook.tab(tab_id, "text")
            self.tts.speak(f"Tab: {tab_name}")

    def _ctrl_tab_next(self, event=None):
        """Advance to the next notebook tab (Ctrl+Tab)."""
        tabs = self.notebook.tabs()
        if tabs:
            idx = list(tabs).index(self.notebook.select())
            self.notebook.select((idx + 1) % len(tabs))
        return "break"

    def _ctrl_tab_prev(self, event=None):
        """Go back to the previous notebook tab (Ctrl+Shift+Tab)."""
        tabs = self.notebook.tabs()
        if tabs:
            idx = list(tabs).index(self.notebook.select())
            self.notebook.select((idx - 1) % len(tabs))
        return "break"

    # ------------------------------------------------------------------ #
    # Tab 1: Browse & Assign
    # ------------------------------------------------------------------ #
    def _build_browse_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="Browse & Assign")
        self._tab_help[str(tab)] = (
            "On the left is a list of all learning paths. "
            "Select a path with arrow keys to see its courses on the right. "
            "Use the Assign to Learner button to assign the selected path to one of your learners. "
            "Press Tab to move between the lists and buttons. "
            "Press Control Tab to go to the next tab, or Control Shift Tab to go to the previous tab. "
            "You have three tabs: Browse and Assign, My Learners, and Opportunities. "
            "Press Escape to return to the login screen. "
            "Press F1 at any time to hear this help again."
        )

        left = tk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        AccessibleLabel(left, text="Learning Paths",
                        font=("Arial", 12, "bold")).pack()
        self.path_listbox = AccessibleListbox(left, tts=self.tts,
                                              item_noun="Learning Path",
                                              height=12, width=40)
        self.path_listbox.pack(fill="both", expand=True, pady=5)
        self.path_listbox.bind("<<ListboxSelect>>", self._on_path_select,
                               add="+")

        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        AccessibleLabel(right, text="Courses in Path",
                        font=("Arial", 12, "bold")).pack()
        self.course_listbox = AccessibleListbox(right, tts=self.tts,
                                                item_noun="Course",
                                                height=12, width=40)
        self.course_listbox.pack(fill="both", expand=True, pady=5)

        AccessibleButton(right, tts=self.tts, text="Assign to Learner",
                         command=self._assign_dialog).pack(pady=5)

        self._refresh_paths()

    def _refresh_paths(self):
        self.path_listbox.delete(0, tk.END)
        self._paths = self.ctrl.browse_all_paths()
        for p in self._paths:
            self.path_listbox.insert(tk.END, f"{p.title} [{p.category}]")

    def _on_path_select(self, event):
        sel = self.path_listbox.curselection()
        if not sel:
            return
        path = self._paths[sel[0]]
        self.course_listbox.delete(0, tk.END)
        self._browse_courses = self.ctrl.get_courses_for_path(path.path_id)
        for c in self._browse_courses:
            self.course_listbox.insert(tk.END, c.title)

    def _assign_dialog(self):
        sel = self.path_listbox.curselection()
        if not sel:
            messagebox.showinfo("Select", "Select a learning path first.")
            return
        path = self._paths[sel[0]]
        courses = self.ctrl.get_courses_for_path(path.path_id)
        learners = self.ctrl.get_my_learners(self.user.user_id)

        if not learners:
            messagebox.showinfo("No Learners",
                                "You have no learners assigned to you. "
                                "Register a learner first.")
            return

        dlg = tk.Toplevel(self)
        dlg.title(f"Assign: {path.title}")
        dlg.grab_set()
        self.ctx.accessibility.apply_theme(dlg)

        AccessibleLabel(dlg, text="Select Learner:").pack(padx=10, pady=5)
        learner_var = tk.StringVar()
        learner_combo = ttk.Combobox(
            dlg, textvariable=learner_var,
            values=[f"{l.name} ({l.username})" for l in learners],
            state="readonly", width=35)
        learner_combo.pack(padx=10, pady=5)
        if learners:
            learner_combo.current(0)

        AccessibleLabel(dlg, text="Deselect courses to exclude:").pack(
            padx=10, pady=(10, 5))
        course_vars = {}
        for c in courses:
            var = tk.BooleanVar(value=True)
            tk.Checkbutton(dlg, text=c.title, variable=var).pack(
                anchor="w", padx=20)
            course_vars[c.course_id] = var

        def assign():
            idx = learner_combo.current()
            if idx < 0:
                messagebox.showwarning("Select", "Select a learner.")
                return
            learner = learners[idx]
            excluded = [cid for cid, v in course_vars.items() if not v.get()]
            self.ctrl.assign_path(self.user.user_id, learner.user_id,
                                  path.path_id, excluded)
            dlg.destroy()
            if self.tts:
                self.tts.speak(f"Path assigned to {learner.name}.")
            messagebox.showinfo("Assigned",
                                f"'{path.title}' assigned to {learner.name}.")
            self._refresh_learners_list()

        AccessibleButton(dlg, tts=self.tts, text="Assign",
                         command=assign).pack(pady=10)

    # ------------------------------------------------------------------ #
    # Tab 2: My Learners & Progress
    # ------------------------------------------------------------------ #
    def _build_learners_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="My Learners")
        self._tab_help[str(tab)] = (
            "This tab shows your registered learners and their progress. "
            "Use the Register New Learner button to add a new learner. "
            "Select a learner from the list to view their progress below. "
            "Press Tab to move between controls. "
            "Press Control Tab to go to the next tab, or Control Shift Tab to go to the previous tab. "
            "Press Escape to return to the login screen."
        )

        top_btns = tk.Frame(tab)
        top_btns.pack(fill="x", padx=10, pady=5)
        AccessibleButton(top_btns, tts=self.tts, text="Register New Learner",
                         command=self._register_learner_dialog).pack(
                             side="left", padx=5)
        AccessibleButton(top_btns, tts=self.tts, text="Refresh",
                         command=self._refresh_learners_list).pack(
                             side="left", padx=5)

        self.learner_listbox = AccessibleListbox(tab, tts=self.tts,
                                                 item_noun="Learner",
                                                 height=6, width=50)
        self.learner_listbox.pack(fill="x", padx=10, pady=5)
        self.learner_listbox.bind("<<ListboxSelect>>",
                                  self._on_learner_select, add="+")

        AccessibleLabel(tab, text="Progress:",
                        font=("Arial", 12, "bold")).pack(padx=10, anchor="w")
        self.progress_frame = tk.Frame(tab)
        self.progress_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self._refresh_learners_list()

    def _refresh_learners_list(self):
        self.learner_listbox.delete(0, tk.END)
        self._learners = self.ctrl.get_my_learners(self.user.user_id)
        for l in self._learners:
            self.learner_listbox.insert(
                tk.END, f"{l.name} ({l.username}) - {l.vision_type}")

    def _on_learner_select(self, event):
        sel = self.learner_listbox.curselection()
        if not sel:
            return
        learner = self._learners[sel[0]]
        self._show_learner_progress(learner)

    def _show_learner_progress(self, learner):
        clear_frame(self.progress_frame)
        assignments = self.ctrl.get_learner_assignments(learner.user_id)
        if not assignments:
            AccessibleLabel(self.progress_frame,
                            text="No assignments yet.").pack()
            if self.tts:
                self.tts.speak(
                    f"Selected Learner: {learner.name}. No assignments yet.")
            return

        for a in assignments:
            path = self.ctrl.get_path_by_id(a.path_id)
            completed, total = self.ctrl.get_progress(a.assignment_id)
            path_name = path.title if path else f"Path {a.path_id}"

            row = tk.Frame(self.progress_frame)
            row.pack(fill="x", pady=3)
            AccessibleLabel(row,
                            text=f"{path_name}: {completed} out of "
                                 f"{total} courses consumed").pack(
                                     side="left")

            # Progress bar
            bar = ttk.Progressbar(row, length=200, maximum=max(total, 1),
                                  value=completed)
            bar.pack(side="left", padx=10)

        if self.tts:
            a0 = assignments[0]
            path0 = self.ctrl.get_path_by_id(a0.path_id)
            c0, t0 = self.ctrl.get_progress(a0.assignment_id)
            name0 = path0.title if path0 else "their path"
            self.tts.speak(
                f"Selected Learner: {learner.name}. "
                f"Completed {c0} out of {t0} courses in {name0}.")

    def _register_learner_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Register New Learner")
        dlg.grab_set()
        self.ctx.accessibility.apply_theme(dlg)

        fields = [("Name", "name"), ("Username", "username"),
                  ("Email", "email"), ("Password", "password")]
        entries = {}
        for i, (label, key) in enumerate(fields):
            AccessibleLabel(dlg, text=f"{label}:").grid(
                row=i, column=0, padx=10, pady=4, sticky="e")
            entry = AccessibleEntry(dlg, tts=self.tts, label_text=label,
                                    width=30,
                                    show="*" if key == "password" else "")
            entry.grid(row=i, column=1, padx=10, pady=4)
            entries[key] = entry

        row = len(fields)
        AccessibleLabel(dlg, text="Vision Type:").grid(
            row=row, column=0, padx=10, pady=4, sticky="e")
        vision_var = tk.StringVar(value="blind")
        acc_audio = tk.BooleanVar(value=True)
        acc_contrast = tk.BooleanVar(value=False)
        acc_large = tk.BooleanVar(value=False)

        def on_vision_change(event=None):
            if vision_var.get() == "blind":
                acc_audio.set(True)
                acc_contrast.set(False)
                acc_large.set(False)
            elif vision_var.get() == "low_vision":
                acc_audio.set(False)
                acc_contrast.set(True)
                acc_large.set(True)

        vision_combo = ttk.Combobox(
            dlg, textvariable=vision_var,
            values=["blind", "low_vision"], state="readonly", width=27)
        vision_combo.grid(row=row, column=1, padx=10, pady=4)
        vision_combo.bind("<<ComboboxSelected>>", on_vision_change)

        AccessibleLabel(dlg, text="Accessibility:").grid(
            row=row + 1, column=0, padx=10, pady=4, sticky="ne")
        acc_frame = tk.Frame(dlg)
        acc_frame.grid(row=row + 1, column=1, sticky="w", padx=10)
        tk.Checkbutton(acc_frame, text="Audio (TTS)",
                       variable=acc_audio).pack(anchor="w")
        tk.Checkbutton(acc_frame, text="High Contrast",
                       variable=acc_contrast).pack(anchor="w")
        tk.Checkbutton(acc_frame, text="Large Text",
                       variable=acc_large).pack(anchor="w")

        AccessibleLabel(dlg, text="STEM Interests:").grid(
            row=row + 2, column=0, padx=10, pady=4, sticky="ne")
        interest_frame = tk.Frame(dlg)
        interest_frame.grid(row=row + 2, column=1, sticky="w", padx=10)
        interest_vars = {}
        for field in STEM_FIELDS:
            var = tk.BooleanVar(value=False)
            tk.Checkbutton(interest_frame, text=field,
                           variable=var).pack(anchor="w")
            interest_vars[field] = var

        def save():
            vals = {k: e.get().strip() for k, e in entries.items()}
            if not all(vals.values()):
                messagebox.showwarning("Missing", "Fill all fields.")
                return
            interests = [f for f, v in interest_vars.items() if v.get()]
            try:
                self.ctrl.register_learner(
                    username=vals["username"], email=vals["email"],
                    password=vals["password"], name=vals["name"],
                    mentor_id=self.user.user_id,
                    vision_type=vision_var.get(),
                    accessibility_prefs={"audio": acc_audio.get(),
                                         "high_contrast": acc_contrast.get(),
                                         "large_text": acc_large.get()},
                    stem_interests=interests)
                dlg.destroy()
                self._refresh_learners_list()
                if self.tts:
                    self.tts.speak(f"Learner {vals['name']} registered.")
                messagebox.showinfo("Success",
                                    f"Learner {vals['name']} registered.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        AccessibleButton(dlg, tts=self.tts, text="Register",
                         command=save).grid(row=row + 3, column=1, pady=10,
                                            sticky="e", padx=10)

    # ------------------------------------------------------------------ #
    # Tab 3: Opportunities
    # ------------------------------------------------------------------ #
    def get_help_text(self):
        """Return F1 help text describing the current location and navigation."""
        try:
            tab_id = self.notebook.select()
            tab_name = self.notebook.tab(tab_id, "text")
        except Exception:
            tab_id, tab_name = None, "unknown"

        base = f"You are on the Mentor Dashboard, {tab_name} tab. "
        return base + self._tab_help.get(tab_id, (
            "Press Tab to move between controls. "
            "Press Escape to return to the login screen."
        ))

    def _build_opportunities_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="Opportunities")
        self._tab_help[str(tab)] = (
            "This tab lists internship and academic opportunities. "
            "Use the Post New Opportunity button to create a new one. "
            "Select an opportunity from the list to see its details. "
            "Press Tab to move between controls. "
            "Press Control Tab to go to the next tab, or Control Shift Tab to go to the previous tab. "
            "Press Escape to return to the login screen."
        )

        AccessibleButton(tab, tts=self.tts, text="Post New Opportunity",
                         command=self._post_opportunity_dialog).pack(
                             padx=10, pady=10, anchor="w")

        self.opp_listbox = AccessibleListbox(tab, tts=self.tts,
                                             item_noun="Opportunity",
                                             height=10, width=60)
        self.opp_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.opp_listbox.bind("<<ListboxSelect>>", self._on_opp_select,
                              add="+")

        self.opp_detail = AccessibleLabel(tab, text="", wraplength=500,
                                          justify="left")
        self.opp_detail.pack(padx=10, pady=5, anchor="w")

        self._refresh_opportunities()

    def _refresh_opportunities(self):
        self.opp_listbox.delete(0, tk.END)
        self._opportunities = self.ctrl.get_all_opportunities()
        for o in self._opportunities:
            self.opp_listbox.insert(tk.END,
                                    f"[{o.opp_type.upper()}] {o.title}")

    def _on_opp_select(self, event):
        sel = self.opp_listbox.curselection()
        if not sel:
            return
        opp = self._opportunities[sel[0]]
        self.opp_detail.configure(text=opp.description)
        if self.tts:
            self.tts.speak(
                f"Selected Opportunity: {opp.title}. {opp.description}")

    def _post_opportunity_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Post Opportunity")
        dlg.grab_set()
        self.ctx.accessibility.apply_theme(dlg)

        AccessibleLabel(dlg, text="Title:").grid(row=0, column=0, padx=10,
                                                  pady=5, sticky="e")
        title_entry = AccessibleEntry(dlg, tts=self.tts, label_text="Title",
                                      width=40)
        title_entry.grid(row=0, column=1, padx=10, pady=5)

        AccessibleLabel(dlg, text="Type:").grid(row=1, column=0, padx=10,
                                                 pady=5, sticky="e")
        type_var = tk.StringVar(value="internship")
        ttk.Combobox(dlg, textvariable=type_var,
                     values=["internship", "academic"], state="readonly",
                     width=37).grid(row=1, column=1, padx=10, pady=5)

        AccessibleLabel(dlg, text="Description:").grid(row=2, column=0,
                                                        padx=10, pady=5,
                                                        sticky="ne")
        desc_text = AccessibleText(dlg, tts=self.tts,
                                   label_text="Description",
                                   width=40, height=6)
        desc_text.grid(row=2, column=1, padx=10, pady=5)

        def save():
            t = title_entry.get().strip()
            d = desc_text.get("1.0", tk.END).strip()
            if not t:
                messagebox.showwarning("Missing", "Title is required.")
                return
            self.ctrl.post_opportunity(t, d, type_var.get(),
                                       self.user.user_id)
            dlg.destroy()
            self._refresh_opportunities()
            if self.tts:
                self.tts.speak("Opportunity posted.")

        AccessibleButton(dlg, tts=self.tts, text="Post",
                         command=save).grid(row=3, column=1, pady=10,
                                            sticky="e", padx=10)
