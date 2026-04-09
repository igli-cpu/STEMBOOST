from stemboost.models.course import Course


class CourseRepository:
    """Handles all course persistence operations."""

    def __init__(self, conn):
        self._conn = conn

    def create_course(self, title, description, path_id, created_by,
                      order_index=0):
        c = self._conn.cursor()
        c.execute(
            """INSERT INTO courses (title, description, path_id, created_by, order_index)
               VALUES (?, ?, ?, ?, ?)""",
            (title, description, path_id, created_by, order_index))
        self._conn.commit()
        return c.lastrowid

    def get_courses_by_path(self, path_id):
        c = self._conn.cursor()
        c.execute("SELECT * FROM courses WHERE path_id = ? ORDER BY order_index",
                  (path_id,))
        return [self._row_to_course(r) for r in c.fetchall()]

    def update_course(self, course_id, title, description):
        c = self._conn.cursor()
        c.execute("UPDATE courses SET title=?, description=? WHERE course_id=?",
                  (title, description, course_id))
        self._conn.commit()

    def delete_course(self, course_id):
        c = self._conn.cursor()
        c.execute("DELETE FROM contents WHERE course_id = ?", (course_id,))
        c.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
        self._conn.commit()

    def _row_to_course(self, row):
        return Course(
            course_id=row[0], title=row[1], description=row[2],
            path_id=row[3], created_by=row[4], order_index=row[5])
