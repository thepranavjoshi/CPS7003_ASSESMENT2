from __future__ import annotations

from sqlalchemy import text

from dal.db import engine, run_ddl
from dal.models import Base
from security.passwords import hash_password
from config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD

def _column_exists(conn, table: str, column: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table});")).fetchall()
    return any(r[1] == column for r in rows)

def _ensure_column(conn, table: str, column: str, ddl_type: str) -> None:
    if not _column_exists(conn, table, column):
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type};"))

def create_database() -> None:
    # Create missing tables (idempotent)
    Base.metadata.create_all(bind=engine)

    # Lightweight "migration" for existing DBs created before new columns existed.
    # SQLite doesn't support many ALTER operations, but ADD COLUMN is safe.
    with engine.begin() as conn:
        _ensure_column(conn, "artefacts", "last_conservation_date", "DATE")
        _ensure_column(conn, "visitors", "age_band", "TEXT")
        _ensure_column(conn, "visitors", "region", "TEXT")
        _ensure_column(conn, "visitors", "membership_type", "TEXT")

    # Triggers: enforce no future visit dates; update last_conservation_date
    run_ddl("""
    CREATE TRIGGER IF NOT EXISTS trg_no_future_visits
    BEFORE INSERT ON visits
    FOR EACH ROW
    WHEN date(NEW.visit_date) > date('now')
    BEGIN
        SELECT RAISE(ABORT, 'visit_date cannot be in the future');
    END;
    """)

    run_ddl("""
    CREATE TRIGGER IF NOT EXISTS trg_update_last_conservation
    AFTER INSERT ON conservation_records
    FOR EACH ROW
    BEGIN
        UPDATE artefacts
        SET last_conservation_date = date(NEW.recorded_at)
        WHERE artefact_id = NEW.artefact_id;
    END;
    """)

    # Seed default admin (idempotent)
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT 1 FROM users WHERE username = :u LIMIT 1"),
            {"u": DEFAULT_ADMIN_USERNAME},
        ).fetchone()

        if not existing:
            conn.execute(
                text("""
                INSERT INTO users (username, password_hash, role, created_at)
                VALUES (:u, :ph, 'admin', datetime('now'))
                """),
                {"u": DEFAULT_ADMIN_USERNAME, "ph": hash_password(DEFAULT_ADMIN_PASSWORD)},
            )

if __name__ == "__main__":
    create_database()
    print("Database initialised successfully.")
