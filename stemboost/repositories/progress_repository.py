from stemboost.models.progress import Progress


class ProgressRepository:
    """Handles all progress tracking persistence operations."""

    def __init__(self, conn):
        self._conn = conn

    def create_progress_rows(self, learner_id, assignment_id, courses,
                             excluded_ids):
        """Create progress rows for each non-excluded course in an assignment."""
        c = self._conn.cursor()
        excluded = set(excluded_ids or [])
        for course in courses:
            if course.course_id not in excluded:
                c.execute(
                    """INSERT INTO progress (learner_id, assignment_id, course_id,
                       completed, completed_date)
                       VALUES (?, ?, ?, 0, '')""",
                    (learner_id, assignment_id, course.course_id))
        self._conn.commit()

    def mark_course_completed(self, learner_id, assignment_id, course_id,
                              completed_date=""):
        c = self._conn.cursor()
        c.execute(
            """UPDATE progress SET completed = 1, completed_date = ?
               WHERE learner_id = ? AND assignment_id = ? AND course_id = ?""",
            (completed_date, learner_id, assignment_id, course_id))
        self._conn.commit()

    def get_progress_for_assignment(self, assignment_id):
        c = self._conn.cursor()
        c.execute("SELECT completed FROM progress WHERE assignment_id = ?",
                  (assignment_id,))
        rows = c.fetchall()
        total = len(rows)
        completed = sum(1 for r in rows if r[0])
        return completed, total

    def get_progress_records(self, assignment_id):
        c = self._conn.cursor()
        c.execute("SELECT * FROM progress WHERE assignment_id = ?",
                  (assignment_id,))
        return [self._row_to_progress(r) for r in c.fetchall()]

    def is_course_completed(self, learner_id, assignment_id, course_id):
        c = self._conn.cursor()
        c.execute(
            """SELECT completed FROM progress
               WHERE learner_id = ? AND assignment_id = ? AND course_id = ?""",
            (learner_id, assignment_id, course_id))
        row = c.fetchone()
        return bool(row and row[0])

    def _row_to_progress(self, row):
        return Progress(
            progress_id=row[0], learner_id=row[1], assignment_id=row[2],
            course_id=row[3], completed=bool(row[4]), completed_date=row[5])
