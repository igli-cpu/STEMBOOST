from abc import ABC, abstractmethod


class ProgressObserver(ABC):
    """Observer interface: receives notifications when learner progress changes."""

    @abstractmethod
    def on_progress_update(self, learner_id, assignment_id, completed, total):
        """Called when a learner completes a course.

        Args:
            learner_id: The learner whose progress changed.
            assignment_id: The assignment that was updated.
            completed: Number of courses completed so far.
            total: Total number of courses in the assignment.
        """


class ProgressSubject:
    """Observable subject that tracks progress and notifies observers."""

    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass  # Already detached or never attached

    def notify(self, learner_id, assignment_id, completed, total):
        for observer in self._observers:
            observer.on_progress_update(learner_id, assignment_id,
                                        completed, total)
