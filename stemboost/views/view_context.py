"""ViewContext decouples views from the concrete StemboostApp class.

Views receive this context instead of the full app object, so they only
depend on the interface they actually use — not on StemboostApp internals.
"""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ViewContext:
    """Everything a view needs from the application layer."""

    tts: Any
    accessibility: Any
    auth: Any
    educator_ctrl: Any
    mentor_ctrl: Any
    learner_ctrl: Any
    root: Any
    show_login: Callable
    show_dashboard: Callable
    reset_demo_data: Callable
