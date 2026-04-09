from stemboost.models.user import Educator, Mentor, Learner


class UserFactory:
    """Factory pattern: creates the appropriate User subclass from a role string."""

    _registry = {
        "educator": Educator,
        "mentor": Mentor,
        "learner": Learner,
    }

    @classmethod
    def create_user(cls, role, **kwargs):
        user_class = cls._registry.get(role)
        if user_class is None:
            raise ValueError(f"Unknown role: {role!r}")
        return user_class(**kwargs)

    @classmethod
    def create_from_row(cls, role, row_dict):
        """Construct the appropriate User subclass from a database row dict.

        Each subclass's from_db_row() knows how to parse its own fields,
        so the factory doesn't need role-specific if/elif logic.
        """
        user_class = cls._registry.get(role)
        if user_class is None:
            raise ValueError(f"Unknown role: {role!r}")
        return user_class.from_db_row(row_dict)
