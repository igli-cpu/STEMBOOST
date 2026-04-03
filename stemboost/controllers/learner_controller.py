from datetime import date

from stemboost.services.observer import ProgressSubject


class LearnerController:
    """Business logic for learner actions: consume content, track progress."""

    def __init__(self, data_service):
        self.ds = data_service
        self.progress_subject = ProgressSubject()

    def get_my_assignments(self, learner_id):
        return self.ds.get_assignments_by_learner(learner_id)

    def get_path_info(self, path_id):
        paths = self.ds.get_all_learning_paths()
        for p in paths:
            if p.path_id == path_id:
                return p
        return None

    def get_courses_for_assignment(self, assignment):
        """Return courses for an assignment, excluding opted-out ones."""
        all_courses = self.ds.get_courses_by_path(assignment.path_id)
        excluded = set(assignment.excluded_course_ids)
        return [c for c in all_courses if c.course_id not in excluded]

    def get_contents(self, course_id):
        return self.ds.get_contents_by_course(course_id)

    def is_course_completed(self, learner_id, assignment_id, course_id):
        return self.ds.is_course_completed(learner_id, assignment_id, course_id)

    def mark_course_complete(self, learner_id, assignment_id, course_id):
        today = date.today().isoformat()
        self.ds.mark_course_completed(learner_id, assignment_id, course_id,
                                      today)
        completed, total = self.ds.get_progress_for_assignment(assignment_id)
        self.progress_subject.notify(learner_id, assignment_id,
                                     completed, total)
        return completed, total

    def get_progress(self, assignment_id):
        return self.ds.get_progress_for_assignment(assignment_id)

    def get_opportunities(self):
        return self.ds.get_all_opportunities()

    def update_accessibility_prefs(self, user_id, prefs):
        self.ds.update_user_accessibility(user_id, prefs)

    def update_stem_interests(self, user_id, interests):
        self.ds.update_user_stem_interests(user_id, interests)

    def get_user(self, user_id):
        return self.ds.get_user_by_id(user_id)
