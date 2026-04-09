from stemboost.models.course import LearningPath


class LearningPathRepository:
    """Handles all learning path persistence operations."""

    def __init__(self, conn):
        self._conn = conn

    def create_learning_path(self, title, description, category, created_by):
        c = self._conn.cursor()
        c.execute(
            """INSERT INTO learning_paths (title, description, category, created_by)
               VALUES (?, ?, ?, ?)""",
            (title, description, category, created_by))
        self._conn.commit()
        return c.lastrowid

    def get_all_learning_paths(self):
        c = self._conn.cursor()
        c.execute("SELECT * FROM learning_paths")
        return [self._row_to_path(r) for r in c.fetchall()]

    def get_learning_path_by_id(self, path_id):
        c = self._conn.cursor()
        c.execute("SELECT * FROM learning_paths WHERE path_id = ?", (path_id,))
        row = c.fetchone()
        if row is None:
            return None
        return self._row_to_path(row)

    def get_paths_by_educator(self, educator_id):
        c = self._conn.cursor()
        c.execute("SELECT * FROM learning_paths WHERE created_by = ?",
                  (educator_id,))
        return [self._row_to_path(r) for r in c.fetchall()]

    def update_learning_path(self, path_id, title, description, category):
        c = self._conn.cursor()
        c.execute(
            """UPDATE learning_paths SET title=?, description=?, category=?
               WHERE path_id=?""",
            (title, description, category, path_id))
        self._conn.commit()

    def delete_learning_path(self, path_id):
        """Delete a path and cascade to courses, contents, assignments, and progress."""
        c = self._conn.cursor()
        # Clean up progress records for assignments linked to this path
        c.execute("DELETE FROM progress WHERE assignment_id IN "
                  "(SELECT assignment_id FROM assignments WHERE path_id = ?)",
                  (path_id,))
        # Clean up assignments linked to this path
        c.execute("DELETE FROM assignments WHERE path_id = ?", (path_id,))
        # Clean up contents in courses of this path
        c.execute("DELETE FROM contents WHERE course_id IN "
                  "(SELECT course_id FROM courses WHERE path_id = ?)", (path_id,))
        c.execute("DELETE FROM courses WHERE path_id = ?", (path_id,))
        c.execute("DELETE FROM learning_paths WHERE path_id = ?", (path_id,))
        self._conn.commit()

    def _row_to_path(self, row):
        return LearningPath(
            path_id=row[0], title=row[1], description=row[2],
            category=row[3], created_by=row[4])
