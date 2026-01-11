from __future__ import annotations

from datetime import date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from dal.models import Base, Exhibit, Visitor

from dal import repositories as repo

def _setup():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON;"))
    Base.metadata.create_all(engine)

    # triggers (same as database/db_init.py)
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TRIGGER IF NOT EXISTS trg_no_future_visits
        BEFORE INSERT ON visits
        FOR EACH ROW
        WHEN date(NEW.visit_date) > date('now')
        BEGIN
            SELECT RAISE(ABORT, 'visit_date cannot be in the future');
        END;
        """))
    Session = sessionmaker(bind=engine, future=True)
    return Session()

def test_future_visit_rejected():
    s = _setup()
    ex = repo.create_exhibit(s, "Test", None, None)
    v = repo.create_visitor(s, "Alice", "alice@example.com")
    s.commit()

    future = date.today() + timedelta(days=2)
    try:
        repo.record_visit(s, v.visitor_id, ex.exhibit_id, future)
        s.commit()
        assert False, "Expected trigger to block future visit"
    except Exception as e:
        s.rollback()
        assert "future" in str(e).lower()

def test_advanced_query_visit_counts():
    s = _setup()
    ex1 = repo.create_exhibit(s, "Ex1", None, None)
    ex2 = repo.create_exhibit(s, "Ex2", None, None)
    v = repo.create_visitor(s, "Bob", "bob@example.com")
    s.commit()

    today = date.today()
    repo.record_visit(s, v.visitor_id, ex1.exhibit_id, today)
    repo.record_visit(s, v.visitor_id, ex1.exhibit_id, today)
    repo.record_visit(s, v.visitor_id, ex2.exhibit_id, today)
    s.commit()

    rows = repo.visit_counts_by_exhibit(s)
    assert rows[0].visit_count >= rows[1].visit_count
