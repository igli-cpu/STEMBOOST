from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from stemboost.services.interfaces import DataServiceProtocol


class EducatorController:
    """Business logic for educator actions: manage paths, courses, content."""

    def __init__(self, data_service: DataServiceProtocol):
        self.ds = data_service

    def get_my_paths(self, educator_id):
        return self.ds.get_paths_by_educator(educator_id)

    def create_path(self, title, description, category, educator_id):
        if not title or not title.strip():
            raise ValueError("Learning path title is required.")
        return self.ds.create_learning_path(title, description, category,
                                            educator_id)

    def update_path(self, path_id, title, description, category):
        self.ds.update_learning_path(path_id, title, description, category)

    def delete_path(self, path_id):
        self.ds.delete_learning_path(path_id)

    def get_courses(self, path_id):
        return self.ds.get_courses_by_path(path_id)

    def create_course(self, title, description, path_id, educator_id,
                      order_index=0):
        if not title or not title.strip():
            raise ValueError("Course title is required.")
        return self.ds.create_course(title, description, path_id, educator_id,
                                     order_index)

    def update_course(self, course_id, title, description):
        self.ds.update_course(course_id, title, description)

    def delete_course(self, course_id):
        self.ds.delete_course(course_id)

    def get_contents(self, course_id):
        return self.ds.get_contents_by_course(course_id)

    def create_content(self, title, text_body, course_id, educator_id,
                       order_index=0):
        if not title or not title.strip():
            raise ValueError("Content title is required.")
        return self.ds.create_content(title, text_body, course_id, educator_id,
                                      order_index)

    def update_content(self, content_id, title, text_body):
        self.ds.update_content(content_id, title, text_body)

    def delete_content(self, content_id):
        self.ds.delete_content(content_id)

    def get_expertise(self, educator_id):
        user = self.ds.get_user_by_id(educator_id)
        return user.expertise_areas if user else []

    def update_expertise(self, educator_id, areas):
        self.ds.update_educator_expertise(educator_id, areas)
