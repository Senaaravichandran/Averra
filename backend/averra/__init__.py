"""Averra application package.

The root ``app.py`` remains a tiny compatibility entrypoint, while this
factory is the canonical way to create an application for local, test, and
production environments.
"""

from pathlib import Path
import logging

from flask import Flask, jsonify, request

from .config import Settings
from .db import init_db
from .seed import seed_demo_data


def create_app(overrides: dict | None = None) -> Flask:
    settings = Settings.from_env()
    project_root = Path(__file__).resolve().parents[2]
    app = Flask(
        __name__,
        template_folder=str(project_root / "frontend" / "templates"),
        static_folder=str(project_root / "frontend" / "static"),
    )
    app.config.from_mapping(settings.to_flask_config())
    if overrides:
        app.config.update(overrides)

    _configure_logging(app)
    init_db(app.config["DATABASE_PATH"])
    if app.config["SEED_DEMO_DATA"]:
        seed_demo_data(app.config["DATABASE_PATH"])

    from .api import api_bp
    from .web import web_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(api_bp, url_prefix="/api/v1", name="api_v1")

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(self), microphone=()")
        if request.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
            response.headers.setdefault("X-Averra-API-Version", "1")
        return response

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found."}), 404
        return "Not found", 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Unhandled application error")
        if request.path.startswith("/api/"):
            return jsonify({"error": "An unexpected server error occurred."}), 500
        return "An unexpected server error occurred.", 500

    return app


def _configure_logging(app: Flask) -> None:
    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
