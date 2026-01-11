from __future__ import annotations

import os

from utils.logging_config import configure_logging
from database.db_init import create_database
from web import create_app

def main() -> None:
    configure_logging()
    create_database()

    app = create_app()

    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"

    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()
