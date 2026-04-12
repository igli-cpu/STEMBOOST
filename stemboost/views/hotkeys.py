"""Hotkey command table — Command pattern over Tk's bind_all.

Each :class:`Hotkey` encapsulates the triple (key binding, description,
action) plus an optional *guard* that decides whether the hotkey should
fire given the currently focused widget. Registering hotkeys is a loop
over a list instead of a block of scattered ``bind_all`` calls, which
means:

* The F1 help text is auto-generated from the list — it can never drift
  from the actual bindings.
* Adding a new hotkey is a one-line data change, not a code change to
  main.py, so :class:`StemboostApp` stays closed to modification.

The guard mechanism replaces the old ``_TYPING_WIDGETS`` /
``_SPACE_ACTIVATED_WIDGETS`` sets. Each hotkey declares its own policy:
"don't fire when focus is on an Entry", "always fire", etc.
"""

from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional


# Widget classes that need to handle keys themselves rather than let us
# hijack them globally.
TYPING_WIDGETS = frozenset({"Entry", "TEntry", "Text", "TCombobox",
                            "Combobox"})
SPACE_ACTIVATED_WIDGETS = frozenset({
    "Button", "TButton", "Checkbutton", "TCheckbutton",
    "Radiobutton", "TRadiobutton",
})


def stand_down_for_typing(focused_class):
    """Guard: suppress the hotkey if focus is on a typing widget."""
    return focused_class not in TYPING_WIDGETS


def stand_down_for_space_consumers(focused_class):
    """Guard: suppress the hotkey if focus is on a widget that uses
    space for its own activation (button, checkbox, radio)."""
    return (focused_class not in TYPING_WIDGETS
            and focused_class not in SPACE_ACTIVATED_WIDGETS)


def always_fire(focused_class):
    return True


@dataclass
class Hotkey:
    """One global keyboard binding.

    * ``keys`` — list of Tk key sequences (e.g. ``["<space>"]``). All
      sequences share the same action, which lets us bind both
      ``<Control-q>`` and ``<Control-Q>`` under one entry.
    * ``description`` — human-readable string used by F1 help.
    * ``action`` — callable taking no args.
    * ``guard`` — optional predicate on the focused widget's class name.
      If it returns False, the hotkey stands down and lets the widget
      handle the key normally.
    """

    keys: Iterable[str]
    description: str
    action: Callable[[], None]
    guard: Callable[[str], bool] = field(default=always_fire)


class HotkeyRegistry:
    """Owns a list of hotkeys and installs them on a Tk root."""

    def __init__(self, root, focus_class_provider):
        """focus_class_provider() -> str, the class name of the current
        focus widget (used by guards)."""
        self._root = root
        self._focus_class = focus_class_provider
        self._hotkeys: list[Hotkey] = []

    def register(self, hotkey: Hotkey):
        self._hotkeys.append(hotkey)
        for key in hotkey.keys:
            self._root.bind_all(key, self._make_handler(hotkey))

    def register_all(self, hotkeys: Iterable[Hotkey]):
        for h in hotkeys:
            self.register(h)

    def _make_handler(self, hotkey: Hotkey):
        def handler(event):
            if not hotkey.guard(self._focus_class()):
                return  # let the widget handle the key
            hotkey.action()
            return "break"
        return handler

    def help_text(self):
        """Generate the F1 help narration from the registered hotkeys."""
        lines = [h.description for h in self._hotkeys if h.description]
        return " ".join(lines)
