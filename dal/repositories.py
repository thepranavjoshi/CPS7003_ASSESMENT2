from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from dal.models import (
    Artefact,
    Exhibit,
    ExhibitArtefact,
    Visitor,
    Visit,
    ConservationRecord,
    TicketPurchase,
    Feedback,
)

# --- Artefacts ---
def create_artefact(session: Session, name: str, description: str | None, material: str | None, acquisition_date: date | None) -> Artefact:
    artefact = Artefact(name=name, description=description, material=material, acquisition_date=acquisition_date)
    session.add(artefact)
    session.flush()
    return artefact

def list_artefacts(session: Session) -> list[Artefact]:
    return list(session.execute(select(Artefact).order_by(Artefact.artefact_id)).scalars())

def link_artefact_to_exhibit(session: Session, artefact_id: int, exhibit_id: int) -> None:
    session.add(ExhibitArtefact(artefact_id=artefact_id, exhibit_id=exhibit_id))

# --- Exhibits ---
def create_exhibit(session: Session, title: str, start_date: date | None, end_date: date | None) -> Exhibit:
    exhibit = Exhibit(title=title, start_date=start_date, end_date=end_date)
    session.add(exhibit)
    session.flush()
    return exhibit

def list_exhibits(session: Session) -> list[Exhibit]:
    return list(session.execute(select(Exhibit).order_by(Exhibit.exhibit_id)).scalars())

# --- Visitors / Visits ---
def create_visitor(session: Session, full_name: str, email: str, age_band: str | None = None, region: str | None = None, membership_type: str | None = None) -> Visitor:
    visitor = Visitor(full_name=full_name, email=email, age_band=age_band, region=region, membership_type=membership_type)
    session.add(visitor)
    session.flush()
    return visitor

def record_visit(session: Session, visitor_id: int, exhibit_id: int, visit_date: date) -> Visit:
    v = Visit(visitor_id=visitor_id, exhibit_id=exhibit_id, visit_date=visit_date)
    session.add(v)
    session.flush()
    return v

# --- Tickets ---
def record_ticket_purchase(session: Session, visitor_id: int, ticket_type: str, price: float) -> TicketPurchase:
    purchase = TicketPurchase(visitor_id=visitor_id, ticket_type=ticket_type, price=price)
    session.add(purchase)
    session.flush()
    return purchase

# --- Feedback ---
def record_feedback(session: Session, visitor_id: int, exhibit_id: int, rating: int, comments: str | None = None) -> Feedback:
    fb = Feedback(visitor_id=visitor_id, exhibit_id=exhibit_id, rating=rating, comments=comments)
    session.add(fb)
    session.flush()
    return fb

# --- Conservation ---
def add_conservation_record(session: Session, artefact_id: int, condition: str, treatment: str | None = None, due_date: date | None = None, notes: str | None = None) -> ConservationRecord:
    rec = ConservationRecord(artefact_id=artefact_id, condition=condition, treatment=treatment, due_date=due_date, notes=notes)
    session.add(rec)
    session.flush()
    return rec

# --- Analytics / advanced queries ---
def visit_counts_by_exhibit(session: Session, start: date | None = None, end: date | None = None):
    stmt = (
        select(
            Exhibit.exhibit_id,
            Exhibit.title,
            func.count(Visit.visit_id).label("visit_count"),
        )
        .join(Visit, Visit.exhibit_id == Exhibit.exhibit_id)
        .group_by(Exhibit.exhibit_id, Exhibit.title)
        .order_by(desc("visit_count"))
    )
    if start:
        stmt = stmt.where(Visit.visit_date >= start)
    if end:
        stmt = stmt.where(Visit.visit_date <= end)
    return session.execute(stmt).all()

def top_visitors(session: Session, limit: int = 5):
    stmt = (
        select(
            Visitor.visitor_id,
            Visitor.full_name,
            Visitor.email,
            func.count(Visit.visit_id).label("visits"),
        )
        .join(Visit, Visit.visitor_id == Visitor.visitor_id)
        .group_by(Visitor.visitor_id, Visitor.full_name, Visitor.email)
        .order_by(desc("visits"))
        .limit(limit)
    )
    return session.execute(stmt).all()

def average_rating_by_exhibit(session: Session):
    stmt = (
        select(
            Exhibit.exhibit_id,
            Exhibit.title,
            func.avg(Feedback.rating).label("avg_rating"),
            func.count(Feedback.feedback_id).label("num_feedback"),
        )
        .join(Feedback, Feedback.exhibit_id == Exhibit.exhibit_id)
        .group_by(Exhibit.exhibit_id, Exhibit.title)
        .order_by(desc("avg_rating"))
    )
    return session.execute(stmt).all()

def conservation_due_soon(session: Session, within_days: int = 30, days: int | None = None):
    """Return conservation records due soon.

    Args:
        within_days: Preferred parameter name.
        days: Backwards-compatible alias used by some callers.
    """
    if days is not None:
        within_days = days
    today = date.today()
    cutoff = today.fromordinal(today.toordinal() + within_days)
    stmt = (
        select(
            Artefact.artefact_id,
            Artefact.name,
            ConservationRecord.due_date,
            ConservationRecord.condition,
        )
        .join(ConservationRecord, ConservationRecord.artefact_id == Artefact.artefact_id)
        .where(ConservationRecord.due_date.is_not(None))
        .where(ConservationRecord.due_date <= cutoff)
        .order_by(ConservationRecord.due_date.asc())
    )
    return session.execute(stmt).all()

def monthly_visit_counts(session: Session):
    # SQLite date formatting: strftime('%Y-%m', visit_date)
    stmt = (
        select(
            func.strftime("%Y-%m", Visit.visit_date).label("ym"),
            func.count(Visit.visit_id).label("count"),
        )
        .group_by("ym")
        .order_by("ym")
    )
    return session.execute(stmt).all()
