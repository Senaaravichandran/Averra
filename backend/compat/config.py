"""Backward-compatible configuration constants."""

from backend.averra.config import BASE_DIR, Settings


_settings = Settings.from_env()
DATABASE_PATH = _settings.database_path
SECRET_KEY = _settings.secret_key
APP_NAME = "Averra"
