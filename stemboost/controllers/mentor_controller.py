from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stemboost.services.interfaces import DataServiceProtocol


class MentorController:
    """Business logic for mentor actions: assign, monitor, post opportunities."""

    def __init__(self, data_service: DataServiceProtocol):
        self.ds = data_service

    def browse_all_paths(self):
        return self.ds.get_all_learning_paths()

    def get_courses_for_path(self, path_id):
        return self.ds.get_courses_by_path(path_id)

    def get_my_learners(self, mentor_id):
        return self.ds.get_learners_by_mentor(mentor_id)

    def get_all_learners(self):
        return self.ds.get_users_by_role("learner")

    def assign_path(self, mentor_id, learner_id, path_id,
                    excluded_course_ids=None):
        today = date.today().isoformat()
        return self.ds.create_assignment(
            mentor_id, learner_id, path_id,
            excluded_course_ids=excluded_course_ids,
            assigned_date=today)

    def register_learner(self, username, email, password, name, mentor_id,
                         vision_type="blind", accessibility_prefs=None,
                         stem_interests=None):
        return self.ds.create_user(
            username=username, email=email, password=password,
            name=name, role="learner",
            vision_type=vision_type,
            accessibility_prefs=accessibility_prefs,
            stem_interests=stem_interests,
            mentor_id=mentor_id)

    def get_learner_assignments(self, learner_id):
        return self.ds.get_assignments_by_learner(learner_id)

    def get_progress(self, assignment_id):
        """Return (completed, total) for an assignment."""
        return self.ds.get_progress_for_assignment(assignment_id)

    def get_path_by_id(self, path_id):
        return self.ds.get_learning_path_by_id(path_id)

    def post_opportunity(self, title, description, opp_type, mentor_id):
        today = date.today().isoformat()
        return self.ds.create_opportunity(title, description, opp_type,
                                          mentor_id, today)

    def get_all_opportunities(self):
        return self.ds.get_all_opportunities()

    def get_assignments_by_mentor(self, mentor_id):
        return self.ds.get_assignments_by_mentor(mentor_id)
