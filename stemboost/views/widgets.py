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


class AccessibleListbox(tk.Listbox):
    """A listbox that announces selected item via TTS.

    `item_noun` names what each row represents (e.g. "Learning Path",
    "Course") and is used in the selection announcement.
    """

    def __init__(self, parent, tts=None, item_noun="item", **kwargs):
        super().__init__(parent, **kwargs)
        self.tts = tts
        self.item_noun = item_noun
        self.configure(takefocus=True)
        if tts:
            self.bind("<<ListboxSelect>>", self._on_select)

    def _on_select(self, event):
        if self.tts:
            sel = self.curselection()
            if sel:
                text = self.get(sel[0])
                self.tts.speak(f"Selected {self.item_noun}: {text}")


def clear_frame(frame):
    """Destroy all children of a frame."""
    for child in frame.winfo_children():
        child.destroy()
