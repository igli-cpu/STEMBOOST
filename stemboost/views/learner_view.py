import tkinter as tk
from tkinter import ttk, messagebox

from stemboost.views.widgets import (AccessibleButton, AccessibleLabel,
                                     AccessibleListbox, clear_frame)
from stemboost.services.observer import ProgressObserver
from stemboost.models.assessment import Assessment


# STEM career path information (REQ-L-008)
CAREER_PATHS = {
    "Computer Science": (
        "Computer Science careers include software developer, systems architect, "
        "cybersecurity analyst, and database administrator. The field is growing "
        "rapidly with strong demand across all industries. Many roles offer "
        "remote work options and competitive salaries."
    ),
    "Data Science": (
        "Data Science combines statistics, programming, and domain expertise. "
        "Roles include data analyst, machine learning engineer, and business "
        "intelligence specialist. Data scientists are in high demand in "
        "healthcare, finance, and technology sectors."
    ),
    "Mathematics": (
        "Mathematics careers span academia, finance, and technology. "
        "Actuaries, statisticians, and operations researchers use math daily. "
        "Strong math skills are foundational for careers in engineering, "
        "physics, and computer science."
    ),
    "Biology": (
        "Biology careers include research scientist, biotechnologist, "
        "environmental consultant, and medical laboratory technician. "
        "Growing fields include genomics, bioinformatics, and conservation "
        "biology."
    ),
    "Engineering": (
        "Engineering spans many specializations: mechanical, electrical, "
        "civil, chemical, and biomedical. Engineers design, build, and "
        "optimize systems and structures. The field offers hands-on problem "
        "solving and strong job prospects."
    ),
    "Physics": (
        "Physics careers range from research and academia to applied roles "
        "in engineering, medical physics, and data analysis. Understanding "
        "physics is valuable in aerospace, energy, and technology sectors."
    ),
    "Chemistry": (
        "Chemistry careers include pharmaceutical research, materials "
        "science, environmental analysis, and quality control. Chemists "
        "work in labs, manufacturing, and regulatory agencies."
    ),
    "Environmental Science": (
        "Environmental Science careers focus on sustainability, conservation, "
        "and pollution management. Roles include environmental consultant, "
        "climate analyst, and conservation scientist."
    ),
}


class LearnerProgressObserver(ProgressObserver):
    """Observer that updates the learner view when progress changes."""

    def __init__(self, view):
        self.view = view

    def on_progress_update(self, learner_id, assignment_id, completed, total):
        if hasattr(self.view, '_refresh_progress_display'):
            self.view._refresh_progress_display()


class LearnerView(tk.Frame):
    """Learner dashboard: view assignments, consume content, track progress."""

    def __init__(self, parent, app, user):
        super().__init__(parent)
        self.app = app
        self.tts = app.tts
        self.user = user
        self.ctrl = app.learner_ctrl

        # Register as observer for progress updates
        self._observer = LearnerProgressObserver(self)
        self.ctrl.progress_subject.attach(self._observer)

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

        # Notebook tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=5)

        self._build_assignments_tab(notebook)
        self._build_progress_tab(notebook)
        self._build_careers_tab(notebook)
        self._build_opportunities_tab(notebook)

        if self.tts:
            self.tts.speak(
                f"Welcome, {self.user.name}. Your learner dashboard is ready. "
                "Use the tabs to view your assignments, progress, STEM careers, "
                "or opportunities.")

    def _logout(self):
        self.ctrl.progress_subject.detach(self._observer)
        self.app.show_login()

    # ------------------------------------------------------------------ #
    # Tab 1: My Assignments
    # ------------------------------------------------------------------ #
    def _build_assignments_tab(self, notebook):
        tab = tk.Frame(notebook)
        notebook.add(tab, text="My Assignments")

        left = tk.Frame(tab)
        left.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        AccessibleLabel(left, text="Assigned Paths",
                        font=("Arial", 12, "bold")).pack()
        self.assign_listbox = AccessibleListbox(left, tts=self.tts,
                                                height=8, width=40)
        self.assign_listbox.pack(fill="both", expand=True, pady=5)
        self.assign_listbox.bind("<<ListboxSelect>>",
                                 self._on_assignment_select)

        right = tk.Frame(tab)
        right.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        AccessibleLabel(right, text="Courses",
                        font=("Arial", 12, "bold")).pack()
        self.course_listbox = AccessibleListbox(right, tts=self.tts,
                                                height=8, width=40)
        self.course_listbox.pack(fill="both", expand=True, pady=5)

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

        left = tk.Frame(tab)
        left.pack(side="left", fill="y", padx=5, pady=5)

        AccessibleLabel(left, text="Career Fields",
                        font=("Arial", 12, "bold")).pack()
        self.career_listbox = AccessibleListbox(left, tts=self.tts,
                                                height=12, width=25)
        self.career_listbox.pack(fill="y", expand=True, pady=5)
        self.career_listbox.bind("<<ListboxSelect>>", self._on_career_select)

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

        self.opp_listbox = AccessibleListbox(tab, tts=self.tts,
                                             height=8, width=60)
        self.opp_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.opp_listbox.bind("<<ListboxSelect>>", self._on_opp_select)

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
    def _show_settings(self):
        dlg = tk.Toplevel(self)
        dlg.title("Accessibility Settings")
        dlg.grab_set()

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
        for field in Assessment.STEM_FIELDS:
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
            self.app.accessibility.update_from_prefs(new_prefs)
            self.app.accessibility.apply_theme(self.app.root)

            dlg.destroy()
            if self.tts:
                self.tts.speak("Settings saved.")

        AccessibleButton(dlg, tts=self.tts, text="Save",
                         command=save).pack(pady=10)
