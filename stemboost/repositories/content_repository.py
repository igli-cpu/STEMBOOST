from stemboost.models.course import Content


class ContentRepository:
    """Handles all content persistence operations."""

    def __init__(self, conn):
        self._conn = conn

    def create_content(self, title, text_body, course_id, created_by,
                       order_index=0):
        c = self._conn.cursor()
        c.execute(
            """INSERT INTO contents (title, text_body, course_id, created_by,
               order_index) VALUES (?, ?, ?, ?, ?)""",
            (title, text_body, course_id, created_by, order_index))
        self._conn.commit()
        return c.lastrowid

    def get_contents_by_course(self, course_id):
        c = self._conn.cursor()
        c.execute("SELECT * FROM contents WHERE course_id = ? ORDER BY order_index",
                  (course_id,))
        return [self._row_to_content(r) for r in c.fetchall()]

    def update_content(self, content_id, title, text_body):
        c = self._conn.cursor()
        c.execute("UPDATE contents SET title=?, text_body=? WHERE content_id=?",
                  (title, text_body, content_id))
        self._conn.commit()

    def delete_content(self, content_id):
        c = self._conn.cursor()
        c.execute("DELETE FROM contents WHERE content_id = ?", (content_id,))
        self._conn.commit()

    def _row_to_content(self, row):
        return Content(
            content_id=row[0], title=row[1], text_body=row[2],
            course_id=row[3], created_by=row[4], order_index=row[5])
