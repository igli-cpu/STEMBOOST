import hashlib
import json
import sqlite3

from stemboost.models.user_factory import UserFactory


class DuplicateUsernameError(Exception):
    """Raised when attempting to create a user with a username that already exists."""
    pass


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class UserRepository:
    """Handles all user persistence operations."""

    def __init__(self, conn):
        self._conn = conn

    def create_user(self, username, email, password, name, role,
                    vision_type="", accessibility_prefs=None,
                    stem_interests=None, expertise_areas=None, mentor_id=None):
        c = self._conn.cursor()
        try:
            c.execute(
                """INSERT INTO users (username, email, password_hash, name, role,
                   vision_type, accessibility_prefs, stem_interests,
                   expertise_areas, mentor_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (username, email, _hash_password(password), name, role,
                 vision_type,
                 json.dumps(accessibility_prefs or {}),
                 json.dumps(stem_interests or []),
                 json.dumps(expertise_areas or []),
                 mentor_id)
            )
        except sqlite3.IntegrityError:
            raise DuplicateUsernameError(
                f"Username '{username}' is already taken.")
        self._conn.commit()
        return c.lastrowid

    def authenticate(self, username, password):
        c = self._conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?",
                  (username, _hash_password(password)))
        row = c.fetchone()
        if row is None:
            return None
        return self._row_to_user(row)

    def get_user_by_id(self, user_id):
        c = self._conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            return None
        return self._row_to_user(row)

    def get_users_by_role(self, role):
        c = self._conn.cursor()
        c.execute("SELECT * FROM users WHERE role = ?", (role,))
        return [self._row_to_user(r) for r in c.fetchall()]

    def get_learners_by_mentor(self, mentor_id):
        c = self._conn.cursor()
        c.execute("SELECT * FROM users WHERE role = 'learner' AND mentor_id = ?",
                  (mentor_id,))
        return [self._row_to_user(r) for r in c.fetchall()]

    def update_user_accessibility(self, user_id, prefs):
        c = self._conn.cursor()
        c.execute("UPDATE users SET accessibility_prefs = ? WHERE user_id = ?",
                  (json.dumps(prefs), user_id))
        self._conn.commit()

    def update_user_stem_interests(self, user_id, interests):
        c = self._conn.cursor()
        c.execute("UPDATE users SET stem_interests = ? WHERE user_id = ?",
                  (json.dumps(interests), user_id))
        self._conn.commit()

    def update_educator_expertise(self, user_id, areas):
        c = self._conn.cursor()
        c.execute("UPDATE users SET expertise_areas = ? WHERE user_id = ?",
                  (json.dumps(areas), user_id))
        self._conn.commit()

    def has_users(self):
        c = self._conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        return c.fetchone()[0] > 0

    def _row_to_user(self, row):
        cols = ("user_id", "username", "email", "password_hash", "name",
                "role", "vision_type", "accessibility_prefs", "stem_interests",
                "expertise_areas", "mentor_id")
        d = dict(zip(cols, row))
        return UserFactory.create_from_row(d["role"], d)
