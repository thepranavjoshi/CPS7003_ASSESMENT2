from __future__ import annotations

import getpass
from datetime import date
from sqlalchemy.exc import IntegrityError

from dal.db import get_session
from security.auth import authenticate, AuthenticationError
from security.rbac import require_role, PermissionError, Actor
from business.validators import (
    ValidationError, parse_date, validate_email, validate_rating, validate_price
)
from dal import repositories as repo
from business.forecasting import seasonal_naive_forecast

def _input(prompt: str) -> str:
    return input(prompt).strip()

def login() -> Actor:
    print("=== HeritagePlus Museum System ===")
    username = _input("Username: ")
    password = getpass.getpass("Password: ")
    with get_session() as session:
        return authenticate(session, username, password)

def run() -> None:
    actor = login()
    print(f"Logged in as {actor.username} ({actor.role})")

    while True:
        print("\nMenu:")
        print("1) Add artefact")
        print("2) Add exhibit")
        print("3) Add visitor")
        print("4) Record visit")
        print("5) Sell ticket")
        print("6) Leave feedback")
        print("7) Add conservation record")
        print("8) Reports (analytics + forecast)")
        print("9) Exit")

        choice = _input("Choose: ")
        try:
            if choice == "1":
                require_role(actor, {"admin", "curator"})
                _add_artefact()
            elif choice == "2":
                require_role(actor, {"admin", "curator"})
                _add_exhibit()
            elif choice == "3":
                require_role(actor, {"admin", "front_desk"})
                _add_visitor()
            elif choice == "4":
                require_role(actor, {"admin", "front_desk"})
                _record_visit()
            elif choice == "5":
                require_role(actor, {"admin", "front_desk"})
                _sell_ticket()
            elif choice == "6":
                _leave_feedback()
            elif choice == "7":
                require_role(actor, {"admin", "curator"})
                _add_conservation()
            elif choice == "8":
                require_role(actor, {"admin", "curator"})
                _reports()
            elif choice == "9":
                print("Bye!")
                return
            else:
                print("Invalid choice.")
        except (ValidationError, IntegrityError, PermissionError) as e:
            print(f"Error: {e}")

def _add_artefact():
    name = _input("Name: ")
    description = _input("Description (optional): ") or None
    material = _input("Material (optional): ") or None
    acq = _input("Acquisition date YYYY-MM-DD (optional): ") or None
    acq_date = parse_date(acq) if acq else None

    with get_session() as session:
        a = repo.create_artefact(session, name, description, material, acq_date)
        print(f"Artefact created with id={a.artefact_id}")

def _add_exhibit():
    title = _input("Title: ")
    sd = _input("Start date YYYY-MM-DD (optional): ") or None
    ed = _input("End date YYYY-MM-DD (optional): ") or None
    start = parse_date(sd) if sd else None
    end = parse_date(ed) if ed else None

    with get_session() as session:
        e = repo.create_exhibit(session, title, start, end)
        print(f"Exhibit created with id={e.exhibit_id}")

def _add_visitor():
    full_name = _input("Full name: ")
    email = _input("Email: ")
    validate_email(email)
    age_band = _input("Age band (optional): ") or None
    region = _input("Region (optional): ") or None
    membership_type = _input("Membership type (optional): ") or None

    with get_session() as session:
        v = repo.create_visitor(session, full_name, email, age_band, region, membership_type)
        print(f"Visitor created with id={v.visitor_id}")

def _record_visit():
    visitor_id = int(_input("Visitor id: "))
    exhibit_id = int(_input("Exhibit id: "))
    vd = parse_date(_input("Visit date YYYY-MM-DD: "))

    with get_session() as session:
        visit = repo.record_visit(session, visitor_id, exhibit_id, vd)
        print(f"Visit recorded with id={visit.visit_id}")

def _sell_ticket():
    visitor_id = int(_input("Visitor id: "))
    ticket_type = _input("Ticket type (Adult/Student/Member): ")
    price = float(_input("Price: "))
    validate_price(price)

    with get_session() as session:
        t = repo.record_ticket_purchase(session, visitor_id, ticket_type, price)
        print(f"Ticket purchase recorded with id={t.purchase_id}")

def _leave_feedback():
    visitor_id = int(_input("Visitor id: "))
    exhibit_id = int(_input("Exhibit id: "))
    rating = int(_input("Rating (1-5): "))
    validate_rating(rating)
    comments = _input("Comments (optional): ") or None

    with get_session() as session:
        fb = repo.record_feedback(session, visitor_id, exhibit_id, rating, comments)
        print(f"Feedback recorded with id={fb.feedback_id}")

def _add_conservation():
    artefact_id = int(_input("Artefact id: "))
    condition = _input("Condition (e.g. Good/Fair/Poor): ")
    treatment = _input("Treatment (optional): ") or None
    due = _input("Due date YYYY-MM-DD (optional): ") or None
    due_date = parse_date(due) if due else None
    notes = _input("Notes (optional): ") or None

    with get_session() as session:
        rec = repo.add_conservation_record(session, artefact_id, condition, treatment, due_date, notes)
        print(f"Conservation record created with id={rec.record_id}")

def _reports():
    with get_session() as session:
        print("\n-- Top exhibits by visits --")
        for row in repo.visit_counts_by_exhibit(session):
            print(f"{row.title}: {row.visit_count}")

        print("\n-- Top visitors --")
        for row in repo.top_visitors(session):
            print(f"{row.full_name} ({row.email}): {row.visits}")

        print("\n-- Average rating by exhibit --")
        for row in repo.average_rating_by_exhibit(session):
            print(f"{row.title}: {float(row.avg_rating):.2f} ({row.num_feedback} reviews)")

        print("\n-- Conservation due in 30 days --")
        for row in repo.conservation_due_soon(session, within_days=30):
            print(f"{row.name}: due {row.due_date} (condition: {row.condition})")

        print("\n-- Forecast (next 3 months visits) --")
        monthly = [(r.ym, int(r.count)) for r in repo.monthly_visit_counts(session)]
        for fp in seasonal_naive_forecast(monthly, months_ahead=3):
            print(f"{fp.year_month}: {fp.predicted_visits} ({fp.method})")
