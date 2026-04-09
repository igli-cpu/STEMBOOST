# STEMBOOST

STEMBOOST is a desktop application designed to teach STEM principles to blind and low-vision users. It provides an accessible learning environment where educators create content, mentors assign and monitor that content, and learners consume it with built-in accessibility support including text-to-speech, high-contrast themes, and large-text modes.

## Overview

The application models three user roles:

- **Educator** -- Creates and manages learning paths, courses, and content units. Each learning path belongs to a category (Job Exploration, Post-Secondary Education, Workplace Readiness, or Work-Based Learning) and contains ordered courses, which in turn contain text-based content.
- **Mentor** -- Browses learning paths created by educators, assigns them to learners (optionally excluding specific courses), registers new learners, monitors learner progress, and posts internship or academic opportunities.
- **Learner** -- Consumes assigned courses with text-to-speech playback, marks courses as complete, tracks their own progress, browses STEM career information, views posted opportunities, and configures accessibility preferences.

Progress is tracked as courses consumed out of total courses assigned (e.g. 3 out of 5 courses consumed).

## Technology Stack

- **Language:** Python 3.10+
- **GUI Framework:** Tkinter
- **Database:** SQLite (file-based, stored at `stemboost/data/stemboost.db`)
- **Text-to-Speech:** pyttsx3
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
      tts_service.py          # Singleton text-to-speech facade wrapping pyttsx3
      accessibility_service.py # Theme management (contrast, text size)
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
      widgets.py              # Accessible widget subclasses (buttons, labels, entries, listboxes)
    data/
      seed_data.py            # Demo data loader (sample users, paths, courses, assignments)
      stemboost.db            # SQLite database file (auto-created on first run)
  requirements.txt
  Feedback.md                 # OOP design review and SOLID analysis
```

## Design Patterns Used

- **MVC** -- Models define domain objects, controllers contain business logic, views handle the Tkinter GUI, and services/repositories manage persistence.
- **Factory** -- `UserFactory` constructs the correct `User` subclass (`Educator`, `Mentor`, or `Learner`) from a role string or database row.
- **Singleton** -- `TTSFacade` ensures a single pyttsx3 engine instance is shared across the application.
- **Observer** -- `ProgressSubject`/`ProgressObserver` notifies the learner view when course completion status changes.
- **Facade** -- `DataService` provides a single entry point to the data layer, delegating to individual repository classes.
- **Repository** -- Each database table has a dedicated repository class responsible for its SQL operations.

## Prerequisites

- Python 3.10 or later
- pyttsx3 (and its system dependencies for TTS playback)
- Tkinter (included with standard Python installations on most platforms)

## Installation

Using pip:

```bash
pip install -r requirements.txt
```

Using uv (from the `stemboost/` subdirectory):

```bash
cd stemboost
uv sync
```

## Running the Application

From the project root:

```bash
python -m stemboost.main
```

Or equivalently:

```bash
python -m stemboost
```

If installed via uv, from the `stemboost/` subdirectory:

```bash
uv run python -m stemboost
```

The application opens a 1000x700 Tkinter window. On the first run, the database is automatically created and populated with demo data.

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

- **Tab** / **Shift+Tab** -- Move between interactive elements. All accessible widgets announce themselves via TTS on focus.
- **Escape** -- Return to the login screen from any view.
- **Enter** -- Submit the login form when the password field is focused.

## Resetting Data

Click the "Reset Demo Data" button on the login screen to drop all tables, recreate them, and re-seed the demo data.
