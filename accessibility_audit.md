# Accessibility Audit: Keyboard/TTS Navigation for Blind Users

## Current State

The application has a foundation of accessible widgets (`AccessibleButton`, `AccessibleEntry`, `AccessibleListbox`, `AccessibleText`) that announce themselves via TTS on focus. However, several critical gaps make the learner interface effectively unusable for a blind user navigating by keyboard alone.

---

## Issues

### 1. Notebook Tabs Unreachable by Keyboard (High)

**Location:** `views/learner_view.py` — `ttk.Notebook`

The `ttk.Notebook` widget does not participate in Tkinter's normal Tab focus traversal. A blind user pressing Tab from the header buttons skips past the notebook tabs entirely. There is no way to switch between "My Assignments", "My Progress", "STEM Careers", and "Opportunities" by keyboard.

**Fix:** Bind `Ctrl+1/2/3/4` as keyboard shortcuts to jump directly to each tab. Announce the shortcut mapping in the navigation introduction. Optionally, also allow Left/Right arrow keys when the notebook has focus.

---

### 2. Checkbuttons Are Silent (High)

**Location:** `views/learner_view.py:405-410` (Settings dialog), `views/login_view.py:159-164`, `views/mentor_view.py` (Register Learner dialog)

`tk.Checkbutton` widgets receive focus but produce no TTS announcement. A blind user has no idea which checkbox they are on, or whether it is currently checked or unchecked.

**Fix:** Create an `AccessibleCheckbutton` widget in `views/widgets.py` that announces "Checkbox: [label], currently checked/unchecked" on `<FocusIn>`, and announces the new state ("checked"/"unchecked") on `<space>` toggle. Replace all `tk.Checkbutton` usages with `AccessibleCheckbutton`.

---

### 3. Comboboxes Are Silent (High)

**Location:** `views/mentor_view.py:117-121` (Assign dialog learner selector), `views/mentor_view.py:253-255` (Vision type), `views/educator_view.py:182-184` (Category), `views/login_view.py:109-112` (Role)

`ttk.Combobox` widgets get focus but produce no TTS announcement. A blind user lands on them silently and cannot tell what field they are on or what value is selected.

**Fix:** Create an `AccessibleCombobox` widget that announces "Dropdown: [label], currently [value]" on `<FocusIn>`, and announces the new selection on `<<ComboboxSelected>>`. Replace all `ttk.Combobox` usages with `AccessibleCombobox`.

---

### 4. No Focus Management After Actions (High)

**Locations:**
- `views/learner_view.py:174-182` — Course content dialog opens but focus stays on parent window
- `views/learner_view.py:148-161` — Assignment selected, courses list populated, but focus stays on assignment listbox
- All `tk.Toplevel` dialogs across all views — focus is not explicitly set to the first interactive widget

A blind user performs an action and then has to Tab around searching for what changed. They cannot tell that a dialog opened or that new content appeared.

**Fix:** After opening any `Toplevel` dialog, call `dlg.focus_set()` or set focus to the first interactive widget inside it. After populating the course listbox from an assignment selection, call `self.course_listbox.focus_set()`. After populating career/opportunity detail text, announce the content.

---

### 5. Messageboxes Not Spoken (Medium)

**Locations:**
- `views/learner_view.py:166` — "Select a course first" (no TTS)
- `views/learner_view.py:215-217` — "Course complete!" (no TTS)
- Various `messagebox.showwarning/showerror/showinfo` calls across all views

`messagebox` dialogs pop up visually but are not read aloud. Some call sites already have parallel `tts.speak()` calls, but many do not. A blind user does not know a dialog appeared.

**Fix:** Create a helper function (e.g. `speak_messagebox(tts, func, title, message)`) that calls both the messagebox function and `tts.speak(message)`. Replace all raw `messagebox` calls with this helper to ensure consistent TTS coverage.

---

### 6. Progress Tab Content Not Spoken (Medium)

**Location:** `views/learner_view.py:266-299`

The "My Progress" tab renders progress as labels and progress bars. When a blind user switches to this tab, they hear "Tab: My Progress" but nothing about the actual content. The labels exist but are not focusable or announced.

**Fix:** When the Progress tab is activated (via `_on_tab_change`), generate and speak a TTS summary: "You have N assignments. [Path name]: X out of Y courses completed." for each assignment. Alternatively, make the progress labels focusable with `announce=True`.

---

### 7. Career/Opportunity Detail Not Auto-Read (Low)

**Locations:**
- `views/learner_view.py:336-345` — Career selected, detail text updated but not spoken
- `views/learner_view.py:378-383` — Opportunity selected, detail label updated but not spoken

When a blind user selects an item from the career or opportunity list, the detail text appears visually but is not spoken. They must manually find and activate the "Read Aloud" button.

**Fix:** Auto-speak the detail text in `_on_career_select()` and `_on_opp_select()` after updating the display. The "Read Aloud" button can remain for re-reading.

---

## Summary

| Priority | Issue | Scope |
|----------|-------|-------|
| High | Notebook tabs unreachable by keyboard | `learner_view.py`, `main.py` |
| High | Checkbuttons silent | `widgets.py`, all views |
| High | Comboboxes silent | `widgets.py`, all views |
| High | No focus management after actions | All views with dialogs |
| Medium | Messageboxes not spoken | All views |
| Medium | Progress tab content not spoken | `learner_view.py` |
| Low | Career/Opportunity detail not auto-read | `learner_view.py` |
