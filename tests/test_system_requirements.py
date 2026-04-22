"""Tests for system-level requirements (REQ-S-*) and the
observer/notification mechanism that backs real-time progress updates."""

from __future__ import annotations

import time

from stemboost.services.observer import ProgressObserver


class _RecordingObserver(ProgressObserver):
    def __init__(self):
        self.events = []

    def on_progress_update(self, learner_id, assignment_id, completed, total):
        self.events.append((learner_id, assignment_id, completed, total))


class TestTtsLatency:
    """REQ-S-001: the TTS shall speak within 1s of being asked to."""

    def test_S001_spy_tts_speak_returns_within_one_second(self, tts):
        start = time.monotonic()
        tts.speak("hello")
        elapsed = time.monotonic() - start
        assert elapsed < 1.0
        assert tts.last_said() == "hello"

    def test_S001_speak_while_disabled_is_silent(self, tts):
        tts.enabled = False
        tts.speak("should not speak")
        assert tts.spoken == []


class TestProgressUpdatesOnCompletion:
    """REQ-S-008: the system shall update the learner progress as a
    Content/Unit is completed.

    Covered at two layers: the persisted counter, and the observer
    broadcast that drives real-time UI refresh.
    """

    def test_S008_progress_persists_after_completion(
            self, learner_ctrl, scenario):
        cid = scenario["course_ids"][0]
        learner_ctrl.mark_course_complete(
            scenario["learner_id"], scenario["assignment_id"], cid)
        assert learner_ctrl.is_course_completed(
            scenario["learner_id"], scenario["assignment_id"], cid) is True

    def test_S008_observer_notified_on_completion(
            self, learner_ctrl, scenario):
        observer = _RecordingObserver()
        learner_ctrl.progress_subject.attach(observer)

        learner_ctrl.mark_course_complete(
            scenario["learner_id"], scenario["assignment_id"],
            scenario["course_ids"][0])

        assert len(observer.events) == 1
        learner_id, assignment_id, completed, total = observer.events[0]
        assert learner_id == scenario["learner_id"]
        assert assignment_id == scenario["assignment_id"]
        assert completed == 1
        assert total == 3

    def test_S008_detached_observer_stops_receiving(
            self, learner_ctrl, scenario):
        observer = _RecordingObserver()
        learner_ctrl.progress_subject.attach(observer)
        learner_ctrl.progress_subject.detach(observer)
        learner_ctrl.mark_course_complete(
            scenario["learner_id"], scenario["assignment_id"],
            scenario["course_ids"][0])
        assert observer.events == []


class TestAuthAndSecurity:
    """REQ-S-009: accounts are secured through password (and email)."""

    def test_S009_password_is_hashed_not_stored_plain(self, ds):
        ds.create_user(
            username="sec", email="s@e.com", password="plaintext-123",
            name="Sec", role="learner")
        # Round-trip: authenticate must work with the real password and
        # fail with the wrong password. The stored hash is not equal to
        # the plaintext.
        user_ok = ds.authenticate("sec", "plaintext-123")
        user_bad = ds.authenticate("sec", "wrong")
        assert user_ok is not None
        assert user_bad is None
        assert user_ok.password_hash != "plaintext-123"
        assert len(user_ok.password_hash) == 64  # sha256 hex digest


class TestAccessibilityTypesAvailable:
    """REQ-S-007: the system provides Audio, High Contrast, Large Text."""

    def test_S007_all_three_accessibility_prefs_round_trip(
            self, ds, learner_ctrl):
        uid = ds.create_user(
            username="axe", email="a@e.com", password="pw", name="Axe",
            role="learner")
        prefs = {"audio": True, "high_contrast": True, "large_text": True}
        learner_ctrl.update_accessibility_prefs(uid, prefs)
        saved = ds.get_user_by_id(uid)
        for key in ("audio", "high_contrast", "large_text"):
            assert saved.accessibility_prefs[key] is True
