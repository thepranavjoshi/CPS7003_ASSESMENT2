# HeritagePlus Museum Group – Database Driven Application (SQLite + SQLAlchemy DAL)

This project uses **SQLite** (as required) and implements a **SQLAlchemy-based Data Access Layer (DAL)** to manage communication between the application and the database.

You can run it either as:
- a **CLI** app (original style), or
- a **Flask web UI** (presentation tier) on top of the same business + DAL layers.

## Quickstart
```bash
pip install -r requirements.txt
python main.py
```

## Run the Flask web UI
```bash
pip install -r requirements.txt
python run_flask.py
```

Then open: `http://127.0.0.1:5000`

Default login (seeded on first run):
- username: `admin`
- password: `admin123`

## Key Features
- **Multi-tier architecture**:
  - `presentation/` (CLI) and `web/` (Flask UI)
  - `business/` (validation + forecasting)
  - `dal/` (SQLAlchemy ORM models + repositories)
- **Core entities**: artefacts, exhibits, visitors, visits, ticket purchases, feedback, conservation records
- **Integrity**: foreign keys, CHECK constraints, and triggers:
  - prevents future visit dates
  - auto-updates `artefacts.last_conservation_date`
- **Security**: authentication + role-based access control (admin/curator/front_desk)
- **Optimisation**: indexes on frequent query paths, WAL mode enabled
- **Analytics**: top exhibits/visitors, average ratings, conservation due soon, monthly visit trend
- **Predictive insight**: seasonal-naive forecasting (no pandas required)
- **External integration**: CSV artefact import (prototype)

## CSV Import (prototype external integration)
```python
from integrations.csv_import import import_artefacts_csv
import_artefacts_csv("artefacts.csv")
```

## Tests
```bash
pytest
```

## Notes for marking / report evidence
- The Flask layer makes the presentation tier explicit, supporting the multi-tier architecture discussion.
- Use the analytics pages (Dashboard) + `EXPLAIN` examples (if you add them in the report) to evidence optimisation.
