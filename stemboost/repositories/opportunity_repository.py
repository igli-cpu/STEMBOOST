from stemboost.models.opportunity import Opportunity


class OpportunityRepository:
    """Handles all opportunity persistence operations."""

    def __init__(self, conn):
        self._conn = conn

    def create_opportunity(self, title, description, opp_type, posted_by,
                           posted_date=""):
        c = self._conn.cursor()
        c.execute(
            """INSERT INTO opportunities (title, description, opp_type,
               posted_by, posted_date) VALUES (?, ?, ?, ?, ?)""",
            (title, description, opp_type, posted_by, posted_date))
        self._conn.commit()
        return c.lastrowid

    def get_all_opportunities(self):
        c = self._conn.cursor()
        c.execute("SELECT * FROM opportunities")
        return [self._row_to_opportunity(r) for r in c.fetchall()]

    def _row_to_opportunity(self, row):
        return Opportunity(
            opportunity_id=row[0], title=row[1], description=row[2],
            opp_type=row[3], posted_by=row[4], posted_date=row[5])
