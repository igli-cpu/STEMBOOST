"""Tests for mentor (REQ-M-*) and educator (REQ-E-*) requirements."""

from __future__ import annotations


class TestEducatorAuthoring:
    """REQ-E-001 through REQ-E-008."""

    def test_E001_educator_account_creation(self, ds):
        uid = ds.create_user(
            username="edu", email="e@e.com", password="pw",
            name="Edu", role="educator",
            expertise_areas=["Mathematics"])
        user = ds.get_user_by_id(uid)
        assert user.role == "educator"
        assert "Mathematics" in user.expertise_areas

    def test_E003_E004_E005_path_course_content_hierarchy(self, ds):
        educator_id = ds.create_user(
            username="e", email="e@e.com", password="pw", name="E",
            role="educator")
        path_id = ds.create_learning_path(
            "Data", "desc", "Job Exploration", educator_id)
        course_id = ds.create_course(
            "Intro", "desc", path_id, educator_id, 0)
        content_id = ds.create_content(
            "Unit 1", "body", course_id, educator_id, 0)

        assert ds.get_learning_path_by_id(path_id).title == "Data"
        courses = ds.get_courses_by_path(path_id)
        assert [c.course_id for c in courses] == [course_id]
        contents = ds.get_contents_by_course(course_id)
        assert [x.content_id for x in contents] == [content_id]

    def test_E007_educator_expertise_can_be_updated(self, ds):
        uid = ds.create_user(
            username="e", email="e@e.com", password="pw", name="E",
            role="educator", expertise_areas=["Physics"])
        ds.update_educator_expertise(uid, ["Physics", "Mathematics"])
        saved = ds.get_user_by_id(uid)
        assert set(saved.expertise_areas) == {"Physics", "Mathematics"}

    def test_E008_educator_can_update_existing_content(self, ds):
        educator_id = ds.create_user(
            username="e", email="e@e.com", password="pw", name="E",
            role="educator")
        path_id = ds.create_learning_path(
            "p", "", "", educator_id)
        course_id = ds.create_course("c", "", path_id, educator_id, 0)
        content_id = ds.create_content(
            "old title", "old body", course_id, educator_id, 0)

        ds.update_content(content_id, "new title", "new body")
        refreshed = ds.get_contents_by_course(course_id)[0]
        assert refreshed.title == "new title"
        assert refreshed.text_body == "new body"


class TestMentorAssignment:
    """REQ-M-002 through REQ-M-006."""

    def test_M002_mentor_assigns_path_to_learner(
            self, mentor_ctrl, scenario, ds):
        # A second learner who isn't yet assigned.
        new_learner = ds.create_user(
            username="new", email="n@e.com", password="pw",
            name="New", role="learner",
            mentor_id=scenario["mentor_id"])
        aid = mentor_ctrl.assign_path(
            scenario["mentor_id"], new_learner, scenario["path_id"])
        assignments = ds.get_assignments_by_learner(new_learner)
        assert [a.assignment_id for a in assignments] == [aid]

    def test_M003_mentor_can_opt_out_courses(
            self, mentor_ctrl, scenario, ds):
        new_learner = ds.create_user(
            username="optout", email="o@e.com", password="pw",
            name="OO", role="learner",
            mentor_id=scenario["mentor_id"])
        excluded = [scenario["course_ids"][0]]
        aid = mentor_ctrl.assign_path(
            scenario["mentor_id"], new_learner, scenario["path_id"],
            excluded_course_ids=excluded)
        # Total progress rows should be 2 (3 courses minus 1 excluded).
        completed, total = mentor_ctrl.get_progress(aid)
        assert completed == 0
        assert total == 2

    def test_M004_mentor_signs_up_learner(self, mentor_ctrl, scenario, ds):
        new_id = mentor_ctrl.register_learner(
            username="signed_up", email="su@e.com", password="pw",
            name="Signed Up", mentor_id=scenario["mentor_id"],
            vision_type="low_vision",
            accessibility_prefs={"audio": True, "high_contrast": False,
                                 "large_text": True},
            stem_interests=["Mathematics"])
        learner = ds.get_user_by_id(new_id)
        assert learner.role == "learner"
        assert learner.mentor_id == scenario["mentor_id"]
        assert learner.vision_type == "low_vision"

    def test_M005_mentor_posts_opportunity(self, mentor_ctrl, scenario):
        mentor_ctrl.post_opportunity(
            "NASA Internship", "Summer program", "internship",
            scenario["mentor_id"])
        opps = mentor_ctrl.get_all_opportunities()
        assert any(o.title == "NASA Internship" for o in opps)

    def test_M006_mentor_sees_learner_progress(
            self, learner_ctrl, mentor_ctrl, scenario):
        learner_ctrl.mark_course_complete(
            scenario["learner_id"], scenario["assignment_id"],
            scenario["course_ids"][0])
        completed, total = mentor_ctrl.get_progress(scenario["assignment_id"])
        assert completed == 1
        assert total == 3
