"""Environment-driven settings with safe local defaults."""

from dataclasses import dataclass
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_path: Path
    secret_key: str
    environment: str
    auth_required: bool
    seed_demo_data: bool
    log_level: str
    max_content_length: int
    admin_email: str
    admin_password_hash: str

    @classmethod
    def from_env(cls) -> "Settings":
        environment = os.getenv("AVERRA_ENV", "development").lower()
        default_seed = environment in {"development", "test"}
        settings = cls(
            database_path=Path(os.getenv("AVERRA_DATABASE", BASE_DIR / "instance" / "averra.sqlite3")),
            secret_key=os.getenv("AVERRA_SECRET", "change-me-before-production"),
            environment=environment,
            auth_required=_bool(os.getenv("AVERRA_AUTH_REQUIRED"), False),
            seed_demo_data=_bool(os.getenv("AVERRA_SEED_DEMO"), default_seed),
            log_level=os.getenv("AVERRA_LOG_LEVEL", "INFO"),
            max_content_length=int(os.getenv("AVERRA_MAX_CONTENT_LENGTH", str(4 * 1024 * 1024))),
            admin_email=os.getenv("AVERRA_ADMIN_EMAIL", ""),
            admin_password_hash=os.getenv("AVERRA_ADMIN_PASSWORD_HASH", ""),
        )
        if settings.environment == "production" and settings.secret_key == "change-me-before-production":
            raise RuntimeError("AVERRA_SECRET must be set before starting Averra in production.")
        if settings.auth_required and not (settings.admin_email and settings.admin_password_hash):
            raise RuntimeError("AVERRA_ADMIN_EMAIL and AVERRA_ADMIN_PASSWORD_HASH are required when AVERRA_AUTH_REQUIRED=true.")
        return settings

    def to_flask_config(self) -> dict:
        return {
            "SECRET_KEY": self.secret_key,
            "DATABASE_PATH": self.database_path,
            "ENVIRONMENT": self.environment,
            "AUTH_REQUIRED": self.auth_required,
            "SEED_DEMO_DATA": self.seed_demo_data,
            "LOG_LEVEL": self.log_level,
            "MAX_CONTENT_LENGTH": self.max_content_length,
            "ADMIN_EMAIL": self.admin_email,
            "ADMIN_PASSWORD_HASH": self.admin_password_hash,
        }
