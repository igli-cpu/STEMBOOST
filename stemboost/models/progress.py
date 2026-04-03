class Progress:
    """Tracks whether a learner has completed a specific course in an assignment."""

    def __init__(self, progress_id=None, learner_id=None, assignment_id=None,
                 course_id=None, completed=False, completed_date=None):
        self.progress_id = progress_id
        self.learner_id = learner_id
        self.assignment_id = assignment_id
        self.course_id = course_id
        self.completed = completed
        self.completed_date = completed_date

    def __repr__(self):
        status = "done" if self.completed else "pending"
        return f"<Progress learner={self.learner_id} course={self.course_id} {status}>"


class Assignment:
    """Links a mentor's assignment of a learning path to a learner."""

    def __init__(self, assignment_id=None, mentor_id=None, learner_id=None,
                 path_id=None, excluded_course_ids=None, assigned_date=None):
        self.assignment_id = assignment_id
        self.mentor_id = mentor_id
        self.learner_id = learner_id
        self.path_id = path_id
        self.excluded_course_ids = excluded_course_ids or []
        self.assigned_date = assigned_date

    def get_excluded_ids_str(self):
        return ",".join(str(cid) for cid in self.excluded_course_ids)

    @staticmethod
    def parse_excluded_ids(csv_str):
        if not csv_str:
            return []
        return [int(x) for x in csv_str.split(",") if x.strip()]

    def __repr__(self):
        return (f"<Assignment id={self.assignment_id} "
                f"learner={self.learner_id} path={self.path_id}>")
