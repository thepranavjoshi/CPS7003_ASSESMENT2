from __future__ import annotations

import csv
from pathlib import Path
from datetime import datetime

from dal.db import get_session
from dal import repositories as repo

def import_artefacts_csv(csv_path: str | Path) -> int:
    """Import artefacts from a CSV file.

    Expected headers: name, description, material, acquisition_date(YYYY-MM-DD)
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(path)

    created = 0
    with path.open("r", encoding="utf-8-sig", newline="") as f, get_session() as session:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            description = (row.get("description") or "").strip() or None
            material = (row.get("material") or "").strip() or None
            acq_raw = (row.get("acquisition_date") or "").strip()
            acq_date = datetime.strptime(acq_raw, "%Y-%m-%d").date() if acq_raw else None
            repo.create_artefact(session, name, description, material, acq_date)
            created += 1
    return created
