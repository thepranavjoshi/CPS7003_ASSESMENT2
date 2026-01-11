from __future__ import annotations

from datetime import datetime
from dal.db import get_session
from dal import repositories as repo

def add_visitor(full_name: str, email: str, age_band: str | None = None, region: str | None = None, membership_type: str | None = None):
    with get_session() as session:
        return repo.create_visitor(session, full_name, email, age_band, region, membership_type)

def add_visit(visitor_id: int, exhibit_id: int, visit_date: str):
    vd = datetime.strptime(visit_date, "%Y-%m-%d").date()
    with get_session() as session:
        return repo.record_visit(session, visitor_id, exhibit_id, vd)

def get_visit_counts_by_exhibit():
    with get_session() as session:
        return repo.visit_counts_by_exhibit(session)
