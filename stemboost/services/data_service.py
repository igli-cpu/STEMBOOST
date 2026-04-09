import sqlite3
import os

from stemboost.repositories.user_repository import UserRepository
from stemboost.repositories.learning_path_repository import LearningPathRepository
from stemboost.repositories.course_repository import CourseRepository
from stemboost.repositories.content_repository import ContentRepository
from stemboost.repositories.assignment_repository import AssignmentRepository
from stemboost.repositories.progress_repository import ProgressRepository
from stemboost.repositories.opportunity_repository import OpportunityRepository


class DataService:
    """Facade over repository classes. Owns the SQLite connection and delegates
    all CRUD operations to the appropriate repository.

    This preserves a single entry point for the data layer while each
    repository class satisfies the Single Responsibility Principle.
    """

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
        self._init_repositories()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def _ensure_connected(self):
        if self._conn is None:
            self.connect()
        return self._conn

    def _init_repositories(self):
        self._users = UserRepository(self._conn)
        self._paths = LearningPathRepository(self._conn)
        self._courses = CourseRepository(self._conn)
        self._contents = ContentRepository(self._conn)
        self._assignments = AssignmentRepository(self._conn)
        self._progress = ProgressRepository(self._conn)
        self._opportunities = OpportunityRepository(self._conn)

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
        c = self._conn.cursor()
        for table in ("progress", "assignments", "contents", "courses",
                      "learning_paths", "opportunities", "users"):
            c.execute(f"DROP TABLE IF EXISTS {table}")
        self._conn.commit()
        self._create_tables()
        self._init_repositories()

    # ------------------------------------------------------------------ #
    # User delegation
    # ------------------------------------------------------------------ #
    def create_user(self, **kwargs):
        return self._users.create_user(**kwargs)

    def authenticate(self, username, password):
        return self._users.authenticate(username, password)

    def get_user_by_id(self, user_id):
        return self._users.get_user_by_id(user_id)

    def get_users_by_role(self, role):
        return self._users.get_users_by_role(role)

    def get_learners_by_mentor(self, mentor_id):
        return self._users.get_learners_by_mentor(mentor_id)

    def update_user_accessibility(self, user_id, prefs):
        self._users.update_user_accessibility(user_id, prefs)

    def update_user_stem_interests(self, user_id, interests):
        self._users.update_user_stem_interests(user_id, interests)

    def update_educator_expertise(self, user_id, areas):
        self._users.update_educator_expertise(user_id, areas)

    def has_users(self):
        return self._users.has_users()

    # ------------------------------------------------------------------ #
    # Learning Path delegation
    # ------------------------------------------------------------------ #
    def create_learning_path(self, title, description, category, created_by):
        return self._paths.create_learning_path(title, description, category,
                                                created_by)

    def get_all_learning_paths(self):
        return self._paths.get_all_learning_paths()

    def get_learning_path_by_id(self, path_id):
        return self._paths.get_learning_path_by_id(path_id)

    def get_paths_by_educator(self, educator_id):
        return self._paths.get_paths_by_educator(educator_id)

    def update_learning_path(self, path_id, title, description, category):
        self._paths.update_learning_path(path_id, title, description, category)

    def delete_learning_path(self, path_id):
        self._paths.delete_learning_path(path_id)

    # ------------------------------------------------------------------ #
    # Course delegation
    # ------------------------------------------------------------------ #
    def create_course(self, title, description, path_id, created_by,
                      order_index=0):
        return self._courses.create_course(title, description, path_id,
                                           created_by, order_index)

    def get_courses_by_path(self, path_id):
        return self._courses.get_courses_by_path(path_id)

    def update_course(self, course_id, title, description):
        self._courses.update_course(course_id, title, description)

    def delete_course(self, course_id):
        self._courses.delete_course(course_id)

    # ------------------------------------------------------------------ #
    # Content delegation
    # ------------------------------------------------------------------ #
    def create_content(self, title, text_body, course_id, created_by,
                       order_index=0):
        return self._contents.create_content(title, text_body, course_id,
                                             created_by, order_index)

    def get_contents_by_course(self, course_id):
        return self._contents.get_contents_by_course(course_id)

    def update_content(self, content_id, title, text_body):
        self._contents.update_content(content_id, title, text_body)

    def delete_content(self, content_id):
        self._contents.delete_content(content_id)

    # ------------------------------------------------------------------ #
    # Assignment delegation
    # ------------------------------------------------------------------ #
    def create_assignment(self, mentor_id, learner_id, path_id,
                          excluded_course_ids=None, assigned_date=""):
        aid = self._assignments.create_assignment(
            mentor_id, learner_id, path_id, excluded_course_ids, assigned_date)
        # Create progress rows for each non-excluded course
        courses = self._courses.get_courses_by_path(path_id)
        self._progress.create_progress_rows(
            learner_id, aid, courses, excluded_course_ids)
        return aid

    def get_assignment_for_learner_path(self, learner_id, path_id):
        return self._assignments.get_assignment_for_learner_path(
            learner_id, path_id)

    def update_excluded_courses(self, assignment_id, excluded_course_ids):
        self._assignments.update_excluded_courses(
            assignment_id, excluded_course_ids)

    def get_assignments_by_learner(self, learner_id):
        return self._assignments.get_assignments_by_learner(learner_id)

    def get_assignments_by_mentor(self, mentor_id):
        return self._assignments.get_assignments_by_mentor(mentor_id)

    # ------------------------------------------------------------------ #
    # Progress delegation
    # ------------------------------------------------------------------ #
    def create_progress_row(self, learner_id, assignment_id, course_id):
        self._progress.create_progress_row(learner_id, assignment_id,
                                           course_id)

    def get_tracked_course_ids(self, assignment_id):
        return self._progress.get_tracked_course_ids(assignment_id)

    def mark_course_completed(self, learner_id, assignment_id, course_id,
                              completed_date=""):
        self._progress.mark_course_completed(learner_id, assignment_id,
                                             course_id, completed_date)

    def get_progress_for_assignment(self, assignment_id):
        return self._progress.get_progress_for_assignment(assignment_id)

    def get_progress_records(self, assignment_id):
        return self._progress.get_progress_records(assignment_id)

    def is_course_completed(self, learner_id, assignment_id, course_id):
        return self._progress.is_course_completed(learner_id, assignment_id,
                                                  course_id)

    # ------------------------------------------------------------------ #
    # Opportunity delegation
    # ------------------------------------------------------------------ #
    def create_opportunity(self, title, description, opp_type, posted_by,
                           posted_date=""):
        return self._opportunities.create_opportunity(title, description,
                                                      opp_type, posted_by,
                                                      posted_date)

    def get_all_opportunities(self):
        return self._opportunities.get_all_opportunities()
