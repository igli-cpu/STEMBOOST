import tkinter as tk


class AccessibleButton(tk.Button):
    """A button that announces its label via TTS on focus."""

    def __init__(self, parent, tts=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.tts = tts
        self.configure(
            relief="raised", bd=2, padx=16, pady=8,
            cursor="hand2", takefocus=True,
        )
        if tts:
            self.bind("<FocusIn>", self._on_focus)

    def _on_focus(self, event):
        if self.tts:
            label = self.cget("text")
            self.tts.speak(f"Button: {label}")


class AccessibleLabel(tk.Label):
    """A label that can announce itself via TTS on focus."""

    def __init__(self, parent, tts=None, announce=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.tts = tts
        if announce and tts:
            self.configure(takefocus=True)
            self.bind("<FocusIn>", self._on_focus)

    def _on_focus(self, event):
        if self.tts:
            self.tts.speak(self.cget("text"))


class AccessibleEntry(tk.Entry):
    """An entry field that announces its purpose via TTS on focus."""

    def __init__(self, parent, tts=None, label_text="", **kwargs):
        super().__init__(parent, **kwargs)
        self.tts = tts
        self.label_text = label_text
        self.configure(takefocus=True)
        if tts:
            self.bind("<FocusIn>", self._on_focus)

    def _on_focus(self, event):
        if self.tts and self.label_text:
            self.tts.speak(f"Text field: {self.label_text}")


class AccessibleText(tk.Text):
    """A text widget that announces its purpose via TTS on focus."""

    def __init__(self, parent, tts=None, label_text="", **kwargs):
        super().__init__(parent, **kwargs)
        self.tts = tts
        self.label_text = label_text
        self.configure(takefocus=True)
        if tts:
            self.bind("<FocusIn>", self._on_focus)

    def _on_focus(self, event):
        if self.tts and self.label_text:
            self.tts.speak(f"Text area: {self.label_text}")


class AccessibleCheckbutton(tk.Checkbutton):
    """A checkbox that announces its label and state on focus and on toggle.

    Pass a `tk.BooleanVar` via `variable=...` so the announced state can
    reflect the actual checked/unchecked value. The caller's `command`
    callback (if any) still runs on toggle; this class wraps it to also
    speak the new state after the toggle completes.
    """

    def __init__(self, parent, tts=None, **kwargs):
        self.tts = tts
        self._var = kwargs.get("variable")
        original_cmd = kwargs.pop("command", None)

        def wrapped_cmd():
            if original_cmd is not None:
                original_cmd()
            self._announce_state()

        kwargs["command"] = wrapped_cmd
        super().__init__(parent, **kwargs)
        self.configure(takefocus=True)
        if tts:
            self.bind("<FocusIn>", self._on_focus)

    def _on_focus(self, event):
        self._announce_state()

    def _announce_state(self):
        if not self.tts:
            return
        label = self.cget("text")
        if self._var is not None:
            state = "checked" if self._var.get() else "unchecked"
            self.tts.speak(f"Checkbox: {label}, {state}")
        else:
            self.tts.speak(f"Checkbox: {label}")


class AccessibleListbox(tk.Listbox):
    """A listbox designed for keyboard-only, screen-reader usage.

    Interaction model:
      * Tab or Down advances the cursor to the next item.
      * Shift+Tab or Up moves the cursor to the previous item.
      * At the last item, Tab exits the listbox forward; at the first
        item, Shift+Tab exits backward.
      * Enter selects the current cursor item and fires `on_activate`.
      * Mouse click also selects + fires `on_activate`.

    `item_noun` names what each row represents (e.g. "Assigned Path",
    "Course") and is used in TTS announcements.

    The caller passes an `on_activate(event)` callback that runs when
    the user commits a selection via Enter or click. Moving the cursor
    with Tab/arrow keys announces the new item but does NOT call
    `on_activate` — so browsing the list doesn't trigger side effects
    like loading related data.
    """

    def __init__(self, parent, tts=None, item_noun="item",
                 on_activate=None, **kwargs):
        kwargs.setdefault("selectmode", "single")
        super().__init__(parent, **kwargs)
        self.tts = tts
        self.item_noun = item_noun
        self._on_activate = on_activate
        self.configure(takefocus=True)
        self.bind("<FocusIn>", self._on_focus)
        self.bind("<<ListboxSelect>>", self._on_select)
        self.bind("<Tab>", self._on_tab_key)
        self.bind("<Shift-Tab>", self._on_shift_tab_key)
        self.bind("<ISO_Left_Tab>", self._on_shift_tab_key)
        self.bind("<Down>", self._on_down_key)
        self.bind("<Up>", self._on_up_key)
        self.bind("<Return>", self._on_return_key)

    # ---- cursor helpers ------------------------------------------------ #
    def _get_active_idx(self):
        try:
            idx = int(self.index("active"))
        except (tk.TclError, ValueError):
            return 0
        size = self.size()
        if size == 0:
            return 0
        return max(0, min(idx, size - 1))

    def _set_active_idx(self, idx):
        size = self.size()
        if size == 0:
            return 0
        idx = max(0, min(idx, size - 1))
        self.activate(idx)
        self.see(idx)
        return idx

    def _announce_current_item(self):
        if not self.tts or self.size() == 0:
            return
        idx = self._get_active_idx()
        try:
            self.tts.speak(self.get(idx))
        except tk.TclError:
            pass

    def _activate_idx(self, idx):
        if idx < 0 or idx >= self.size():
            return
        if self.tts:
            self.tts.speak(f"Selected {self.item_noun}: {self.get(idx)}")
        if self._on_activate is not None:
            self._on_activate(None)

    # ---- event handlers ----------------------------------------------- #
    def _on_focus(self, event):
        if not self.tts:
            return
        size = self.size()
        if size == 0:
            self.tts.speak(f"{self.item_noun} list is empty.")
            return
        # Ensure the cursor starts at the first item so the user can
        # press Enter immediately to select it.
        self._set_active_idx(self._get_active_idx())
        first = self.get(self._get_active_idx())
        self.tts.speak(
            f"{self.item_noun} list, {size} items. "
            f"First item: {first}. "
            "Press Tab or Down arrow to move through items, "
            "Enter to select.")

    def _on_select(self, event):
        """Fires on mouse click (and Space in single mode)."""
        sel = self.curselection()
        if sel:
            self._activate_idx(sel[0])

    def _on_tab_key(self, event):
        # Tkinter's <Tab> pattern also matches Shift+Tab because
        # unmentioned modifiers are don't-cares. Route Shift+Tab to the
        # reverse handler.
        if event.state & 0x1:
            return self._on_shift_tab_key(event)
        size = self.size()
        if size == 0:
            return None  # let default tab traversal run
        active = self._get_active_idx()
        if active < size - 1:
            self._set_active_idx(active + 1)
            self._announce_current_item()
            return "break"
        return None  # at end — let default traversal exit the listbox

    def _on_shift_tab_key(self, event):
        size = self.size()
        if size == 0:
            return None
        active = self._get_active_idx()
        if active > 0:
            self._set_active_idx(active - 1)
            self._announce_current_item()
            return "break"
        return None  # at start — let default traversal exit backward

    def _on_down_key(self, event):
        if self.size() == 0:
            return "break"
        active = self._get_active_idx()
        self._set_active_idx(active + 1)
        self._announce_current_item()
        return "break"

    def _on_up_key(self, event):
        if self.size() == 0:
            return "break"
        active = self._get_active_idx()
        self._set_active_idx(active - 1)
        self._announce_current_item()
        return "break"

    def _on_return_key(self, event):
        if self.size() == 0:
            return "break"
        active = self._get_active_idx()
        self.selection_clear(0, tk.END)
        self.selection_set(active)
        self._activate_idx(active)
        return "break"


def clear_frame(frame):
    """Destroy all children of a frame."""
    for child in frame.winfo_children():
        child.destroy()
