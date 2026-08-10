"""Runtime configuration for Averra."""

from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("AVERRA_DATABASE", BASE_DIR / "instance" / "averra.sqlite3"))
SECRET_KEY = os.getenv("AVERRA_SECRET", "averra-development-key")
APP_NAME = "Averra"

