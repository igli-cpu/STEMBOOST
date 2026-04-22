"""Tests for learner-facing requirements (REQ-L-*).

Each test cites the requirement it verifies in its docstring so the suite
doubles as a traceability matrix between the code and the requirement
elicitation document.
"""

from __future__ import annotations


class TestAccessibilityRegistration:
    """REQ-L-001, REQ-L-002, REQ-L-006: learners annotate accessibility needs
    (including vision type and audio/contrast/large-text prefs) at
    registration and can update them later."""

    def test_L001_learner_annotates_accessibility_needs_on_register(
            self, ds):
        """REQ-L-001: accessibility needs captured during registration."""
        uid = ds.create_user(
            username="alex", email="a@example.com", password="pw",
            name="Alex", role="learner",
            vision_type="blind",
            accessibility_prefs={"audio": True, "high_contrast": True,
                                 "large_text": False},
            stem_interests=[])
        user = ds.get_user_by_id(uid)
        assert user.vision_type == "blind"
        assert user.accessibility_prefs["high_contrast"] is True
        assert user.accessibility_prefs["audio"] is True

    def test_L002_register_as_blind_or_low_vision(self, ds):
        """REQ-L-002: vision_type supports both blind and low_vision."""
        blind_id = ds.create_user(
            username="b", email="b@e.com", password="pw", name="B",
            role="learner", vision_type="blind")
        lv_id = ds.create_user(
            username="lv", email="lv@e.com", password="pw", name="LV",
            role="learner", vision_type="low_vision")
        assert ds.get_user_by_id(blind_id).vision_type == "blind"
        assert ds.get_user_by_id(lv_id).vision_type == "low_vision"

    def test_L006_learner_can_toggle_accessibility_features(
            self, learner_ctrl, scenario, ds):
        """REQ-L-006: learner can change audio, high_contrast, large_text."""
        new_prefs = {"audio": False, "high_contrast": True,
                     "large_text": True}
        learner_ctrl.update_accessibility_prefs(
            scenario["learner_id"], new_prefs)
        saved = ds.get_user_by_id(scenario["learner_id"])
        assert saved.accessibility_prefs == new_prefs


class TestStemInterests:
    """REQ-L-003: learners identify STEM paths they are interested in."""

    def test_L003_learner_can_set_stem_interests(
            self, learner_ctrl, scenario, ds):
        interests = ["Computer Science", "Mathematics"]
        learner_ctrl.update_stem_interests(
            scenario["learner_id"], interests)
        saved = ds.get_user_by_id(scenario["learner_id"])
        assert set(saved.stem_interests) == set(interests)


class TestViewAssignedContent:
    """REQ-L-009: learner views content assigned by their mentor."""

    def test_L009_learner_sees_only_their_assignments(
            self, learner_ctrl, mentor_ctrl, ds, scenario):
        # A second learner should not see the first learner's assignment.
        other_learner = ds.create_user(
            username="other", email="o@e.com", password="pw",
            name="Other", role="learner",
            mentor_id=scenario["mentor_id"])

        mine = learner_ctrl.get_my_assignments(scenario["learner_id"])
        theirs = learner_ctrl.get_my_assignments(other_learner)

        assert len(mine) == 1
        assert mine[0].assignment_id == scenario["assignment_id"]
        assert theirs == []

    def test_L009_courses_for_assignment_match_path(
            self, learner_ctrl, scenario):
        assignments = learner_ctrl.get_my_assignments(scenario["learner_id"])
        courses = learner_ctrl.get_courses_for_assignment(assignments[0])
        assert [c.course_id for c in courses] == scenario["course_ids"]

    def test_L009_mentor_opt_out_hides_courses_from_learner(
            self, mentor_ctrl, learner_ctrl, ds, scenario):
        """REQ-M-003 cross-check: mentor-excluded courses are hidden
        from the learner's assignment view."""
        new_learner = ds.create_user(
            username="opt", email="o2@e.com", password="pw",
            name="Opt", role="learner",
            mentor_id=scenario["mentor_id"])
        excluded = [scenario["course_ids"][0]]
        mentor_ctrl.assign_path(
            scenario["mentor_id"], new_learner, scenario["path_id"],
            excluded_course_ids=excluded)

        assignments = learner_ctrl.get_my_assignments(new_learner)
        courses = learner_ctrl.get_courses_for_assignment(assignments[0])
        visible_ids = {c.course_id for c in courses}
        assert scenario["course_ids"][0] not in visible_ids
        assert scenario["course_ids"][1] in visible_ids


class TestLearnerProgressTracking:
    """REQ-L-007: learner gets progress in their selected learning path.

    The elicitation comment specifies progress is reported as
    "X out of Y courses consumed" — NOT a narrative progress report.
    """

    def test_L007_initial_progress_is_zero_of_total(
            self, learner_ctrl, scenario):
        completed, total = learner_ctrl.get_progress(
            scenario["assignment_id"])
        assert completed == 0
        assert total == len(scenario["course_ids"])

    def test_L007_progress_increments_after_completion(
            self, learner_ctrl, scenario):
        learner_ctrl.mark_course_complete(
            scenario["learner_id"], scenario["assignment_id"],
            scenario["course_ids"][0])
        completed, total = learner_ctrl.get_progress(
            scenario["assignment_id"])
        assert completed == 1
        assert total == 3

    def test_L007_full_completion_reaches_total_of_total(
            self, learner_ctrl, scenario):
        for cid in scenario["course_ids"]:
            learner_ctrl.mark_course_complete(
                scenario["learner_id"], scenario["assignment_id"], cid)
        completed, total = learner_ctrl.get_progress(
            scenario["assignment_id"])
        assert completed == total == 3

    def test_L007_marking_same_course_twice_is_idempotent(
            self, learner_ctrl, scenario):
        """Mark-complete is idempotent — the count cannot exceed total."""
        cid = scenario["course_ids"][0]
        learner_ctrl.mark_course_complete(
            scenario["learner_id"], scenario["assignment_id"], cid)
        learner_ctrl.mark_course_complete(
            scenario["learner_id"], scenario["assignment_id"], cid)
        completed, total = learner_ctrl.get_progress(
            scenario["assignment_id"])
        assert completed == 1
        assert total == 3
