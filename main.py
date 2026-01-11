from __future__ import annotations

from utils.logging_config import configure_logging
from database.db_init import create_database
from presentation.cli import run

def main() -> None:
    configure_logging()
    create_database()
    run()

if __name__ == "__main__":
    main()
