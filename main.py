from services.artefact_service import add_artefact, get_all_artefacts
from services.visitor_service import (
    add_visitor,
    add_visit,
    get_visit_counts_by_exhibit
)
from utils.db_connection import get_connection


def database_is_empty():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM artefacts")
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0


def seed_data():
    print("Seeding sample data...")

    add_artefact(
        "Ancient Coin",
        "Gold coin from Roman era",
        "Gold",
        "2019-03-15"
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO exhibits (title, start_date, end_date) VALUES (?, ?, ?)",
        ("Roman Empire", "2024-01-01", "2024-12-31")
    )
    conn.commit()
    conn.close()

    add_visitor("Alice Brown", "alice.brown@example.com")
    add_visit(1, 1, "2025-01-10")
    add_visit(1, 1, "2025-01-11")


def main():
    if database_is_empty():
        seed_data()

    print("\n--- Artefacts ---")
    artefacts = get_all_artefacts()
    for artefact in artefacts:
        print(dict(artefact))

    print("\n--- Visit Counts by Exhibit ---")
    results = get_visit_counts_by_exhibit()
    for row in results:
        print(dict(row))


if __name__ == "__main__":
    main()

