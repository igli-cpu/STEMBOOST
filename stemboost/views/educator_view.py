import tkinter as tk
from tkinter import ttk, messagebox

from stemboost.views.widgets import (AccessibleButton, AccessibleLabel,
                                     AccessibleEntry, AccessibleText,
                                     AccessibleListbox, clear_frame)
from stemboost.models.assessment import Assessment


CATEGORIES = [
    "Job Exploration",
    "Post-Secondary Education",
    "Workplace Readiness",
    "Work-Based Learning",
]


class EducatorView(tk.Frame):
    """Educator dashboard: manage learning paths, courses, and content."""

    def __init__(self, parent, app, user):
        super().__init__(parent)
        self.app = app
        self.tts = app.tts
        self.user = user
        self.ctrl = app.educator_ctrl
        self._selected_path = None
        self._selected_course = None
        self._build()

    def _build(self):
        clear_frame(self)

        # Header
        header = tk.Frame(self)
        header.pack(fill="x", padx=10, pady=5)
        AccessibleLabel(header, text=f"Educator: {self.user.name}",
                        font=("Arial", 16, "bold")).pack(side="left")
        AccessibleButton(header, tts=self.tts, text="Logout",
                         command=self.app.show_login).pack(side="right")
        AccessibleButton(header, tts=self.tts, text="Update Expertise",
                         command=self._show_expertise).pack(side="right", padx=5)

        # Main area with three columns: Paths | Courses | Content
        main = tk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # -- Paths column --
        path_frame = tk.LabelFrame(main, text="Learning Paths", padx=5, pady=5)
        path_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.path_listbox = AccessibleListbox(path_frame, tts=self.tts,
                                              height=15, width=30)
        self.path_listbox.pack(fill="both", expand=True)
        self.path_listbox.bind("<<ListboxSelect>>", self._on_path_select)

        btn_row = tk.Frame(path_frame)
        btn_row.pack(fill="x", pady=5)
        AccessibleButton(btn_row, tts=self.tts, text="New Path",
                         command=self._new_path).pack(side="left", padx=2)
        AccessibleButton(btn_row, tts=self.tts, text="Edit",
                         command=self._edit_path).pack(side="left", padx=2)
        AccessibleButton(btn_row, tts=self.tts, text="Delete",
                         command=self._delete_path).pack(side="left", padx=2)

        # -- Courses column --
        course_frame = tk.LabelFrame(main, text="Courses", padx=5, pady=5)
        course_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.course_listbox = AccessibleListbox(course_frame, tts=self.tts,
                                                height=15, width=30)
        self.course_listbox.pack(fill="both", expand=True)
        self.course_listbox.bind("<<ListboxSelect>>", self._on_course_select)

        btn_row2 = tk.Frame(course_frame)
        btn_row2.pack(fill="x", pady=5)
        AccessibleButton(btn_row2, tts=self.tts, text="New Course",
                         command=self._new_course).pack(side="left", padx=2)
        AccessibleButton(btn_row2, tts=self.tts, text="Edit",
                         command=self._edit_course).pack(side="left", padx=2)
        AccessibleButton(btn_row2, tts=self.tts, text="Delete",
                         command=self._delete_course).pack(side="left", padx=2)

        # -- Content column --
        content_frame = tk.LabelFrame(main, text="Content", padx=5, pady=5)
        content_frame.pack(side="left", fill="both", expand=True, padx=5)

        self.content_listbox = AccessibleListbox(content_frame, tts=self.tts,
                                                 height=15, width=30)
        self.content_listbox.pack(fill="both", expand=True)

        btn_row3 = tk.Frame(content_frame)
        btn_row3.pack(fill="x", pady=5)
        AccessibleButton(btn_row3, tts=self.tts, text="New Content",
                         command=self._new_content).pack(side="left", padx=2)
        AccessibleButton(btn_row3, tts=self.tts, text="Edit",
                         command=self._edit_content).pack(side="left", padx=2)
        AccessibleButton(btn_row3, tts=self.tts, text="Delete",
                         command=self._delete_content).pack(side="left", padx=2)

        self._refresh_paths()
        if self.tts:
            self.tts.speak("Educator dashboard. You can manage learning paths, "
                           "courses, and content.")

    def _refresh_paths(self):
        self.path_listbox.delete(0, tk.END)
        self._paths = self.ctrl.get_my_paths(self.user.user_id)
        for p in self._paths:
            self.path_listbox.insert(tk.END, f"{p.title} [{p.category}]")
        self._selected_path = None
        self.course_listbox.delete(0, tk.END)
        self.content_listbox.delete(0, tk.END)

    def _on_path_select(self, event):
        sel = self.path_listbox.curselection()
        if not sel:
            return
        self._selected_path = self._paths[sel[0]]
        self._refresh_courses()

    def _refresh_courses(self):
        self.course_listbox.delete(0, tk.END)
        self.content_listbox.delete(0, tk.END)
        if not self._selected_path:
            return
        self._courses = self.ctrl.get_courses(self._selected_path.path_id)
        for c in self._courses:
            self.course_listbox.insert(tk.END, c.title)
        self._selected_course = None

    def _on_course_select(self, event):
        sel = self.course_listbox.curselection()
        if not sel:
            return
        self._selected_course = self._courses[sel[0]]
        self._refresh_contents()

    def _refresh_contents(self):
        self.content_listbox.delete(0, tk.END)
        if not self._selected_course:
            return
        self._contents = self.ctrl.get_contents(self._selected_course.course_id)
        for c in self._contents:
            self.content_listbox.insert(tk.END, c.title)

    # ---- Path CRUD dialogs ----
    def _new_path(self):
        self._path_dialog("Create Learning Path")

    def _edit_path(self):
        if not self._selected_path:
            messagebox.showinfo("Select", "Select a path first.")
            return
        self._path_dialog("Edit Learning Path", self._selected_path)

    def _path_dialog(self, title, path=None):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.grab_set()

        AccessibleLabel(dlg, text="Title:").grid(row=0, column=0, padx=10,
                                                  pady=5, sticky="e")
        title_entry = AccessibleEntry(dlg, tts=self.tts, label_text="Title",
                                      width=40)
        title_entry.grid(row=0, column=1, padx=10, pady=5)

        AccessibleLabel(dlg, text="Description:").grid(row=1, column=0,
                                                        padx=10, pady=5,
                                                        sticky="ne")
        desc_text = AccessibleText(dlg, tts=self.tts,
                                   label_text="Description",
                                   width=40, height=4)
        desc_text.grid(row=1, column=1, padx=10, pady=5)

        AccessibleLabel(dlg, text="Category:").grid(row=2, column=0, padx=10,
                                                     pady=5, sticky="e")
        cat_var = tk.StringVar(value=CATEGORIES[0])
        ttk.Combobox(dlg, textvariable=cat_var, values=CATEGORIES,
                     state="readonly", width=37).grid(row=2, column=1,
                                                       padx=10, pady=5)

        if path:
            title_entry.insert(0, path.title)
            desc_text.insert("1.0", path.description)
            cat_var.set(path.category)

        def save():
            t = title_entry.get().strip()
            d = desc_text.get("1.0", tk.END).strip()
            c = cat_var.get()
            if not t:
                messagebox.showwarning("Missing", "Title is required.")
                return
            if path:
                self.ctrl.update_path(path.path_id, t, d, c)
            else:
                self.ctrl.create_path(t, d, c, self.user.user_id)
            dlg.destroy()
            self._refresh_paths()
            if self.tts:
                self.tts.speak("Learning path saved.")

        AccessibleButton(dlg, tts=self.tts, text="Save",
                         command=save).grid(row=3, column=1, pady=10,
                                            sticky="e", padx=10)

    def _delete_path(self):
        if not self._selected_path:
            return
        if messagebox.askyesno("Delete",
                               f"Delete '{self._selected_path.title}'?"):
            self.ctrl.delete_path(self._selected_path.path_id)
            self._refresh_paths()
            if self.tts:
                self.tts.speak("Path deleted.")

    # ---- Course CRUD dialogs ----
    def _new_course(self):
        if not self._selected_path:
            messagebox.showinfo("Select", "Select a learning path first.")
            return
        self._course_dialog("Create Course")

    def _edit_course(self):
        if not self._selected_course:
            messagebox.showinfo("Select", "Select a course first.")
            return
        self._course_dialog("Edit Course", self._selected_course)

    def _course_dialog(self, title, course=None):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.grab_set()

        AccessibleLabel(dlg, text="Title:").grid(row=0, column=0, padx=10,
                                                  pady=5, sticky="e")
        title_entry = AccessibleEntry(dlg, tts=self.tts, label_text="Title",
                                      width=40)
        title_entry.grid(row=0, column=1, padx=10, pady=5)

        AccessibleLabel(dlg, text="Description:").grid(row=1, column=0,
                                                        padx=10, pady=5,
                                                        sticky="ne")
        desc_text = AccessibleText(dlg, tts=self.tts,
                                   label_text="Description",
                                   width=40, height=4)
        desc_text.grid(row=1, column=1, padx=10, pady=5)

        if course:
            title_entry.insert(0, course.title)
            desc_text.insert("1.0", course.description)

        def save():
            t = title_entry.get().strip()
            d = desc_text.get("1.0", tk.END).strip()
            if not t:
                messagebox.showwarning("Missing", "Title is required.")
                return
            if course:
                self.ctrl.update_course(course.course_id, t, d)
            else:
                order = len(self._courses) + 1 if hasattr(self, '_courses') else 1
                self.ctrl.create_course(t, d, self._selected_path.path_id,
                                        self.user.user_id, order)
            dlg.destroy()
            self._refresh_courses()
            if self.tts:
                self.tts.speak("Course saved.")

        AccessibleButton(dlg, tts=self.tts, text="Save",
                         command=save).grid(row=2, column=1, pady=10,
                                            sticky="e", padx=10)

    def _delete_course(self):
        if not self._selected_course:
            return
        if messagebox.askyesno("Delete",
                               f"Delete '{self._selected_course.title}'?"):
            self.ctrl.delete_course(self._selected_course.course_id)
            self._refresh_courses()
            if self.tts:
                self.tts.speak("Course deleted.")

    # ---- Content CRUD dialogs ----
    def _new_content(self):
        if not self._selected_course:
            messagebox.showinfo("Select", "Select a course first.")
            return
        self._content_dialog("Create Content")

    def _edit_content(self):
        sel = self.content_listbox.curselection()
        if not sel:
            messagebox.showinfo("Select", "Select a content unit first.")
            return
        content = self._contents[sel[0]]
        self._content_dialog("Edit Content", content)

    def _content_dialog(self, title, content=None):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.grab_set()

        AccessibleLabel(dlg, text="Title:").grid(row=0, column=0, padx=10,
                                                  pady=5, sticky="e")
        title_entry = AccessibleEntry(dlg, tts=self.tts, label_text="Title",
                                      width=50)
        title_entry.grid(row=0, column=1, padx=10, pady=5)

        AccessibleLabel(dlg, text="Content Text:").grid(row=1, column=0,
                                                         padx=10, pady=5,
                                                         sticky="ne")
        body_text = AccessibleText(dlg, tts=self.tts,
                                   label_text="Content body",
                                   width=50, height=10)
        body_text.grid(row=1, column=1, padx=10, pady=5)

        if content:
            title_entry.insert(0, content.title)
            body_text.insert("1.0", content.text_body)

        def save():
            t = title_entry.get().strip()
            b = body_text.get("1.0", tk.END).strip()
            if not t:
                messagebox.showwarning("Missing", "Title is required.")
                return
            if content:
                self.ctrl.update_content(content.content_id, t, b)
            else:
                order = len(self._contents) + 1 if hasattr(self, '_contents') else 1
                self.ctrl.create_content(t, b,
                                         self._selected_course.course_id,
                                         self.user.user_id, order)
            dlg.destroy()
            self._refresh_contents()
            if self.tts:
                self.tts.speak("Content saved.")

        AccessibleButton(dlg, tts=self.tts, text="Save",
                         command=save).grid(row=2, column=1, pady=10,
                                            sticky="e", padx=10)

    def _delete_content(self):
        sel = self.content_listbox.curselection()
        if not sel:
            return
        content = self._contents[sel[0]]
        if messagebox.askyesno("Delete", f"Delete '{content.title}'?"):
            self.ctrl.delete_content(content.content_id)
            self._refresh_contents()
            if self.tts:
                self.tts.speak("Content deleted.")

    # ---- Expertise dialog ----
    def _show_expertise(self):
        dlg = tk.Toplevel(self)
        dlg.title("Update Expertise Areas")
        dlg.grab_set()

        current = self.ctrl.get_expertise(self.user.user_id)
        exp_vars = {}
        for i, field in enumerate(Assessment.STEM_FIELDS):
            var = tk.BooleanVar(value=(field in current))
            tk.Checkbutton(dlg, text=field, variable=var).grid(
                row=i, column=0, sticky="w", padx=20, pady=2)
            exp_vars[field] = var

        def save():
            areas = [f for f, v in exp_vars.items() if v.get()]
            self.ctrl.update_expertise(self.user.user_id, areas)
            self.user.expertise_areas = areas
            dlg.destroy()
            if self.tts:
                self.tts.speak("Expertise areas updated.")

        AccessibleButton(dlg, tts=self.tts, text="Save",
                         command=save).grid(row=len(Assessment.STEM_FIELDS),
                                            column=0, pady=10)
