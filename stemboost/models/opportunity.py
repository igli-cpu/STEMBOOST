class Opportunity:
    """An internship or academic opportunity posted by a mentor."""

    def __init__(self, opportunity_id=None, title="", description="",
                 opp_type="internship", posted_by=None, posted_date=None):
        self.opportunity_id = opportunity_id
        self.title = title
        self.description = description
        self.opp_type = opp_type  # "internship" or "academic"
        self.posted_by = posted_by
        self.posted_date = posted_date

    def __repr__(self):
        return f"<Opportunity id={self.opportunity_id} title={self.title!r}>"
