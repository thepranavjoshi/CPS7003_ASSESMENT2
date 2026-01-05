import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "museum.db")


def create_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artefacts (
        artefact_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        material TEXT,
        acquisition_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exhibits (
        exhibit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        start_date TEXT,
        end_date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visitors (
        visitor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visits (
        visit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        visitor_id INTEGER,
        exhibit_id INTEGER,
        visit_date TEXT,
        FOREIGN KEY(visitor_id) REFERENCES visitors(visitor_id),
        FOREIGN KEY(exhibit_id) REFERENCES exhibits(exhibit_id)
    )
    """)

    conn.commit()
    conn.close()
    print("Database and tables created successfully.")


if __name__ == "__main__":
    create_database()

