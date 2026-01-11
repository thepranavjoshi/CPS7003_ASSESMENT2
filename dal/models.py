from __future__ import annotations

from datetime import date, datetime
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Artefact(Base):
    __tablename__ = "artefacts"

    artefact_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    material: Mapped[str | None] = mapped_column(String(100))
    acquisition_date: Mapped[date | None] = mapped_column(Date)
    last_conservation_date: Mapped[date | None] = mapped_column(Date)

    conservation_records = relationship("ConservationRecord", back_populates="artefact", cascade="all, delete-orphan")
    exhibits = relationship("Exhibit", secondary="exhibit_artefacts", back_populates="artefacts")

class Exhibit(Base):
    __tablename__ = "exhibits"

    exhibit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)

    __table_args__ = (
        CheckConstraint("(end_date IS NULL) OR (start_date IS NULL) OR (end_date >= start_date)", name="ck_exhibit_dates"),
    )

    artefacts = relationship("Artefact", secondary="exhibit_artefacts", back_populates="exhibits")
    visits = relationship("Visit", back_populates="exhibit", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="exhibit", cascade="all, delete-orphan")

class ExhibitArtefact(Base):
    __tablename__ = "exhibit_artefacts"
    exhibit_id: Mapped[int] = mapped_column(ForeignKey("exhibits.exhibit_id", ondelete="CASCADE"), primary_key=True)
    artefact_id: Mapped[int] = mapped_column(ForeignKey("artefacts.artefact_id", ondelete="CASCADE"), primary_key=True)

    __table_args__ = (
        Index("ix_exhibit_artefacts_exhibit", "exhibit_id"),
        Index("ix_exhibit_artefacts_artefact", "artefact_id"),
    )

class Visitor(Base):
    __tablename__ = "visitors"

    visitor_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)

    # Demographics (keep minimal to support GDPR discussion)
    age_band: Mapped[str | None] = mapped_column(String(50))
    region: Mapped[str | None] = mapped_column(String(80))
    membership_type: Mapped[str | None] = mapped_column(String(40))  # e.g. Standard / Student / Member

    visits = relationship("Visit", back_populates="visitor", cascade="all, delete-orphan")
    tickets = relationship("TicketPurchase", back_populates="visitor", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="visitor", cascade="all, delete-orphan")

class Visit(Base):
    __tablename__ = "visits"

    visit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visitor_id: Mapped[int] = mapped_column(ForeignKey("visitors.visitor_id", ondelete="CASCADE"), nullable=False)
    exhibit_id: Mapped[int] = mapped_column(ForeignKey("exhibits.exhibit_id", ondelete="CASCADE"), nullable=False)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)

    visitor = relationship("Visitor", back_populates="visits")
    exhibit = relationship("Exhibit", back_populates="visits")

    __table_args__ = (
        Index("ix_visits_exhibit_date", "exhibit_id", "visit_date"),
        Index("ix_visits_visitor_date", "visitor_id", "visit_date"),
    )

class ConservationRecord(Base):
    __tablename__ = "conservation_records"

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artefact_id: Mapped[int] = mapped_column(ForeignKey("artefacts.artefact_id", ondelete="CASCADE"), nullable=False)
    condition: Mapped[str] = mapped_column(String(120), nullable=False)
    treatment: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    artefact = relationship("Artefact", back_populates="conservation_records")

    __table_args__ = (
        Index("ix_conservation_due_date", "due_date"),
    )

class TicketPurchase(Base):
    __tablename__ = "ticket_purchases"

    purchase_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visitor_id: Mapped[int] = mapped_column(ForeignKey("visitors.visitor_id", ondelete="CASCADE"), nullable=False)
    ticket_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Adult/Student/Member
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    visitor = relationship("Visitor", back_populates="tickets")

    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_ticket_price_nonneg"),
        Index("ix_ticket_purchase_date", "purchase_date"),
    )

class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visitor_id: Mapped[int] = mapped_column(ForeignKey("visitors.visitor_id", ondelete="CASCADE"), nullable=False)
    exhibit_id: Mapped[int] = mapped_column(ForeignKey("exhibits.exhibit_id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comments: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    visitor = relationship("Visitor", back_populates="feedback")
    exhibit = relationship("Exhibit", back_populates="feedback")

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating_range"),
        Index("ix_feedback_exhibit_submitted", "exhibit_id", "submitted_at"),
    )

class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)  # admin/curator/front_desk
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('admin','curator','front_desk')", name="ck_user_role"),
    )
