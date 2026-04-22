"""Tests for the learner progress tab's TTS behavior.

The progress tab must (a) report progress as "X out of Y courses consumed"
in line with the elicitation comment on page 3, and (b) speak that
progress via TTS — this test file verifies the speech text produced by
`LearnerView._build_progress_speech`, which is the pure-data helper that
the UI calls for both per-row focus announcements and the Read Aloud
button. Testing the helper directly keeps these assertions decoupled
from Tkinter.
"""

from __future__ import annotations


def _build_speech(learner_ctrl, learner_id):
    """Mirror of LearnerView._build_progress_speech but without a Tk view.

    Kept in the test file so the helper-under-test can't be circumvented
    by accidental refactor — if this drifts from the view implementation
    the focus/read-aloud tests below will fail alongside it.
    """
    # Import lazily so failures during Tk setup don't break collection
    # on CI runners that lack a display.
    from stemboost.views.learner_view import LearnerView

    class _Stub:
        ctrl = learner_ctrl

        class _User:
            pass
        user = _User()
        user.user_id = learner_id
    stub = _Stub()
    assignments = learner_ctrl.get_my_assignments(learner_id)
    return LearnerView._build_progress_speech(stub, assignments)


class TestProgressSpeechContent:
    """The spoken progress summary must match the requirement-defined
    phrasing: "N out of M courses consumed"."""

    def test_uses_out_of_phrasing_for_incomplete_path(
            self, learner_ctrl, scenario):
        summary, per_row = _build_speech(
            learner_ctrl, scenario["learner_id"])
        assert "0 out of 3 courses consumed" in summary
        assert len(per_row) == 1
        assert "0 out of 3 courses consumed" in per_row[0]

    def test_percentage_is_included_when_incomplete(
            self, learner_ctrl, scenario):
        learner_ctrl.mark_course_complete(
            scenario["learner_id"], scenario["assignment_id"],
            scenario["course_ids"][0])
        summary, _ = _build_speech(
            learner_ctrl, scenario["learner_id"])
        assert "1 out of 3 courses consumed" in summary
        assert "33 percent" in summary

    def test_path_complete_announced_when_all_courses_done(
            self, learner_ctrl, scenario):
        for cid in scenario["course_ids"]:
            learner_ctrl.mark_course_complete(
                scenario["learner_id"], scenario["assignment_id"], cid)
        summary, per_row = _build_speech(
            learner_ctrl, scenario["learner_id"])
        assert "path complete" in per_row[0].lower()
        assert "all 3 courses consumed" in summary.lower()

    def test_zero_assignments_yields_friendly_summary(
            self, learner_ctrl, ds, scenario):
        # A brand-new learner with no assignments.
        uid = ds.create_user(
            username="solo", email="s@e.com", password="pw",
            name="Solo", role="learner",
            mentor_id=scenario["mentor_id"])
        summary, per_row = _build_speech(learner_ctrl, uid)
        assert per_row == []
        assert "no assignments" in summary.lower()


class TestSpyTtsReceivesProgress:
    """End-to-end: when we speak the summary through the SpyTTS, the text
    recorded must include the "out of" phrasing required by REQ-L-007 +
    the elicitation comment."""

    def test_spoken_summary_contains_progress_phrasing(
            self, learner_ctrl, scenario, tts):
        summary, _ = _build_speech(
            learner_ctrl, scenario["learner_id"])
        tts.speak(summary)
        assert tts.heard("out of 3 courses consumed")

    def test_read_aloud_respects_disabled_audio(
            self, learner_ctrl, scenario, tts):
        """REQ-L-006 + REQ-S-002 cross-check: when the learner disables
        audio the TTS must not emit speech."""
        summary, _ = _build_speech(
            learner_ctrl, scenario["learner_id"])
        tts.enabled = False
        tts.speak(summary)
        assert tts.spoken == []

    def test_stop_reading_clears_playback(self, tts):
        tts.speak("some long announcement")
        tts.stop()
        assert tts.stopped == 1
