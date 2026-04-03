import tkinter as tk
import tkinter.font as tkfont


# Default theme colors
THEME_NORMAL = {
    "bg": "#f0f0f0",
    "fg": "#1a1a1a",
    "button_bg": "#e0e0e0",
    "button_fg": "#1a1a1a",
    "entry_bg": "#ffffff",
    "entry_fg": "#1a1a1a",
    "highlight": "#4a90d9",
    "font_size": 12,
}

THEME_HIGH_CONTRAST = {
    "bg": "#000000",
    "fg": "#ffffff",
    "button_bg": "#333333",
    "button_fg": "#ffffff",
    "entry_bg": "#1a1a1a",
    "entry_fg": "#ffffff",
    "highlight": "#ffff00",
    "font_size": 12,
}

THEME_LARGE_TEXT = {
    "bg": "#f0f0f0",
    "fg": "#1a1a1a",
    "button_bg": "#e0e0e0",
    "button_fg": "#1a1a1a",
    "entry_bg": "#ffffff",
    "entry_fg": "#1a1a1a",
    "highlight": "#4a90d9",
    "font_size": 18,
}

THEME_HIGH_CONTRAST_LARGE = {
    "bg": "#000000",
    "fg": "#ffffff",
    "button_bg": "#333333",
    "button_fg": "#ffffff",
    "entry_bg": "#1a1a1a",
    "entry_fg": "#ffffff",
    "highlight": "#ffff00",
    "font_size": 18,
}


class AccessibilityService:
    """Applies accessibility settings (contrast, text size, TTS) to the UI."""

    def __init__(self):
        self.audio_enabled = True
        self.high_contrast = False
        self.large_text = False

    def get_theme(self):
        if self.high_contrast and self.large_text:
            return THEME_HIGH_CONTRAST_LARGE
        elif self.high_contrast:
            return THEME_HIGH_CONTRAST
        elif self.large_text:
            return THEME_LARGE_TEXT
        else:
            return THEME_NORMAL

    def apply_theme(self, widget):
        """Recursively apply the current theme to a widget and its children."""
        theme = self.get_theme()
        self._apply_to_widget(widget, theme)
        for child in widget.winfo_children():
            self.apply_theme(child)

    def _apply_to_widget(self, widget, theme):
        widget_class = widget.winfo_class()
        try:
            if widget_class in ("Frame", "Labelframe", "Toplevel", "Tk"):
                widget.configure(bg=theme["bg"])
            elif widget_class == "Label":
                widget.configure(bg=theme["bg"], fg=theme["fg"],
                                 font=("Arial", theme["font_size"]))
            elif widget_class == "Button":
                widget.configure(bg=theme["button_bg"], fg=theme["button_fg"],
                                 font=("Arial", theme["font_size"]),
                                 activebackground=theme["highlight"],
                                 activeforeground=theme["fg"])
            elif widget_class == "Entry":
                widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"],
                                 font=("Arial", theme["font_size"]),
                                 insertbackground=theme["fg"])
            elif widget_class == "Text":
                widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"],
                                 font=("Arial", theme["font_size"]),
                                 insertbackground=theme["fg"])
            elif widget_class == "Listbox":
                widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"],
                                 font=("Arial", theme["font_size"]),
                                 selectbackground=theme["highlight"])
            elif widget_class in ("TCombobox", "Combobox"):
                pass  # ttk widgets styled differently
        except tk.TclError:
            pass

    def update_from_prefs(self, prefs):
        """Update settings from a learner's accessibility_prefs dict."""
        self.audio_enabled = prefs.get("audio", True)
        self.high_contrast = prefs.get("high_contrast", False)
        self.large_text = prefs.get("large_text", False)
