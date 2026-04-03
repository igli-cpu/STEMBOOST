class LearningPath:
    """A curated sequence of courses within a STEM focus area."""

    def __init__(self, path_id=None, title="", description="", category="",
                 created_by=None):
        self.path_id = path_id
        self.title = title
        self.description = description
        self.category = category
        self.created_by = created_by

    def __repr__(self):
        return f"<LearningPath id={self.path_id} title={self.title!r}>"


class Course:
    """A module within a learning path containing content units."""

    def __init__(self, course_id=None, title="", description="", path_id=None,
                 created_by=None, order_index=0):
        self.course_id = course_id
        self.title = title
        self.description = description
        self.path_id = path_id
        self.created_by = created_by
        self.order_index = order_index

    def __repr__(self):
        return f"<Course id={self.course_id} title={self.title!r}>"


class Content:
    """The smallest deliverable unit within a course. Text read aloud via TTS."""

    def __init__(self, content_id=None, title="", text_body="", course_id=None,
                 created_by=None, order_index=0):
        self.content_id = content_id
        self.title = title
        self.text_body = text_body
        self.course_id = course_id
        self.created_by = created_by
        self.order_index = order_index

    def __repr__(self):
        return f"<Content id={self.content_id} title={self.title!r}>"
