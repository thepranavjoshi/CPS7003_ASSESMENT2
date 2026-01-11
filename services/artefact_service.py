from __future__ import annotations

from datetime import datetime
from dal.db import get_session
from dal import repositories as repo

def add_artefact(name: str, description: str | None, material: str | None, acquisition_date: str | None):
    acq_date = datetime.strptime(acquisition_date, "%Y-%m-%d").date() if acquisition_date else None
    with get_session() as session:
        return repo.create_artefact(session, name, description, material, acq_date)

def get_all_artefacts():
    with get_session() as session:
        return repo.list_artefacts(session)
