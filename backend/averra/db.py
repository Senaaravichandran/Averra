"""Database lifecycle and versioned migration runner."""

from pathlib import Path
import sqlite3


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "database" / "migrations"


def get_db(database_path: str | Path) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def init_db(database_path: str | Path) -> None:
    db = get_db(database_path)
    db.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    applied = {row[0] for row in db.execute("SELECT version FROM schema_migrations")}
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for migration in migration_files:
        version = int(migration.stem.split("_", 1)[0])
        if version in applied:
            continue
        db.executescript(migration.read_text(encoding="utf-8"))
        db.execute("INSERT INTO schema_migrations (version) VALUES (?)", (version,))
    db.commit()
    db.close()


def rows_to_dict(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]
