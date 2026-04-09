from stemboost.models.progress import Assignment


class AssignmentRepository:
    """Handles all assignment persistence operations."""

    def __init__(self, conn):
        self._conn = conn

    def create_assignment(self, mentor_id, learner_id, path_id,
                          excluded_course_ids=None, assigned_date=""):
        excluded_str = ",".join(str(x) for x in (excluded_course_ids or []))
        c = self._conn.cursor()
        c.execute(
            """INSERT INTO assignments (mentor_id, learner_id, path_id,
               excluded_course_ids, assigned_date)
               VALUES (?, ?, ?, ?, ?)""",
            (mentor_id, learner_id, path_id, excluded_str, assigned_date))
        self._conn.commit()
        return c.lastrowid

    def get_assignment_for_learner_path(self, learner_id, path_id):
        """Return existing assignment for a learner+path combo, or None."""
        c = self._conn.cursor()
        c.execute(
            "SELECT * FROM assignments WHERE learner_id = ? AND path_id = ?",
            (learner_id, path_id))
        row = c.fetchone()
        return self._row_to_assignment(row) if row else None

    def update_excluded_courses(self, assignment_id, excluded_course_ids):
        """Update the excluded_course_ids for an existing assignment."""
        excluded_str = ",".join(str(x) for x in (excluded_course_ids or []))
        c = self._conn.cursor()
        c.execute(
            "UPDATE assignments SET excluded_course_ids = ? "
            "WHERE assignment_id = ?",
            (excluded_str, assignment_id))
        self._conn.commit()

    def get_assignments_by_learner(self, learner_id):
        c = self._conn.cursor()
        c.execute("SELECT * FROM assignments WHERE learner_id = ?", (learner_id,))
        return [self._row_to_assignment(r) for r in c.fetchall()]

    def get_assignments_by_mentor(self, mentor_id):
        c = self._conn.cursor()
        c.execute("SELECT * FROM assignments WHERE mentor_id = ?", (mentor_id,))
        return [self._row_to_assignment(r) for r in c.fetchall()]

    def _row_to_assignment(self, row):
        return Assignment(
            assignment_id=row[0], mentor_id=row[1], learner_id=row[2],
            path_id=row[3],
            excluded_course_ids=Assignment.parse_excluded_ids(row[4]),
            assigned_date=row[5])
