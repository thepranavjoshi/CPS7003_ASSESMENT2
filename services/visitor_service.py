from utils.db_connection import get_connection


def add_visitor(full_name, email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO visitors (full_name, email)
        VALUES (?, ?)
        """,
        (full_name, email)
    )

    conn.commit()
    conn.close()
    print("Visitor added successfully.")


def add_visit(visitor_id, exhibit_id, visit_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO visits (visitor_id, exhibit_id, visit_date)
        VALUES (?, ?, ?)
        """,
        (visitor_id, exhibit_id, visit_date)
    )

    conn.commit()
    conn.close()
    print("Visit recorded successfully.")


def get_visit_counts_by_exhibit():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT e.title, COUNT(v.visit_id) AS visit_count
        FROM visits v
        JOIN exhibits e ON v.exhibit_id = e.exhibit_id
        GROUP BY e.title
        ORDER BY visit_count DESC
        """
    )

    rows = cursor.fetchall()
    conn.close()
    return rows

