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
