from utils.db_connection import get_connection


def add_artefact(name, description, material, acquisition_date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO artefacts (name, description, material, acquisition_date)
        VALUES (?, ?, ?, ?)
        """,
        (name, description, material, acquisition_date)
    )

    conn.commit()
    conn.close()
    print("Artefact added successfully.")


def get_all_artefacts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT artefact_id, name, material, acquisition_date
        FROM artefacts
        ORDER BY artefact_id ASC
        """
    )

    rows = cursor.fetchall()
    conn.close()
    return rows

