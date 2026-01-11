from __future__ import annotations

from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL

# Engine configured for SQLite foreign keys and reasonable defaults
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,   # ✅ IMPORTANT
    future=True
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    # Enable FK enforcement in SQLite
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.close()

@contextmanager
def get_session() -> Session:
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def run_ddl(sql: str) -> None:
    # Helper for triggers / indexes (SQLite DDL)
    with engine.begin() as conn:
        conn.execute(text(sql))
