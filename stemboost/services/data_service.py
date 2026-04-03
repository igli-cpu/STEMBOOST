import sqlite3
import hashlib
import json
import os

from stemboost.models.user import Educator, Mentor, Learner
from stemboost.models.user_factory import UserFactory
from stemboost.models.course import LearningPath, Course, Content
from stemboost.models.progress import Assignment, Progress
from stemboost.models.opportunity import Opportunity


def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class DataService:
    """SQLite persistence layer for all STEMBOOST data."""

    def __init__(self, db_path=None):
        if db_path is None:
            db_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(db_dir, "..", "data", "stemboost.db")
        self.db_path = db_path if db_path == ":memory:" else os.path.abspath(db_path)
        self._conn = None

    def connect(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            self.connect()
        return self._conn

    # ------------------------------------------------------------------ #
    # Table creation
    # ------------------------------------------------------------------ #
    def _create_tables(self):
        c = self._conn.cursor()
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                vision_type TEXT DEFAULT '',
                accessibility_prefs TEXT DEFAULT '{}',
                stem_interests TEXT DEFAULT '[]',
                expertise_areas TEXT DEFAULT '[]',
                mentor_id INTEGER DEFAULT NULL,
                FOREIGN KEY (mentor_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS learning_paths (
                path_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT '',
                created_by INTEGER NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                path_id INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                order_index INTEGER DEFAULT 0,
                FOREIGN KEY (path_id) REFERENCES learning_paths(path_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS contents (
                content_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                text_body TEXT DEFAULT '',
                course_id INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                order_index INTEGER DEFAULT 0,
                FOREIGN KEY (course_id) REFERENCES courses(course_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS assignments (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                mentor_id INTEGER NOT NULL,
                learner_id INTEGER NOT NULL,
                path_id INTEGER NOT NULL,
                excluded_course_ids TEXT DEFAULT '',
                assigned_date TEXT DEFAULT '',
                FOREIGN KEY (mentor_id) REFERENCES users(user_id),
                FOREIGN KEY (learner_id) REFERENCES users(user_id),
                FOREIGN KEY (path_id) REFERENCES learning_paths(path_id)
            );

            CREATE TABLE IF NOT EXISTS progress (
                progress_id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id INTEGER NOT NULL,
                assignment_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                completed INTEGER DEFAULT 0,
                completed_date TEXT DEFAULT '',
                FOREIGN KEY (learner_id) REFERENCES users(user_id),
                FOREIGN KEY (assignment_id) REFERENCES assignments(assignment_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            );

            CREATE TABLE IF NOT EXISTS opportunities (
                opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                opp_type TEXT DEFAULT 'internship',
                posted_by INTEGER NOT NULL,
                posted_date TEXT DEFAULT '',
                FOREIGN KEY (posted_by) REFERENCES users(user_id)
            );
        """)
        self._conn.commit()

    # ------------------------------------------------------------------ #
    # Reset
    # ------------------------------------------------------------------ #
    def reset_database(self):
        """Drop all tables and recreate them."""
        c = self.conn.cursor()
        for table in ("progress", "assignments", "contents", "courses",
                      "learning_paths", "opportunities", "users"):
            c.execute(f"DROP TABLE IF EXISTS {table}")
        self.conn.commit()
        self._create_tables()

    # ------------------------------------------------------------------ #
    # User CRUD
    # ------------------------------------------------------------------ #
    def create_user(self, username, email, password, name, role,
                    vision_type="", accessibility_prefs=None,
                    stem_interests=None, expertise_areas=None, mentor_id=None):
        c = self.conn.cursor()
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
        self.conn.commit()
        return c.lastrowid

    def authenticate(self, username, password):
        """Return user row dict if credentials match, else None."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?",
                  (username, _hash_password(password)))
        row = c.fetchone()
        if row is None:
            return None
        return self._row_to_user(row)

    def get_user_by_id(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row is None:
            return None
        return self._row_to_user(row)

    def get_users_by_role(self, role):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE role = ?", (role,))
        return [self._row_to_user(r) for r in c.fetchall()]

    def get_learners_by_mentor(self, mentor_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE role = 'learner' AND mentor_id = ?",
                  (mentor_id,))
        return [self._row_to_user(r) for r in c.fetchall()]

    def update_user_accessibility(self, user_id, prefs):
        c = self.conn.cursor()
        c.execute("UPDATE users SET accessibility_prefs = ? WHERE user_id = ?",
                  (json.dumps(prefs), user_id))
        self.conn.commit()

    def update_user_stem_interests(self, user_id, interests):
        c = self.conn.cursor()
        c.execute("UPDATE users SET stem_interests = ? WHERE user_id = ?",
                  (json.dumps(interests), user_id))
        self.conn.commit()

    def update_educator_expertise(self, user_id, areas):
        c = self.conn.cursor()
        c.execute("UPDATE users SET expertise_areas = ? WHERE user_id = ?",
                  (json.dumps(areas), user_id))
        self.conn.commit()

    def _row_to_user(self, row):
        cols = ("user_id", "username", "email", "password_hash", "name",
                "role", "vision_type", "accessibility_prefs", "stem_interests",
                "expertise_areas", "mentor_id")
        d = dict(zip(cols, row))
        role = d["role"]
        kwargs = {
            "user_id": d["user_id"],
            "username": d["username"],
            "email": d["email"],
            "password_hash": d["password_hash"],
            "name": d["name"],
        }
        if role == "educator":
            user = UserFactory.create_user(role, **kwargs)
            user.expertise_areas = json.loads(d["expertise_areas"] or "[]")
        elif role == "learner":
            user = UserFactory.create_user(
                role,
                vision_type=d["vision_type"] or "blind",
                accessibility_prefs=json.loads(d["accessibility_prefs"] or "{}"),
                stem_interests=json.loads(d["stem_interests"] or "[]"),
                mentor_id=d["mentor_id"],
                **kwargs,
            )
        else:
            user = UserFactory.create_user(role, **kwargs)
        return user

    # ------------------------------------------------------------------ #
    # Learning Path CRUD
    # ------------------------------------------------------------------ #
    def create_learning_path(self, title, description, category, created_by):
        c = self.conn.cursor()
        c.execute(
            """INSERT INTO learning_paths (title, description, category, created_by)
               VALUES (?, ?, ?, ?)""",
            (title, description, category, created_by))
        self.conn.commit()
        return c.lastrowid

    def get_all_learning_paths(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM learning_paths")
        return [self._row_to_path(r) for r in c.fetchall()]

    def get_paths_by_educator(self, educator_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM learning_paths WHERE created_by = ?",
                  (educator_id,))
        return [self._row_to_path(r) for r in c.fetchall()]

    def update_learning_path(self, path_id, title, description, category):
        c = self.conn.cursor()
        c.execute(
            """UPDATE learning_paths SET title=?, description=?, category=?
               WHERE path_id=?""",
            (title, description, category, path_id))
        self.conn.commit()

    def delete_learning_path(self, path_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM contents WHERE course_id IN "
                  "(SELECT course_id FROM courses WHERE path_id = ?)", (path_id,))
        c.execute("DELETE FROM courses WHERE path_id = ?", (path_id,))
        c.execute("DELETE FROM learning_paths WHERE path_id = ?", (path_id,))
        self.conn.commit()

    def _row_to_path(self, row):
        return LearningPath(
            path_id=row[0], title=row[1], description=row[2],
            category=row[3], created_by=row[4])

    # ------------------------------------------------------------------ #
    # Course CRUD
    # ------------------------------------------------------------------ #
    def create_course(self, title, description, path_id, created_by, order_index=0):
        c = self.conn.cursor()
        c.execute(
            """INSERT INTO courses (title, description, path_id, created_by, order_index)
               VALUES (?, ?, ?, ?, ?)""",
            (title, description, path_id, created_by, order_index))
        self.conn.commit()
        return c.lastrowid

    def get_courses_by_path(self, path_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM courses WHERE path_id = ? ORDER BY order_index",
                  (path_id,))
        return [self._row_to_course(r) for r in c.fetchall()]

    def update_course(self, course_id, title, description):
        c = self.conn.cursor()
        c.execute("UPDATE courses SET title=?, description=? WHERE course_id=?",
                  (title, description, course_id))
        self.conn.commit()

    def delete_course(self, course_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM contents WHERE course_id = ?", (course_id,))
        c.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
        self.conn.commit()

    def _row_to_course(self, row):
        return Course(
            course_id=row[0], title=row[1], description=row[2],
            path_id=row[3], created_by=row[4], order_index=row[5])

    # ------------------------------------------------------------------ #
    # Content CRUD
    # ------------------------------------------------------------------ #
    def create_content(self, title, text_body, course_id, created_by,
                       order_index=0):
        c = self.conn.cursor()
        c.execute(
            """INSERT INTO contents (title, text_body, course_id, created_by,
               order_index) VALUES (?, ?, ?, ?, ?)""",
            (title, text_body, course_id, created_by, order_index))
        self.conn.commit()
        return c.lastrowid

    def get_contents_by_course(self, course_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM contents WHERE course_id = ? ORDER BY order_index",
                  (course_id,))
        return [self._row_to_content(r) for r in c.fetchall()]

    def update_content(self, content_id, title, text_body):
        c = self.conn.cursor()
        c.execute("UPDATE contents SET title=?, text_body=? WHERE content_id=?",
                  (title, text_body, content_id))
        self.conn.commit()

    def delete_content(self, content_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM contents WHERE content_id = ?", (content_id,))
        self.conn.commit()

    def _row_to_content(self, row):
        return Content(
            content_id=row[0], title=row[1], text_body=row[2],
            course_id=row[3], created_by=row[4], order_index=row[5])

    # ------------------------------------------------------------------ #
    # Assignment CRUD
    # ------------------------------------------------------------------ #
    def create_assignment(self, mentor_id, learner_id, path_id,
                          excluded_course_ids=None, assigned_date=""):
        excluded_str = ",".join(str(x) for x in (excluded_course_ids or []))
        c = self.conn.cursor()
        c.execute(
            """INSERT INTO assignments (mentor_id, learner_id, path_id,
               excluded_course_ids, assigned_date)
               VALUES (?, ?, ?, ?, ?)""",
            (mentor_id, learner_id, path_id, excluded_str, assigned_date))
        self.conn.commit()
        aid = c.lastrowid

        # Create progress rows for each non-excluded course
        courses = self.get_courses_by_path(path_id)
        excluded = set(excluded_course_ids or [])
        for course in courses:
            if course.course_id not in excluded:
                c.execute(
                    """INSERT INTO progress (learner_id, assignment_id, course_id,
                       completed, completed_date)
                       VALUES (?, ?, ?, 0, '')""",
                    (learner_id, aid, course.course_id))
        self.conn.commit()
        return aid

    def get_assignments_by_learner(self, learner_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM assignments WHERE learner_id = ?", (learner_id,))
        return [self._row_to_assignment(r) for r in c.fetchall()]

    def get_assignments_by_mentor(self, mentor_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM assignments WHERE mentor_id = ?", (mentor_id,))
        return [self._row_to_assignment(r) for r in c.fetchall()]

    def _row_to_assignment(self, row):
        return Assignment(
            assignment_id=row[0], mentor_id=row[1], learner_id=row[2],
            path_id=row[3],
            excluded_course_ids=Assignment.parse_excluded_ids(row[4]),
            assigned_date=row[5])

    # ------------------------------------------------------------------ #
    # Progress
    # ------------------------------------------------------------------ #
    def mark_course_completed(self, learner_id, assignment_id, course_id,
                              completed_date=""):
        c = self.conn.cursor()
        c.execute(
            """UPDATE progress SET completed = 1, completed_date = ?
               WHERE learner_id = ? AND assignment_id = ? AND course_id = ?""",
            (completed_date, learner_id, assignment_id, course_id))
        self.conn.commit()

    def get_progress_for_assignment(self, assignment_id):
        """Return (completed_count, total_count) for an assignment."""
        c = self.conn.cursor()
        c.execute("SELECT completed FROM progress WHERE assignment_id = ?",
                  (assignment_id,))
        rows = c.fetchall()
        total = len(rows)
        completed = sum(1 for r in rows if r[0])
        return completed, total

    def get_progress_records(self, assignment_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM progress WHERE assignment_id = ?",
                  (assignment_id,))
        return [self._row_to_progress(r) for r in c.fetchall()]

    def is_course_completed(self, learner_id, assignment_id, course_id):
        c = self.conn.cursor()
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

    # ------------------------------------------------------------------ #
    # Opportunities
    # ------------------------------------------------------------------ #
    def create_opportunity(self, title, description, opp_type, posted_by,
                           posted_date=""):
        c = self.conn.cursor()
        c.execute(
            """INSERT INTO opportunities (title, description, opp_type,
               posted_by, posted_date) VALUES (?, ?, ?, ?, ?)""",
            (title, description, opp_type, posted_by, posted_date))
        self.conn.commit()
        return c.lastrowid

    def get_all_opportunities(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM opportunities")
        return [self._row_to_opportunity(r) for r in c.fetchall()]

    def _row_to_opportunity(self, row):
        return Opportunity(
            opportunity_id=row[0], title=row[1], description=row[2],
            opp_type=row[3], posted_by=row[4], posted_date=row[5])
