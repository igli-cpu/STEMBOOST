# STEMBOOST

STEMBOOST is a desktop application designed to teach STEM principles to blind and low-vision users. It provides an accessible learning environment where educators create content, mentors assign and monitor that content, and learners consume it with built-in accessibility support including text-to-speech, high-contrast themes, and large-text modes.

## Overview

The application models three user roles:

- **Educator** -- Creates and manages learning paths, courses, and content units. Each learning path belongs to a category (Job Exploration, Post-Secondary Education, Workplace Readiness, or Work-Based Learning) and contains ordered courses, which in turn contain text-based content.
- **Mentor** -- Browses learning paths created by educators, assigns them to learners (optionally excluding specific courses), registers new learners, monitors learner progress, and posts internship or academic opportunities.
- **Learner** -- Consumes assigned courses with text-to-speech playback, marks courses as complete, tracks their own progress, browses STEM career information, views posted opportunities, and configures accessibility preferences.

Progress is tracked as courses consumed out of total courses assigned (e.g. 3 out of 5 courses consumed).

## Technology Stack

- **Language:** Python 3.12+
- **GUI Framework:** Tkinter
- **Database:** SQLite (file-based, stored at `stemboost/data/stemboost.db`)
- **Text-to-Speech:** piper-tts (primary, neural TTS) with pyttsx3 fallback
- **Package Manager:** uv (or pip)

## Project Structure

```
STEMBOOST/
  stemboost/                  # Main package
    main.py                   # Application entry point, StemboostApp class
    __main__.py               # Allows running via `python -m stemboost`
    models/
      user.py                 # User, Educator, Mentor, Learner classes
      user_factory.py         # Factory pattern for constructing User subclasses
      course.py               # LearningPath, Course, Content classes
      progress.py             # Progress, Assignment classes
      opportunity.py          # Opportunity class
      assessment.py           # STEM field and skill level constants
      constants.py            # Domain constants (STEM fields, career path descriptions)
    controllers/
      auth_controller.py      # Login, registration, session management
      educator_controller.py  # CRUD for paths, courses, content
      mentor_controller.py    # Assignment, learner management, opportunities
      learner_controller.py   # Content consumption, progress tracking
    services/
      data_service.py         # Facade over all repositories; owns the DB connection
      tts_service.py          # TTS backend router: selects piper-tts or pyttsx3 at startup
      accessibility_service.py # Theme management (contrast, text size)
      interfaces.py           # Protocol definitions for DIP (controllers depend on these)
      observer.py             # Observer pattern for progress notifications
    repositories/
      user_repository.py      # User table CRUD and authentication
      learning_path_repository.py
      course_repository.py
      content_repository.py
      assignment_repository.py
      progress_repository.py
      opportunity_repository.py
    views/
      login_view.py           # Login and registration screens
      educator_view.py        # Educator dashboard (3-column path/course/content manager)
      mentor_view.py          # Mentor dashboard (tabbed: browse/assign, learners, opportunities)
      learner_view.py         # Learner dashboard (tabbed: assignments, progress, careers, opportunities)
      hotkeys.py              # Command pattern: HotkeyRegistry wires global key bindings
      view_context.py         # ViewContext dataclass passed to all views (decouples from StemboostApp)
      widgets.py              # Accessible widget subclasses (buttons, labels, entries, listboxes)
    data/
      seed_data.py            # Demo data loader (sample users, paths, courses, assignments)
      stemboost.db            # SQLite database file (auto-created on first run)
  tests/
    conftest.py               # Shared fixtures: in-memory DataService, SpyTTS test double, seeded scenario
    test_learner_requirements.py
    test_mentor_educator_requirements.py
    test_progress_tts.py
    test_system_requirements.py
  docs/
    ai_uc1.drawio             # Use-case diagram (source)
    ai_uc1.png                # Use-case diagram (rendered)
    ai_uc2.png                # Use-case diagram 2 (rendered)
    general_uc.drawio         # Use-case diagram (source)
  pyproject.toml
  requirements.txt            # Legacy pip file (prefer pyproject.toml)
```

## Design Patterns Used

- **MVC** -- Models define domain objects, controllers contain business logic, views handle the Tkinter GUI, and services/repositories manage persistence.
- **Factory** -- `UserFactory` constructs the correct `User` subclass (`Educator`, `Mentor`, or `Learner`) from a role string or database row.
- **Singleton** -- Each TTS backend class uses a `get_instance()` class method so only one engine instance exists per process.
- **Observer** -- `ProgressSubject`/`ProgressObserver` notifies the learner view when course completion status changes.
- **Facade** -- `DataService` provides a single entry point to the data layer, delegating to individual repository classes. `TTSFacade` (module-level alias) hides which backend is active.
- **Repository** -- Each database table has a dedicated repository class responsible for its SQL operations.
- **Command** -- `HotkeyRegistry` in `hotkeys.py` encapsulates each key binding as a `Hotkey` dataclass (key sequences + description + action + guard), decoupling key registration from `StemboostApp`.
- **Protocol / Dependency Inversion** -- `services/interfaces.py` defines `DataServiceProtocol` so controllers depend on an abstract interface rather than the concrete `DataService` implementation.

## Prerequisites

- Python 3.12 or later
- Tkinter (included with standard Python installations on most platforms)
- For piper-tts (default): internet access on first run to download the voice model (~50 MB to `models/piper-tts/`), or pre-downloaded model files already present in that directory
- For pyttsx3 fallback (optional): see *Optional pytts packages* below

## Installation

### Using uv (recommended)

```bash
uv sync
```

### Using pip

```bash
pip install piper-tts numpy sounddevice
```

### Optional pytts packages

Install `pyttsx3` as a fallback TTS engine (used automatically when piper-tts is unavailable):

```bash
# uv
uv sync --extra pytts

# pip
pip install pyttsx3
```

### Test dependencies

```bash
# uv
uv sync --extra test

# pip
pip install pytest
```

## Text-to-Speech Backend Selection

At startup, the application automatically selects the best available TTS engine:

1. **piper-tts** (neural, high-fidelity) -- used if `piper-tts`, `numpy`, and `sounddevice` are importable **and** either a pre-downloaded model exists in `models/piper-tts/` or the machine has internet access. The first run downloads the default voice (`hfc_female`, ~50 MB) from HuggingFace.
2. **pyttsx3** (system TTS, lower fidelity) -- used as a fallback when piper-tts is unavailable. On Windows, SAPI5 is used; on macOS/Linux, the platform speech engine is used via the pyttsx3 driver.

If neither engine can be loaded, the application raises an `ImportError` with installation instructions.

## Running the Application

From the project root:

```bash
python -m stemboost.main
```

Or equivalently:

```bash
python -m stemboost
```

If installed via uv, from the project root:

```bash
uv run python -m stemboost
```

The application opens a 1000×700 Tkinter window. On the first run, the database is automatically created and populated with demo data. If piper-tts is the active backend, the voice model is downloaded at this point (requires an internet connection).

## Running Tests

```bash
# uv
uv run pytest

# pip / standard
pytest
```

Tests use an in-memory SQLite database and a `SpyTTS` test double — no audio hardware or network access is required.

## Demo Accounts

The seed data creates the following accounts (all with password `pass123`):

| Username       | Role     | Notes                           |
|----------------|----------|---------------------------------|
| dr.smith       | educator | Computer Science, Data Science  |
| prof.chen      | educator | Mathematics, Physics            |
| ms.jones       | mentor   | Mentors Alex and Sam            |
| mr.williams    | mentor   | Mentors Jordan                  |
| alex           | learner  | Blind, high-contrast            |
| sam            | learner  | Low vision, large text          |
| jordan         | learner  | Blind, high-contrast + large text |

## Keyboard Navigation

All interactive widgets announce themselves via TTS when focused.

| Key | Action |
|-----|--------|
| **Tab** / **Shift+Tab** | Move between interactive elements |
| **F1** | Announce current position and available navigation options |
| **Space** | Activate the focused button |
| **Enter** | Submit the login form (when password field is focused) |
| **Escape** | Return to the login screen from any view |

## Resetting Data

Click the **Reset Demo Data** button on the login screen to drop all tables, recreate them, and re-seed the demo data.
