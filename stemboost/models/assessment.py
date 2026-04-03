class Assessment:
    """Initial assessment to determine a learner's interests and skill level."""

    STEM_FIELDS = [
        "Computer Science",
        "Mathematics",
        "Biology",
        "Chemistry",
        "Physics",
        "Engineering",
        "Data Science",
        "Environmental Science",
    ]

    SKILL_LEVELS = ["Beginner", "Intermediate", "Advanced"]

    def __init__(self, selected_interests=None, skill_level="Beginner"):
        self.selected_interests = selected_interests or []
        self.skill_level = skill_level

    def is_complete(self):
        return len(self.selected_interests) > 0
