from __future__ import annotations

from datetime import date, datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from dal.db import get_session
from dal import repositories as repo
from security.auth import authenticate, AuthenticationError
from security.rbac import require_role, PermissionError as RBACPermissionError, Actor
from business.forecasting import seasonal_naive_forecast

bp = Blueprint("web", __name__)

def current_actor() -> Actor | None:
    u = session.get("username")
    r = session.get("role")
    if not u or not r:
        return None
    return Actor(username=u, role=r)

def login_required():
    def decorator(fn):
        from functools import wraps
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_actor():
                return redirect(url_for("web.login", next=request.path))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def role_required(*roles: str):
    def decorator(fn):
        from functools import wraps
        @wraps(fn)
        def wrapper(*args, **kwargs):
            actor = current_actor()
            if not actor:
                return redirect(url_for("web.login", next=request.path))
            try:
                require_role(actor, set(roles))
            except RBACPermissionError as e:
                flash(str(e), "error")
                return redirect(url_for("web.dashboard"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator

@bp.get("/")
def index():
    if current_actor():
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        with get_session() as db:
            try:
                actor = authenticate(db, username, password)
                session["username"] = actor.username
                session["role"] = actor.role
                flash(f"Welcome, {actor.username} ({actor.role})", "success")
                nxt = request.args.get("next")
                return redirect(nxt or url_for("web.dashboard"))
            except AuthenticationError:
                flash("Invalid username or password", "error")
    return render_template("login.html")

@bp.get("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("web.login"))

@bp.get("/dashboard")
@login_required()
def dashboard():
    actor = current_actor()
    with get_session() as db:
        visits_by_exhibit = repo.visit_counts_by_exhibit(db)
        avg_ratings = repo.average_rating_by_exhibit(db)
        due_soon = repo.conservation_due_soon(db, days=30)
        monthly = repo.monthly_visit_counts(db)
        # monthly is list of Row(ym, count) - convert to tuples
        monthly_tuples = [(row.ym, int(row.count)) for row in monthly]
        forecast = seasonal_naive_forecast(monthly_tuples, months_ahead=3) if monthly_tuples else []

    return render_template(
        "dashboard.html",
        actor=actor,
        visits_by_exhibit=visits_by_exhibit,
        avg_ratings=avg_ratings,
        due_soon=due_soon,
        monthly=monthly_tuples,
        forecast=forecast,
    )

# -------------------- Artefacts --------------------
@bp.get("/artefacts")
@login_required()
def artefacts():
    with get_session() as db:
        items = repo.list_artefacts(db)
    return render_template("artefacts.html", actor=current_actor(), artefacts=items)

@bp.route("/artefacts/new", methods=["GET","POST"])
@role_required("admin","curator")
def artefact_new():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        description = request.form.get("description","").strip()
        material = request.form.get("material","").strip()
        acquisition_date = request.form.get("acquisition_date","").strip()
        try:
            ad = date.fromisoformat(acquisition_date) if acquisition_date else None
        except ValueError:
            flash("Acquisition date must be YYYY-MM-DD", "error")
            return render_template("artefact_new.html", actor=current_actor())
        if not name:
            flash("Name is required", "error")
            return render_template("artefact_new.html", actor=current_actor())
        with get_session() as db:
            repo.create_artefact(db, name=name, description=description, material=material, acquisition_date=ad)
        flash("Artefact created.", "success")
        return redirect(url_for("web.artefacts"))
    return render_template("artefact_new.html", actor=current_actor())

# -------------------- Exhibits --------------------
@bp.get("/exhibits")
@login_required()
def exhibits():
    with get_session() as db:
        items = repo.list_exhibits(db)
    return render_template("exhibits.html", actor=current_actor(), exhibits=items)

@bp.route("/exhibits/new", methods=["GET","POST"])
@role_required("admin","curator")
def exhibit_new():
    if request.method == "POST":
        title = request.form.get("title","").strip()
        start_date = request.form.get("start_date","").strip()
        end_date = request.form.get("end_date","").strip()
        if not title:
            flash("Title is required", "error")
            return render_template("exhibit_new.html", actor=current_actor())
        try:
            sd = date.fromisoformat(start_date) if start_date else None
            ed = date.fromisoformat(end_date) if end_date else None
        except ValueError:
            flash("Dates must be YYYY-MM-DD", "error")
            return render_template("exhibit_new.html", actor=current_actor())
        with get_session() as db:
            repo.create_exhibit(db, title=title, start_date=sd, end_date=ed)
        flash("Exhibit created.", "success")
        return redirect(url_for("web.exhibits"))
    return render_template("exhibit_new.html", actor=current_actor())

@bp.route("/exhibits/link-artefact", methods=["GET","POST"])
@role_required("admin","curator")
def exhibit_link_artefact():
    with get_session() as db:
        exhibits = repo.list_exhibits(db)
        artefacts = repo.list_artefacts(db)
        if request.method == "POST":
            exhibit_id = int(request.form.get("exhibit_id"))
            artefact_id = int(request.form.get("artefact_id"))
            repo.link_artefact_to_exhibit(db, exhibit_id=exhibit_id, artefact_id=artefact_id)
            flash("Linked artefact to exhibit.", "success")
            return redirect(url_for("web.exhibits"))
    return render_template("exhibit_link_artefact.html", actor=current_actor(), exhibits=exhibits, artefacts=artefacts)

# -------------------- Visitors / Visits / Tickets / Feedback --------------------
@bp.get("/visitors")
@login_required()
def visitors():
    # simple list based on visits/top visitors
    with get_session() as db:
        top = repo.top_visitors(db, limit=25)
    return render_template("visitors.html", actor=current_actor(), top_visitors=top)

@bp.route("/visitors/new", methods=["GET","POST"])
@role_required("admin","front_desk","curator")
def visitor_new():
    if request.method == "POST":
        full_name = request.form.get("full_name","").strip()
        email = request.form.get("email","").strip()
        age_band = request.form.get("age_band","").strip() or None
        region = request.form.get("region","").strip() or None
        membership_type = request.form.get("membership_type","").strip() or None
        if not full_name or not email:
            flash("Full name and email are required", "error")
            return render_template("visitor_new.html", actor=current_actor())
        with get_session() as db:
            try:
                repo.create_visitor(db, full_name=full_name, email=email, age_band=age_band, region=region, membership_type=membership_type)
            except Exception as e:
                flash(f"Could not create visitor: {e}", "error")
                return render_template("visitor_new.html", actor=current_actor())
        flash("Visitor created.", "success")
        return redirect(url_for("web.visitors"))
    return render_template("visitor_new.html", actor=current_actor())

@bp.route("/visits/record", methods=["GET","POST"])
@role_required("admin","front_desk")
def visit_record():
    with get_session() as db:
        exhibits = repo.list_exhibits(db)
        # For picking visitor, we can accept visitor_id directly (simple) or email
        if request.method == "POST":
            visitor_id = int(request.form.get("visitor_id"))
            exhibit_id = int(request.form.get("exhibit_id"))
            visit_date = request.form.get("visit_date","").strip()
            try:
                vd = date.fromisoformat(visit_date) if visit_date else date.today()
                repo.record_visit(db, visitor_id=visitor_id, exhibit_id=exhibit_id, visit_date=vd)
                flash("Visit recorded.", "success")
                return redirect(url_for("web.dashboard"))
            except Exception as e:
                flash(f"Could not record visit: {e}", "error")
    return render_template("visit_record.html", actor=current_actor(), exhibits=exhibits)

@bp.route("/tickets/record", methods=["GET","POST"])
@role_required("admin","front_desk")
def ticket_record():
    with get_session() as db:
        if request.method == "POST":
            visitor_id = int(request.form.get("visitor_id"))
            ticket_type = request.form.get("ticket_type","").strip() or "standard"
            price = request.form.get("price","").strip()
            purchase_date = request.form.get("purchase_date","").strip()
            try:
                pr = float(price)
                pd = date.fromisoformat(purchase_date) if purchase_date else date.today()
                repo.record_ticket_purchase(db, visitor_id=visitor_id, ticket_type=ticket_type, price=pr, purchase_date=pd)
                flash("Ticket purchase recorded.", "success")
                return redirect(url_for("web.dashboard"))
            except Exception as e:
                flash(f"Could not record ticket: {e}", "error")
    return render_template("ticket_record.html", actor=current_actor())

@bp.route("/feedback/record", methods=["GET","POST"])
@role_required("admin","front_desk","curator")
def feedback_record():
    with get_session() as db:
        exhibits = repo.list_exhibits(db)
        if request.method == "POST":
            visitor_id = int(request.form.get("visitor_id"))
            exhibit_id = int(request.form.get("exhibit_id"))
            rating = int(request.form.get("rating"))
            comments = request.form.get("comments","").strip() or None
            try:
                repo.record_feedback(db, visitor_id=visitor_id, exhibit_id=exhibit_id, rating=rating, comments=comments)
                flash("Feedback recorded.", "success")
                return redirect(url_for("web.dashboard"))
            except Exception as e:
                flash(f"Could not record feedback: {e}", "error")
    return render_template("feedback_record.html", actor=current_actor(), exhibits=exhibits)

# -------------------- Conservation --------------------
@bp.route("/conservation/new", methods=["GET","POST"])
@role_required("admin","curator")
def conservation_new():
    with get_session() as db:
        artefacts = repo.list_artefacts(db)
        if request.method == "POST":
            artefact_id = int(request.form.get("artefact_id"))
            condition = request.form.get("condition","").strip()
            treatment = request.form.get("treatment","").strip() or None
            due_date = request.form.get("due_date","").strip()
            notes = request.form.get("notes","").strip() or None
            conservator = request.form.get("conservator","").strip() or None
            try:
                dd = date.fromisoformat(due_date) if due_date else None
                repo.add_conservation_record(db, artefact_id=artefact_id, condition=condition, treatment=treatment, due_date=dd, notes=notes, conservator=conservator)
                flash("Conservation record added.", "success")
                return redirect(url_for("web.dashboard"))
            except Exception as e:
                flash(f"Could not add conservation record: {e}", "error")
    return render_template("conservation_new.html", actor=current_actor(), artefacts=artefacts)
