import json


class User:
    """Base class for all system users.

    Provides default values for all role-specific attributes so that any
    User subclass can be used interchangeably (Liskov Substitution Principle).
    """

    def __init__(self, user_id=None, username="", email="", password_hash="",
                 name="", role=""):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.name = name
        self.role = role
        # Defaults for role-specific attributes (LSP: any User subclass is
        # substitutable without checking its concrete type first).
        self.accessibility_prefs = {}
        self.vision_type = ""
        self.stem_interests = []
        self.mentor_id = None
        self.expertise_areas = []

    @classmethod
    def _base_kwargs(cls, row_dict):
        """Extract the common constructor kwargs from a DB row dict."""
        return {
            "user_id": row_dict["user_id"],
            "username": row_dict["username"],
            "email": row_dict["email"],
            "password_hash": row_dict["password_hash"],
            "name": row_dict["name"],
        }

    @classmethod
    def from_db_row(cls, row_dict):
        """Construct a base User from a database row dictionary."""
        return cls(**cls._base_kwargs(row_dict))

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.user_id} name={self.name!r}>"


class Educator(User):
    """An educator who creates learning paths, courses, and content."""

    def __init__(self, expertise_areas=None, **kwargs):
        super().__init__(role="educator", **kwargs)
        self.expertise_areas = expertise_areas or []

    @classmethod
    def from_db_row(cls, row_dict):
        """Construct an Educator from a DB row, parsing expertise_areas JSON."""
        kwargs = cls._base_kwargs(row_dict)
        kwargs["expertise_areas"] = json.loads(
            row_dict.get("expertise_areas") or "[]")
        return cls(**kwargs)

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

    @classmethod
    def from_db_row(cls, row_dict):
        """Construct a Mentor from a DB row."""
        return cls(**cls._base_kwargs(row_dict))


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

    @classmethod
    def from_db_row(cls, row_dict):
        """Construct a Learner from a DB row, parsing JSON fields."""
        kwargs = cls._base_kwargs(row_dict)
        kwargs["vision_type"] = row_dict.get("vision_type") or "blind"
        kwargs["accessibility_prefs"] = json.loads(
            row_dict.get("accessibility_prefs") or "{}")
        kwargs["stem_interests"] = json.loads(
            row_dict.get("stem_interests") or "[]")
        kwargs["mentor_id"] = row_dict.get("mentor_id")
        return cls(**kwargs)

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
