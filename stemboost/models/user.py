import json


class User:
    """Base class for all system users."""

    def __init__(self, user_id=None, username="", email="", password_hash="",
                 name="", role=""):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.name = name
        self.role = role

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.user_id} name={self.name!r}>"


class Educator(User):
    """An educator who creates learning paths, courses, and content."""

    def __init__(self, expertise_areas=None, **kwargs):
        super().__init__(role="educator", **kwargs)
        self.expertise_areas = expertise_areas or []

    def get_expertise_areas_json(self):
        return json.dumps(self.expertise_areas)

    @staticmethod
    def parse_expertise_areas(json_str):
        if not json_str:
            return []
        return json.loads(json_str)


class Mentor(User):
    """A mentor who assigns content to learners and monitors progress."""

    def __init__(self, **kwargs):
        super().__init__(role="mentor", **kwargs)


class Learner(User):
    """A learner who consumes assigned content with accessibility support."""

    def __init__(self, vision_type="blind", accessibility_prefs=None,
                 stem_interests=None, mentor_id=None, **kwargs):
        super().__init__(role="learner", **kwargs)
        self.vision_type = vision_type
        self.accessibility_prefs = accessibility_prefs or {
            "audio": True,
            "high_contrast": False,
            "large_text": False,
        }
        self.stem_interests = stem_interests or []
        self.mentor_id = mentor_id

    def get_accessibility_prefs_json(self):
        return json.dumps(self.accessibility_prefs)

    def get_stem_interests_json(self):
        return json.dumps(self.stem_interests)

    @staticmethod
    def parse_accessibility_prefs(json_str):
        if not json_str:
            return {"audio": True, "high_contrast": False, "large_text": False}
        return json.loads(json_str)

    @staticmethod
    def parse_stem_interests(json_str):
        if not json_str:
            return []
        return json.loads(json_str)
