"""Shared fixtures for requirements-based tests.

These fixtures build a clean in-memory SQLite-backed DataService and
populate it with a minimal scenario: one educator-authored learning path
with three courses, a mentor, and a learner assigned to the path.

A SpyTTS fake stands in for the real TTS engine so we can assert that
specific strings were spoken without touching audio hardware.
"""

from __future__ import annotations

import pytest

from stemboost.controllers.learner_controller import LearnerController
from stemboost.controllers.mentor_controller import MentorController
from stemboost.services.data_service import DataService


class SpyTTS:
    """Test double for the TTS facade — records spoken text."""

    def __init__(self):
        self.enabled = True
        self.spoken: list[str] = []
        self.stopped = 0

    def speak(self, text):
        if not self.enabled:
            return
        self.spoken.append(text)

    def stop(self):
        self.stopped += 1

    @property
    def is_speaking(self):
        return False

    def attach_to_root(self, root):
        pass

    def set_volume(self, volume):
        pass

    def set_voice(self, voice):
        pass

    def last_said(self) -> str:
        return self.spoken[-1] if self.spoken else ""

    def heard(self, substring: str) -> bool:
        return any(substring in s for s in self.spoken)


@pytest.fixture
def ds():
    """Fresh in-memory DataService for each test."""
    service = DataService(db_path=":memory:")
    service.connect()
    yield service
    service.close()


@pytest.fixture
def tts():
    return SpyTTS()


@pytest.fixture
def scenario(ds):
    """Seeded scenario with one mentor, one educator, one learner, one path
    containing three courses (each with one content unit), and an
    assignment linking the learner to the path.

    Returns a namespace-style dict of ids so tests can reference them.
    """
    educator_id = ds.create_user(
        username="edu1", email="edu1@example.com", password="pw",
        name="Dr. Edu", role="educator",
        expertise_areas=["Computer Science"])
    mentor_id = ds.create_user(
        username="mentor1", email="m@example.com", password="pw",
        name="Mentor One", role="mentor")
    learner_id = ds.create_user(
        username="learner1", email="l@example.com", password="pw",
        name="Learner One", role="learner",
        vision_type="blind",
        accessibility_prefs={"audio": True, "high_contrast": False,
                             "large_text": False},
        stem_interests=["Computer Science"],
        mentor_id=mentor_id)

    path_id = ds.create_learning_path(
        title="Intro to CS",
        description="Foundations of computer science",
        category="Post-Secondary Education",
        created_by=educator_id)

    course_ids = []
    for i in range(3):
        cid = ds.create_course(
            title=f"Course {i + 1}",
            description=f"Description for course {i + 1}",
            path_id=path_id, created_by=educator_id, order_index=i)
        ds.create_content(
            title=f"Unit {i + 1}", text_body=f"Body of unit {i + 1}.",
            course_id=cid, created_by=educator_id, order_index=0)
        course_ids.append(cid)

    assignment_id = ds.create_assignment(
        mentor_id=mentor_id, learner_id=learner_id, path_id=path_id,
        excluded_course_ids=None, assigned_date="2026-01-01")

    return {
        "educator_id": educator_id,
        "mentor_id": mentor_id,
        "learner_id": learner_id,
        "path_id": path_id,
        "course_ids": course_ids,
        "assignment_id": assignment_id,
    }


@pytest.fixture
def learner_ctrl(ds):
    return LearnerController(ds)


@pytest.fixture
def mentor_ctrl(ds):
    return MentorController(ds)
