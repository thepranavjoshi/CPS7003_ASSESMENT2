from __future__ import annotations

import os
from flask import Flask

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

    # Blueprints
    from web.routes import bp
    app.register_blueprint(bp)

    return app
